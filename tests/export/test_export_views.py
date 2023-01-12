import asyncio
import os

from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_views')
os.environ['LAP_PATH_DATA'] = DATA_DIR
os.environ['LAP_DB_DIALECT'] = 'sqlite'
os.environ['LAP_DB_DRIVER'] = 'aiosqlite'
os.environ['LAP_DB_DBNAME'] = './test_export_views.db'
os.environ['LAP_CLEAR'] = 'true'
os.environ['LAP_INFERENCE_ENABLED'] = 'false'

from app.run import app

from ..utils import insert_db_data, insert_image_files, remove_data_dir


def test_export_file_to_yolo_data_format():
    with TestClient(app) as client:
        insert_image_files()
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 1
        testset = testsets[1]

        response = client.post(f"/exports", params={'file_id': testset['file'].id})
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
    remove_data_dir()


def test_export_file_to_yolo_data_format_with_filters():
    with TestClient(app) as client:
        insert_image_files()
        testsets = asyncio.get_event_loop().run_until_complete(insert_db_data())
        assert len(testsets) > 1
        testset = testsets[1]

        response = client.post(f"/exports", params={'file_id': testset['file'].id,
                                                    'filters': ['region=top',
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
    remove_data_dir()
