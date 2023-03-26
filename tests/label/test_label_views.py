import asyncio
import os

from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_views')
os.environ['LAP_PATH_DATA'] = DATA_DIR
os.environ['LAP_DB_DIALECT'] = 'sqlite'
os.environ['LAP_DB_DRIVER'] = 'aiosqlite'
os.environ['LAP_DB_DBNAME'] = './test_label_views.db'
os.environ['LAP_CLEAR'] = 'true'
os.environ['LAP_INFERENCE_ENABLED'] = 'false'

from app.run import app

from ..utils import insert_db_data, remove_data_dir


def test_update_unused():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        answer = not testset['bboxes'][0].label.unused
        testset['bboxes'][0].label.unused = answer
        response = client.put(f"/labels/{testset['bboxes'][0].label.id}",
                              json=testset['bboxes'][0].label.dict(),
                              headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        result = response.json()
        assert result['unused'] == answer
    remove_data_dir()


def test_update_reviewed():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        answer = not testset['bboxes'][0].label.reviewed
        testset['bboxes'][0].label.reviewed = answer
        response = client.put(f"/labels/{testset['bboxes'][0].label.id}",
                              json=testset['bboxes'][0].label.dict(),
                              headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        result = response.json()
        assert result['reviewed'] == answer
    remove_data_dir()


def test_get_statistics():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        answer = len(testset['bboxes'])

        response = client.get(f"/labels/statistics",
                              params={'file_id': testset['file'].id})
        assert response.status_code == 200
        result = response.json()
        assert 'region' in result
        assert sum(result['region'].values()) == answer, \
            'All bboxes should have `region` label.'
    remove_data_dir()
