import os
import unittest

from inference import InferenceClient
from inference.inference_pb2 import Request, Reply
from app.image.schemas import ImageRead

# You need to run "grpc_tools.protoc" to parse "../../protos/*.proto" files


class TestInferenceClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.config_disabled = {'enabled': False}
        self.config_enabled = {'enabled': True,
                               'host': '192.168.0.4',
                               'port': 5050,
                               'batch_size': 1}
        # You need to have an image file in "../pre_downloaded_images" directory
        # If the hash of image file is "6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32",
        # the path of image file should be "../pre_downloaded_images/6d/6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32"
        self.db_image = {'id': 1, 'file_id': 1,
                         'hash': '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32',
                         'width': 600, 'height': 600,
                         'url': 'test url'}
        self.db_image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../pre_downloaded_images',
                                          self.db_image['hash'][:2], f"{self.db_image['hash']}.jpg")

    async def test_ping_client_with_no_config(self):
        client = InferenceClient()
        self.assertFalse(client.enabled())
        r = await client.ping()
        self.assertFalse(r)

    async def test_ping_disabled_client(self):
        client = InferenceClient(config=self.config_disabled)
        self.assertFalse(client.enabled())
        r = await client.ping()
        self.assertFalse(r)

    async def test_ping_enabled_client(self):
        client = InferenceClient(config=self.config_enabled)

        r = await client.ping()
        self.assertTrue(r)

    async def test_make_request(self):
        client = InferenceClient()
        request = Request()
        image = ImageRead(**self.db_image)
        await client._make_request(request, image, self.db_image_path)
        self.assertEqual(1, len(request.images))

    def test_parse_reply(self):
        client = InferenceClient()
        reply = Reply()
        bbox = reply.regions.add()
        bbox.image.id = 1
        bbox.bbox.rx1, bbox.bbox.ry1, bbox.bbox.rx2, bbox.bbox.ry2 = 0.1, 0.1, 0.2, 0.2
        r = client._parse_reply(reply)
        self.assertEqual(1, len(r))

    async def test_infer(self):
        client = InferenceClient(self.config_enabled)
        image = ImageRead(**self.db_image)
        r = await client.infer([(image, self.db_image_path)])
        self.assertEqual(1, len(r))
        data = r[0]
        self.assertEqual(tuple, type(data))
        self.assertEqual(image.id, data[0], msg='inferred data should have the requested image id')
