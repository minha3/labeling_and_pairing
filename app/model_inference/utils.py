import aiofiles
import grpc
import json

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from google.protobuf import empty_pb2

from common.exceptions import OperationError
from app.image.schemas import ImageRead
from app.bbox.schemas import BBoxBase
from app.label.schemas import LabelBase
from app.model_inference import inference_pb2
from app.model_inference.inference_pb2_grpc import InferenceAPIsServiceStub


class InferenceClient(ABC):
    def __init__(self, config: dict):
        missing_configs = set(self.required_configs) - set(config.keys())
        if missing_configs:
            raise KeyError(f'Missing required configuration parameters: {missing_configs}')
        self._config = config

    @property
    def required_configs(self):
        return []

    @abstractmethod
    async def infer(self, images: List[Tuple[ImageRead, str]]) -> \
            List[Tuple[int, BBoxBase, Optional[LabelBase]]]:
        pass


class TorchServeClient(InferenceClient):
    @property
    def required_configs(self):
        return ['host', 'grpc_inference_port', 'grpc_management_port', 'project']

    @property
    def inference_addr(self):
        return f"{self._config['host']}:{self._config['grpc_inference_port']}"

    @property
    def management_addr(self):
        return f"{self._config['host']}:{self._config['grpc_management_port']}"

    async def infer(self, images: List[Tuple[ImageRead, str]]) -> \
            List[Tuple[int, BBoxBase, Optional[LabelBase]]]:
        async with grpc.aio.insecure_channel(
            self.inference_addr,
            options=[('grpc.max_send_message_length', 100 * 1024 * 1024),
                     ('grpc.max_receive_message_length', 100 * 1024 * 1024)]
        ) as channel:
            client = InferenceAPIsServiceStub(channel)

            if not await self._ping(client):
                raise OperationError(f"Inference server {self.inference_addr} is not healthy")

            result = []
            for image, path in images:
                _, prediction = await self._send_request(client, self._config['project'], image, path)
                result.extend(self._parse_response(image, prediction))
            return result

    @staticmethod
    async def _ping(client) -> bool:
        response = await client.Ping(empty_pb2.Empty())
        health = json.loads(response.health)
        return health['status'].lower() == 'healthy'

    @staticmethod
    async def _send_request(client, model, image: ImageRead, path: str):
        async with aiofiles.open(path, 'rb') as f:
            data = await f.read()
        request = inference_pb2.PredictionsRequest(model_name=model,
                                                   input={'data': data})
        response = await client.Predictions(request)
        prediction = json.loads(response.prediction.decode('utf-8'))
        return image, prediction[0]

    @staticmethod
    def _parse_response(image: ImageRead, response: List[dict]) -> List[Tuple[int, BBoxBase, Optional[LabelBase]]]:
        result = []
        for region in response:
            base_bbox = BBoxBase(rx1=region['box']['x1'] / image.width,
                                 ry1=region['box']['y1'] / image.height,
                                 rx2=region['box']['x2'] / image.width,
                                 ry2=region['box']['y2'] / image.height)

            result.append((image.id, base_bbox, LabelBase(region=region['name'])))
        return result
