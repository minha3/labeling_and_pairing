import asyncio
import os
import time

from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_views')
os.environ['LAP_PATH_DATA'] = DATA_DIR
os.environ['LAP_DB_DIALECT'] = 'sqlite'
os.environ['LAP_DB_DRIVER'] = 'aiosqlite'
os.environ['LAP_DB_DBNAME'] = './test_file_views.db'
os.environ['LAP_CLEAR'] = 'true'
os.environ['LAP_INFERENCE_ENABLED'] = 'false'

from app.file.utils import get_file_dirpath
from app.run import app

from ..utils import insert_db_data, remove_data_dir


# Set a valid image url to test some test cases
VALID_CSV_FILE_CONTENTS = b'url\nPut valid image url here'


def test_insert_non_csv_format():
    with TestClient(app) as client:
        response = client.post('/files',
                               files={'file': ('invalid_file.txt', b'this is text file', 'text/plain')})
        assert response.status_code == 400
    remove_data_dir()


def test_insert_invalid_csv_fields():
    with TestClient(app) as client:
        _test_file(client, 'invalid_csv_fields.csv', b'this,is,invalid,csv,field', {'cnt_url': -1})
    remove_data_dir()


def test_insert_non_url_file():
    with TestClient(app) as client:
        _test_file(client, 'non_url.csv', b'url\nthis is not a url', {'cnt_url': 0})
    remove_data_dir()


def test_insert_non_image_url():
    with TestClient(app) as client:
        _test_file(client, 'non_image_url.csv', b'url\nhttps://google.com/', {'cnt_url': 1, 'cnt_image': 0})
    remove_data_dir()


def test_insert_duplicate_filename():
    with TestClient(app) as client:
        datasets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        response = client.post('/files',
                               files={'file': (datasets[0]['file'].name, b'anything', 'text/csv')})
        assert response.status_code == 400
    remove_data_dir()


def test_insert():
    with TestClient(app) as client:
        _test_file(client, 'valid_image_url.csv', VALID_CSV_FILE_CONTENTS, {'cnt_url': 1, 'cnt_image': 1})
    remove_data_dir()


def test_get_all():
    with TestClient(app) as client:
        datasets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        response = client.get('/files')
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
    remove_data_dir()


def test_get_exists():
    with TestClient(app) as client:
        datasets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        response = client.get(f"/files/{datasets[0]['file'].id}")
        assert response.status_code == 200
    remove_data_dir()


def test_get_non_exists():
    with TestClient(app) as client:
        response = client.get(f"/files/{int(1e9)}")
        assert response.status_code == 404
    remove_data_dir()


def test_delete():
    with TestClient(app) as client:
        datasets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        response = client.delete(f"/files/{datasets[0]['file'].id}")
        assert response.status_code == 204
    remove_data_dir()


def _insert_file(_client, filename, content):
    response = _client.post('/files', files={'file': (filename, content, 'text/csv')})
    assert response.status_code == 200
    file_obj = response.json()
    assert 'id' in file_obj
    assert os.path.exists(f"{get_file_dirpath()}/{filename}")
    return file_obj


def _get_file(_client, file_id, required):
    response = _client.get("/files")
    assert response.status_code == 200
    files = response.json()
    assert type(files) == list
    assert len(files) > 0
    assert file_id in [o['id'] for o in files]

    # wait for required columns to fill in after background process of downloading and inferring images is complete
    end_time = time.time() + 10
    while time.time() < end_time:
        response = _client.get(f"/files/{file_id}")
        assert response.status_code == 200
        file_obj = response.json()
        if all(file_obj[key] is not None for key in required):
            break
        time.sleep(0.1)
    response = _client.get(f"/files/{file_id}")
    assert response.status_code == 200
    return response.json()


def _remove_file(_client, file_id):
    response = _client.delete(f"/files/{file_id}")
    assert response.status_code == 204


def _test_file(_client, filename, content, testset):
    file_obj = _insert_file(_client, filename, content)
    file_obj = _get_file(_client, file_obj['id'], testset.keys())
    for key, value in testset.items():
        assert file_obj[key] == value, f'Test failed for key {key}'
    _remove_file(_client, file_obj['id'])
