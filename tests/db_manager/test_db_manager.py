import os
import unittest
import yaml

from sqlalchemy.exc import IntegrityError

from common import schemas
from common.exceptions import *
from label import load_labels
from db import DBManager


class TestDBManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        my_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(my_dir, 'db_data.yml'), 'r') as f:
            self.db_data = yaml.safe_load(f)
        self.FILE1 = schemas.FileCreate(**self.db_data['file1'])
        self.FILE2 = schemas.FileCreate(**self.db_data['file2'])
        self.IMAGE1 = schemas.ImageCreate(**self.db_data['image1'])
        self.REGION_BASE1 = self.db_data['region1']
        self.REGION_BASE2 = self.db_data['region2']

        load_labels(my_dir)
        self.db_manager = DBManager(db_config={'dialect': 'mysql',
                                               'driver': 'aiomysql',
                                               'user': 'root',
                                               'password': os.environ['LAP_DB_PASSWORD'],
                                               'host': 'localhost',
                                               'dbname': os.environ['LAP_DB_DBNAME']})
        await self.db_manager.create_all(drop=True)

    async def asyncTearDown(self) -> None:
        await self.db_manager.drop_all()
        await self.db_manager.close()

    async def test_01_insert_file(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_file(session, self.FILE1)
            self.assertIsNotNone(r)

    async def test_02_insert_duplicate_filename(self):
        async for session in self.db_manager.get_session():
            await self.db_manager.insert_file(session, self.FILE1)
            with self.assertRaises(IntegrityError, msg='Inserting a file with a duplicate name results in an error'):
                await self.db_manager.insert_file(session, self.FILE1)

    async def test_03_get_existent_file(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_file(session, self.FILE1)
            r = await self.db_manager.get_file(session, r.id)
            self.assertIsNotNone(r)

    async def test_04_get_non_existent_file(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_file(session, 1)

    async def test_05_get_non_existent_file_silently(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_file(session, 1, silent=True)
            self.assertIsNone(r)

    async def test_06_insert_images(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            r = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            self.assertEqual(1, len(r))

    async def test_07_insert_duplicate_imagehash_on_same_file(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            r = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            self.assertEqual(0, len(r), msg='Inserting an image with a duplicate hash on same file should be ignored silently')

    async def test_08_insert_duplicate_imagehash_on_other_files(self):
        self.assertNotEqual(self.FILE1.name, self.FILE2.name,
                            msg='Prepare two files with different names')
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            file2 = await self.db_manager.insert_file(session, self.FILE2)
            await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            r = await self.db_manager.insert_images(session, [self.IMAGE1], file2.id)
            self.assertEqual(0, len(r), msg='Inserting an image with a duplicate hash on other files should be ignored silently')

    async def test_09_get_existent_images(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            r = await self.db_manager.get_images(session, file1.id)
            self.assertEqual(1, len(r))

    async def test_10_get_non_existent_images(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            r = await self.db_manager.get_images(session, file1.id)
            self.assertEqual(0, len(r))

    async def test_11_get_non_existent_image(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_image(session, 1)

    async def test_12_get_non_existent_image_silently(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_image(session, 1, silent=True)
            self.assertIsNone(r)

    async def test_13_insert_regions(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            r = await self.db_manager.insert_regions(session, [schemas.RegionCreate(**self.REGION_BASE1,
                                                                                    **{'image_id': image1.id})])
            self.assertEqual(1, len(r))

    async def test_14_update_labels_when_inserting_non_existent_region(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            regions = await self.db_manager.insert_regions(session, [schemas.RegionCreate(**self.REGION_BASE1,
                                                                                          **{'image_id': image1.id})])
            region1 = regions[0]
            for k, v in region1.labels.items():
                if k in self.REGION_BASE1['labels']:
                    self.assertEqual(self.REGION_BASE1['labels'][k], v,
                                     msg=f'The value of label type "{k}" should be same with query')
                else:
                    self.assertIsNone(v, msg=f'The value of label type "{k}" should be None')

    async def test_15_update_labels_when_inserting_existent_region(self):
        """
        재학습 등의 이유로 저장된 영역의 라벨만 업데이트해야하는 경우가 있다.
        재학습 시에는 새로 검출되는 영역도 포함될 수 있어 insert 함수를 사용한다.
        따라서 insert 함수는 이미 존재하는 영역인 경우에 라벨 값을 갱신할 수 있어야 한다.
        """
        self.assertEqual({self.REGION_BASE1[k] for k in ['rx1', 'ry1', 'rx2', 'ry2']},
                         {self.REGION_BASE2[k] for k in ['rx1', 'ry1', 'rx2', 'ry2']},
                         msg='Prepare two regions with same bounding box')
        self.assertNotEqual(self.REGION_BASE1['labels'].keys(), self.REGION_BASE2['labels'].keys(),
                            msg='Prepare two regions with different label types')
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            regions = await self.db_manager.insert_regions(session, [schemas.RegionCreate(**self.REGION_BASE1,
                                                                                          **{'image_id': image1.id})])
            region_id = regions[0].id

            await self.db_manager.insert_regions(session, [schemas.RegionCreate(**self.REGION_BASE2,
                                                                                **{'image_id': image1.id})])

            region1 = await self.db_manager.get_region(session, region_id)
            for k, v in region1.labels.items():
                if k in self.REGION_BASE2['labels']:
                    self.assertEqual(self.REGION_BASE2['labels'][k], v,
                                     msg=f'The value of label type "{k}" should be same with query')
                else:
                    self.assertIsNone(v, msg=f'The value of label type "{k}" should be None')

    async def test_17_get_regions_with_image_id(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            await self.db_manager.insert_regions(session, [schemas.RegionCreate(**self.REGION_BASE1,
                                                                                **{'image_id': image1.id})])

            r = await self.db_manager.get_regions(session, image1.id)
            self.assertEqual(1, len(r))

    async def test_18_get_regions_with_file_id(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            await self.db_manager.insert_regions(session, [schemas.RegionCreate(**self.REGION_BASE1,
                                                                                **{'image_id': image1.id})])

            r = await self.db_manager.get_regions(session, file1.id)
            self.assertEqual(1, len(r))

    async def test_19_delete_image_automatically_in_cascade(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            await self.db_manager.delete_file(session, file1.id)
            with self.assertRaises(ParameterNotFoundError,
                                   msg='Images should be automatically deleted when a related file is deleted'):
                await self.db_manager.get_image(session, image1.id)

    async def test_20_delete_region_automatically_in_cascade(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            regions = await self.db_manager.insert_regions(session, [schemas.RegionCreate(**self.REGION_BASE1,
                                                                                          **{'image_id': image1.id})])
            region1 = regions[0]

            await self.db_manager.delete_file(session, file1.id)
            with self.assertRaises(ParameterNotFoundError,
                                   msg='Regions should be automatically deleted when a related file is deleted'):
                await self.db_manager.get_region(session, region1.id)


if __name__ == '__main__':
    unittest.main(testLoader=unittest.TestLoader())
