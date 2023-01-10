import asyncio
import io
import os
import time
import PIL.Image
from collections import Counter
from fastapi.testclient import TestClient

os.environ['LAP_PATH_DATA'] = os.path.dirname(os.path.realpath(__file__))
os.environ['LAP_DB_DIALECT'] = 'sqlite'
os.environ['LAP_DB_DRIVER'] = 'aiosqlite'
os.environ['LAP_DB_DBNAME'] = './test_app.db'
os.environ['LAP_CLEAR'] = 'true'
os.environ['LAP_INFERENCE_ENABLED'] = 'false'

from app.run import app, file_manager
from tests.utils import insert_db_data, insert_image_files


# Set a valid image url to test some test cases
VALID_FILE = {'name': 'valid_image.csv', 'content': b'url\nPut valid image url here'}


def test_ping():
    with TestClient(app) as client:
        response = client.get('/ping')
        assert response.status_code == 204
        assert 'content-length' not in map(str.lower, response.headers.keys())
        assert 'content-type' not in map(str.lower, response.headers.keys())


def test_insert_file_non_csv_format():
    with TestClient(app) as client:
        response = client.post('/files',
                               files={'file': ('invalid_file.txt', b'this is text file', 'text/plain')})
        assert response.status_code == 400


def test_insert_file_invalid_csv_fields():
    with TestClient(app) as client:
        _test_file(client, 'invalid_csv_fields.csv', b'this,is,invalid,csv,field', {'cnt_url': -1})


def test_insert_file_non_url_file():
    with TestClient(app) as client:
        _test_file(client, 'non_url.csv', b'url\nthis is not a url', {'cnt_url': 0})


def test_insert_file_non_image_url():
    with TestClient(app) as client:
        _test_file(client, 'non_image_url.csv', b'url\nhttps://google.com/',
                   {'cnt_url': 1, 'cnt_image': 0})


def test_insert_file_existent():
    filename = 'valid_image_url.csv'
    content_with_valid_image_url = b'anything'
    with TestClient(app) as client:
        response = client.post('/files',
                               files={'file': (filename, content_with_valid_image_url, 'text/csv')})
        assert response.status_code == 200

        response = client.post('/files',
                               files={'file': (filename, content_with_valid_image_url, 'text/csv')})
        assert response.status_code == 400


def test_insert_file():
    with TestClient(app) as client:
        _test_file(client, VALID_FILE['name'], VALID_FILE['content'], {'cnt_url': 1, 'cnt_image': 1})


# In production, image files are automatically saved in a data directory and image data is automatically stored in a database after inserting a file.
# So you need to prepare files, images and regions data to be stored in the database in advance in db_data.yml
# And you need to download image files from image urls in db_data.yml and save them in "../pre_downloaded_images" directory
# If the hash of image file is "6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32",
# the path of image file should be "../pre_downloaded_images/6d/6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32"
# Test cases for image runs after inserting temporary data into database and copying image files to image directory
def test_insert_datasets():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0


def test_get_images():
    with TestClient(app) as client:
        insert_image_files()
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        response = client.get('/images', params={'file_id': testset['file'].id})
        assert response.status_code == 200
        images = response.json()
        assert len(images) == len(testset['images'])


def test_get_image():
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


def test_get_bboxes_from_file():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        response = client.get('/bboxes', params={'file_id': testset['file'].id})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == len(testset['bboxes'])


def test_get_bboxes_from_image():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        cnt_of_bboxes_per_image = Counter([o.image_id for o in testset['bboxes']])
        for image in testset['images']:
            response = client.get('/bboxes', params={'image_id': image.id})
            assert response.status_code == 200
            assert len(response.json()) == cnt_of_bboxes_per_image[image.id], \
                f'total count of bboxes of {image} should be matched with prepared data'


def test_update_label_as_unused():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        testset['bboxes'][0].label.unused = True
        response = client.put(f"/labels/{testset['bboxes'][0].label.id}",
                              json=testset['bboxes'][0].label.dict(),
                              headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        result = response.json()
        assert result['unused'] is True

        response = client.get('/bboxes', params={'file_id': testset['file'].id, 'filters': 'unused=true'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1

        response = client.get('/bboxes', params={'file_id': testset['file'].id, 'filters': 'unused=false'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == len(testset['bboxes']) - 1, \
            'bbox which is "unused=True" should be excluded'


def test_update_label_as_reviewed():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        testset['bboxes'][0].label.reviewed = True
        response = client.put(f"/labels/{testset['bboxes'][0].label.id}",
                              json=testset['bboxes'][0].label.dict(),
                              headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        result = response.json()
        assert result['reviewed'] is True

        response = client.get('/bboxes', params={'file_id': testset['file'].id, 'filters': 'reviewed=true'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1

        response = client.get('/bboxes', params={'file_id': testset['file'].id, 'filters': 'reviewed=false'})
        assert response.status_code == 200
        result = response.json()
        assert len(result) == len(testset['bboxes']) - 1, \
            'bbox which is "reviewed=True" should be excluded'


def test_export_file_to_yolo_data_format():
    with TestClient(app) as client:
        insert_image_files()
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 1
        testset = testsets[1]

        response = client.get(f"/export/{testset['file'].id}")
        assert response.status_code == 200

        count_of_filtered_images = len({o.image_id for o in testset['bboxes']})
        result = response.json()['path']

        count_of_saved_images = 0
        for dirpath, dirnames, filenames in os.walk(result):
            for filename in filenames:
                if filename.endswith('.jpg') and os.path.isfile(os.path.join(dirpath, filename)):
                    count_of_saved_images += 1
        assert count_of_saved_images == count_of_filtered_images, \
            'exported data should contain as many .jpg files as number of images'


def test_export_file_to_yolo_data_format_with_filters():
    with TestClient(app) as client:
        insert_image_files()
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 1
        testset = testsets[1]

        response = client.get(f"/export/{testset['file'].id}", params={'filters': ['region=top',
                                                                                   'unused=false',
                                                                                   'reviewed=true']})
        assert response.status_code == 200

        count_of_filtered_images = len({o.image_id for o in testset['bboxes']
                                        if o.label.region == 'top' and not o.label.unused and o.label.reviewed})

        result = response.json()['path']

        count_of_saved_images = 0
        for dirpath, dirnames, filenames in os.walk(result):
            for filename in filenames:
                if filename.endswith('.jpg') and os.path.isfile(os.path.join(dirpath, filename)):
                    count_of_saved_images += 1
        assert count_of_saved_images == count_of_filtered_images, \
            'exported data should contain as many .jpg as number of filtered images'


def _insert_file(_client, filename, content):
    response = _client.post('/files', files={'file': (filename, content, 'text/csv')})
    assert response.status_code == 200
    file_obj = response.json()
    assert 'id' in file_obj
    assert os.path.exists(f"{file_manager.file_dir}/{filename}")
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
