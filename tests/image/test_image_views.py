import asyncio
import os
import io

import PIL.Image
from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_views')
os.environ['LAP_PATH_DATA'] = DATA_DIR
os.environ['LAP_DB_DIALECT'] = 'sqlite'
os.environ['LAP_DB_DRIVER'] = 'aiosqlite'
os.environ['LAP_DB_DBNAME'] = './test_image_views.db'
os.environ['LAP_CLEAR'] = 'true'
os.environ['LAP_INFERENCE_ENABLED'] = 'false'

from app.run import app

from ..utils import insert_db_data, insert_image_files, remove_data_dir


def test_get_all():
    with TestClient(app) as client:
        insert_image_files()
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        response = client.get('/images', params={'file_id': testset['file'].id})
        assert response.status_code == 200
        images = response.json()
        assert len(images) == len(testset['images'])
    remove_data_dir()


def test_get_exists():
    with TestClient(app) as client:
        insert_image_files()
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        response = client.get(f"/images/{testset['images'][0].id}")
        assert response.status_code == 200
        assert int(response.headers.get('Content-Length')) > 0
        assert type(response.content) == bytes
        assert len(response.content) > 0
        pil_image = PIL.Image.open(io.BytesIO(response.content))
        assert pil_image.width == testset['images'][0].width
        assert pil_image.height == testset['images'][0].height
    remove_data_dir()


def test_get_non_exists():
    with TestClient(app) as client:
        response = client.get(f"/images/{int(1e9)}")
        assert response.status_code == 404
    remove_data_dir()
