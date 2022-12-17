import asyncio
import logging
import grpc
import aiofiles

from typing import List, Tuple
from inference.inference_pb2_grpc import InferenceStub
from inference.inference_pb2 import Request, Reply
from label import translate
from common import schemas


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

    async def infer(self, images: List[Tuple[schemas.Image, str]]) -> List[schemas.RegionCreate]:
        """
        :param images: list of tuple(schemas.Image, path of image file)
        :return:
        """
        if not images:
            return []

        result = []
        try:
            async with grpc.aio.insecure_channel(self._addr) as channel:
                client = InferenceStub(channel)
                request = Request()
                for i in range(len(images) // self._batch_size + 1):
                    coros = []
                    for image, path in images[i*self._batch_size:(i + 1) * self._batch_size]:
                        coros.append(self._make_request(request, image, path))
                    if coros:
                        await asyncio.gather(*coros)
                        result.extend(self._parse_reply(await client.compute(request)))
        except Exception:
            file_ids = {o[0].file_id for o in images}
            file_ids_str = ','.join(file_ids[:3]) + ',...' if len(file_ids) > 3 else ''
            logging.exception(f'Unexpected exception occurred when request images of files'
                              f' [{file_ids_str}] to inference server.'
                              f' Total count of processed images is {len(result)}/{len(images)}.')

        return result

    @staticmethod
    async def _make_request(request: Request, image: schemas.Image, path: str):
        request_image = request.images.add()
        request_image.id = image.id
        request_image.width = image.width
        request_image.height = image.height
        async with aiofiles.open(path, 'rb') as f:
            request_image.data = await f.read()

    @staticmethod
    def _parse_reply(reply: Reply) -> List[schemas.RegionCreate]:
        result = []
        for region in reply.regions:
            base_region = schemas.RegionCreate(image_id=region.image.id,
                                               rx1=region.bbox.rx1, ry1=region.bbox.ry1,
                                               rx2=region.bbox.rx2, ry2=region.bbox.ry2, labels={})
            for label in region.labels:
                base_region.labels[translate(label.type)] = translate(label.name, label.type)
            result.append(base_region)
        return result
