import asyncio
import os
from collections import Counter

from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_views')
os.environ['LAP_PATH_DATA'] = DATA_DIR
os.environ['LAP_DB_DIALECT'] = 'sqlite'
os.environ['LAP_DB_DRIVER'] = 'aiosqlite'
os.environ['LAP_DB_DBNAME'] = './test_bbox_views.db'
os.environ['LAP_CLEAR'] = 'true'
os.environ['LAP_INFERENCE_ENABLED'] = 'false'

from app.run import app

from ..utils import insert_db_data, remove_data_dir


def test_get_bboxes_from_file():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        response = client.get('/bboxes', params={'file_id': testset['file'].id})
        assert response.status_code == 200
        result = response.json()
        assert len(result['items']) == len(testset['bboxes'])
        assert result['total'] == len(testset['bboxes'])
    remove_data_dir()


def test_get_bboxes_from_image():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]

        answers = Counter([o.image_id for o in testset['bboxes']])
        for image in testset['images']:
            response = client.get('/bboxes', params={'image_id': image.id})
            assert response.status_code == 200
            result = response.json()
            assert len(result['items']) == answers[image.id], \
                f'total count of bboxes of {image} should be matched with prepared data'
    remove_data_dir()


def test_get_bboxes_from_file_with_label_filter():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        test_label_type = 'style'
        test_label_name = 'street'

        answer = sum(getattr(o.label, test_label_type) == test_label_name
                     for o in testset['bboxes'])

        response = client.get('/bboxes', params={'file_id': testset['file'].id,
                                                 'filters': f'{test_label_type}={test_label_name}'})
        assert response.status_code == 200
        result = response.json()
        assert len(result['items']) == answer, \
            f'total count of bboxes that {test_label_type} is {test_label_name} ' \
            f'should be matched with prepared data'
    remove_data_dir()


def test_get_bboxes_from_file_with_label_sort_asc():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        sort_label_type = 'style'

        answer = sorted(testset['bboxes'],
                        key=lambda o: getattr(o.label, sort_label_type))

        response = client.get('/bboxes', params={'file_id': testset['file'].id,
                                                 'sort_by': f'{sort_label_type}'})
        assert response.status_code == 200
        result = response.json()
        assert result['items'] == answer, \
            f'boxes should be sorted in the order of {sort_label_type} labels'
    remove_data_dir()


def test_get_bboxes_from_file_with_label_sort_desc():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        sort_label_type = 'style'

        answer = sorted(testset['bboxes'],
                        key=lambda o: getattr(o.label, sort_label_type),
                        reverse=True)

        response = client.get('/bboxes', params={'file_id': testset['file'].id,
                                                 'sort_by': f'-{sort_label_type}'})
        assert response.status_code == 200
        result = response.json()
        assert result['items'] == answer, \
            f'boxes should be sorted in reverse order of {sort_label_type} labels'
    remove_data_dir()


def test_get_bboxes_from_file_with_label_sort_multiple():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        sort_label_type = 'region,-style'

        answer = sorted(
            testset['bboxes'],
            key=lambda o: (o.label.region, -ord(o.label.style[0]))
        )

        response = client.get('/bboxes', params={'file_id': testset['file'].id,
                                                 'sort_by': f'{sort_label_type}'})
        assert response.status_code == 200
        result = response.json()
        assert result['items'] == answer, \
            f'boxes should be sorted in the order of {sort_label_type}'
    remove_data_dir()


def test_get_bboxes_from_file_with_pagination():
    with TestClient(app) as client:
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 0
        testset = testsets[0]
        page = 1
        items_per_page = 2

        response = client.get('/bboxes', params={'file_id': testset['file'].id,
                                                 'page': page,
                                                 'items_per_page': items_per_page})
        assert response.status_code == 200
        result = response.json()
        assert result['total'] == len(testset['bboxes'])
        assert result['page'] == page
        assert result['items_per_page'] == items_per_page
        assert len(result['items']) == items_per_page
    remove_data_dir()
