import asyncio
import logging
import grpc
import aiofiles
import time

from typing import List, Tuple, Optional
from inference.inference_pb2_grpc import InferenceStub
from inference.inference_pb2 import Request, Reply

from app.image.schemas import ImageRead
from app.bbox.schemas import BBoxBase
from app.label.schemas import LabelBase
from app.label.utils import translate


class InferenceClient:
    def __init__(self, config: dict = None):
        self._enabled = False
        self._addr = None
        self._batch_size = 1
        if config:
            self._enabled = config['enabled']
            if self._enabled:
                self._addr = '{host}:{port}'.format(**config)
                self._batch_size = config['batch_size']

    def enabled(self):
        return self._enabled

    async def ping(self) -> bool:
        if not self._enabled:
            return False
        try:
            async with grpc.aio.insecure_channel(self._addr) as channel:
                client = InferenceStub(channel)
                request = Request()
                await client.compute(request)
                return True
        except grpc.aio.AioRpcError:
            return False
        # This handler is for unknown exceptions. Known exceptions should be handled explicitly
        except:
            logging.exception('Unexpected exception occurred when request health check to inference server.')
            return False

    async def infer(self, images: List[Tuple[ImageRead, str]]) -> \
            List[Tuple[int, BBoxBase, Optional[LabelBase]]]:
        """
        :param images: list of tuple(schemas.Image, path of image file)
        :return: list of tuple(image id, schemas.RegionBase, schemas.LabelBase)
        """
        if not images:
            return []

        result = []
        try:
            async with grpc.aio.insecure_channel(self._addr,
                                                 options=[('grpc.max_send_message_length', 100 * 1024 * 1024),
                                                          ('grpc.max_receive_message_length', 100 * 1024 * 1024)]) \
                    as channel:
                client = InferenceStub(channel)
                total = len(images)
                for i in range(total // self._batch_size + 1):
                    request = Request()
                    coros = []
                    s = i * self._batch_size
                    e = (i + 1) * self._batch_size
                    for image, path in images[s:e]:
                        coros.append(self._make_request(request, image, path))
                    if coros:
                        await asyncio.gather(*coros)
                        try:
                            t = time.time()
                            reply = await client.compute(request)
                            result.extend(self._parse_reply(reply))
                            logging.debug(
                                f'Parsing replies completed. elapsed: {time.time() - t}. image ids: {s} ~ {e} / {total}')
                        except KeyboardInterrupt:
                            logging.info(f'Stopped to parse replies. image ids {s} ~ {e} / {total}')
                            return result
                        except grpc.aio.AioRpcError:
                            logging.exception(f'Failed to parse replies. image ids {s} ~ {e} / {total}')
        except Exception:
            file_ids = list({o[0].file_id for o in images})
            file_ids_str = ','.join(map(str, file_ids[:3])) + (',...' if len(file_ids) > 3 else '')
            logging.exception(f'Unexpected exception occurred when request images of files'
                              f' [{file_ids_str}] to inference server.'
                              f' Total count of processed images is {len(result)}/{total}.')

        return result

    @staticmethod
    async def _make_request(request: Request, image: ImageRead, path: str):
        request_image = request.images.add()
        request_image.id = image.id
        request_image.width = image.width
        request_image.height = image.height
        async with aiofiles.open(path, 'rb') as f:
            request_image.data = await f.read()

    @staticmethod
    def _parse_reply(reply: Reply) -> List[Tuple[int, BBoxBase, Optional[LabelBase]]]:
        result = []
        for region in reply.regions:
            image_id = region.image.id
            base_region = BBoxBase(rx1=region.bbox.rx1, ry1=region.bbox.ry1,
                                   rx2=region.bbox.rx2, ry2=region.bbox.ry2)
            labels = {}
            for label in region.labels:
                label_type, label_name = translate(label.type), translate(label.name, label.type)
                if label_type and label_name:
                    labels[label_type] = label_name
            if labels:
                base_label = LabelBase(**labels)
            else:
                base_label = None
            result.append((image_id, base_region, base_label))
        return result
