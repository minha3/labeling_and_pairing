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
        self.BBOX_BASE1 = schemas.BBoxBase(**self.db_data['bbox1'])
        self.BBOX_BASE2 = schemas.BBoxBase(**self.db_data['bbox2'])
        self.BBOX_BASE3 = schemas.BBoxBase(**self.db_data['bbox3'])
        self.LABEL_BASE1 = schemas.LabelBase(**self.db_data['label1'])
        self.LABEL_BASE2 = schemas.LabelBase(**self.db_data['label2'])
        self.LABEL_BASE3 = schemas.LabelBase(**self.db_data['label3'])

        load_labels()
        self.db_manager = DBManager(db_config={'dialect': 'sqlite',
                                               'driver': 'aiosqlite',
                                               'dbname': './test_db_manager.db'})
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

    async def test_04_file_from_orm(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_file(session, self.FILE1)
            r = await self.db_manager.get_file(session, r.id)
            self.assertIsNotNone(schemas.File.from_orm(r))

    async def test_05_get_non_existent_file(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_file(session, 1)

    async def test_06_get_non_existent_file_silently(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_file(session, 1, silent=True)
            self.assertIsNone(r)

    async def test_07_insert_images(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            r = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            self.assertEqual(1, len(r))

    async def test_08_insert_duplicate_imagehash_on_same_file(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            r = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            self.assertEqual(0, len(r), msg='Inserting an image with a duplicate hash on same file should be ignored silently')

    async def test_09_insert_duplicate_imagehash_on_other_files(self):
        self.assertNotEqual(self.FILE1.name, self.FILE2.name,
                            msg='Prepare two files with different names')
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            file2 = await self.db_manager.insert_file(session, self.FILE2)
            await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            r = await self.db_manager.insert_images(session, [self.IMAGE1], file2.id)
            self.assertEqual(0, len(r), msg='Inserting an image with a duplicate hash on other files should be ignored silently')

    async def test_10_get_existent_images(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            r = await self.db_manager.get_images(session, file1.id)
            self.assertEqual(1, len(r))

    async def test_11_image_from_orm(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            r = await self.db_manager.get_images(session, file1.id)
            self.assertIsNotNone(schemas.Image.from_orm(r[0]))

    async def test_12_get_non_existent_images(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            r = await self.db_manager.get_images(session, file1.id)
            self.assertEqual(0, len(r))

    async def test_13_get_non_existent_image(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_image(session, 1)

    async def test_14_get_non_existent_image_silently(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_image(session, 1, silent=True)
            self.assertIsNone(r)

    async def test_15_delete_image_automatically_in_cascade(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            await self.db_manager.delete_file(session, file1.id)
            with self.assertRaises(ParameterNotFoundError,
                                   msg='Images should be automatically deleted when a related file is deleted'):
                await self.db_manager.get_image(session, image1.id)

    async def test_16_insert_bboxes(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            r = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            self.assertEqual(1, len(r))

    async def test_17_get_bboxes_with_image_id(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]
            await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])

            r = await self.db_manager.get_bboxes(session, image_id=image1.id)
            self.assertEqual(1, len(r))

    async def test_18_get_bboxes_with_file_id(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]
            await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])

            r = await self.db_manager.get_bboxes(session, file1.id)
            self.assertEqual(1, len(r))

    async def test_19_bbox_from_orm(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]
            await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])

            r = await self.db_manager.get_bboxes(session, file1.id)
            o = schemas.BBox.from_orm(r[0])
            self.assertIsNotNone(o)
            self.assertIsNone(o.label)

    async def test_20_delete_bbox_automatically_in_cascade(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            await self.db_manager.delete_file(session, file1.id)
            with self.assertRaises(ParameterNotFoundError,
                                   msg='BBoxes should be automatically deleted when a related file is deleted'):
                await self.db_manager.get_bbox(session, bbox1.id)

            r = await self.db_manager.get_bboxes(session, file_id=file1.id)
            self.assertEqual(0, len(r),
                             msg='BBoxes should be automatically deleted when a related file is deleted')

    async def test_21_insert_labels(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            r = await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])
            self.assertEqual(1, len(r))

    async def test_22_get_bbox_with_label(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])

            r = await self.db_manager.get_bbox(session, bbox_id=bbox1.id)
            self.assertEqual(self.LABEL_BASE1.region, r.label.region)

    async def test_23_get_bboxes_with_label(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])

            r = await self.db_manager.get_bboxes(session, file_id=file1.id)
            self.assertEqual(1, len(r))
            self.assertEqual(self.LABEL_BASE1.region, r[0].label.region)

    async def test_24_bbox_from_orm_with_label(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])

            r = await self.db_manager.get_bboxes(session, file_id=file1.id)
            o = schemas.BBox.from_orm(r[0])
            self.assertIsNotNone(o)
            self.assertIsNotNone(o.label)

    async def test_25_get_bboxes_with_filters(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])

            r = await self.db_manager.get_bboxes(session, file_id=file1.id, unused=False)
            self.assertEqual(1, len(r))
            self.assertEqual(self.LABEL_BASE1.region, r[0].label.region)

            r = await self.db_manager.get_bboxes(session, file_id=file1.id, reviewed=True)
            self.assertEqual(0, len(r))

    async def test_26_get_existent_label(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            labels = await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])
            label1 = labels[0]

            r = await self.db_manager.get_label(session, label1.id)
            self.assertIsNotNone(r)

    async def test_27_get_non_existent_label(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_label(session, 1)

    async def test_28_update_label(self):
        self.assertNotEqual(self.LABEL_BASE1.region, self.LABEL_BASE3.region,
                            msg='The region values of two regions should be different. '
                                'Because region value is used as filter option')
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)

            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]

            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]

            labels = await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])
            label1 = schemas.Label.from_orm(labels[0])
            label1.region = self.LABEL_BASE3.region

            label = await self.db_manager.update_label(session, label1)
            self.assertEqual(self.LABEL_BASE3.region, label.region)

    async def test_29_get_data_to_export_without_filter(self):
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]
            bboxes = await self.db_manager.insert_bboxes(session, [(image1.id, self.BBOX_BASE1), (image1.id, self.BBOX_BASE3)])
            await self.db_manager.insert_labels(session, [(bboxes[0].id, self.LABEL_BASE1), (bboxes[1].id, self.LABEL_BASE3)])

            export_data = await self.db_manager.get_data_to_export(session, file1.id)
            self.assertEqual(1, len(export_data))
            self.assertEqual(2, len(export_data[0].bboxes))

    async def test_30_get_data_to_export_with_filters(self):
        self.assertNotEqual(self.LABEL_BASE1.region, self.LABEL_BASE3.region,
                            msg='The region values of two regions should be different. '
                                'Because region value is used as filter option')
        async for session in self.db_manager.get_session():
            file1 = await self.db_manager.insert_file(session, self.FILE1)
            images = await self.db_manager.insert_images(session, [self.IMAGE1], file1.id)
            image1 = images[0]
            bboxes = await self.db_manager.insert_bboxes(session,
                                                         [(image1.id, self.BBOX_BASE1), (image1.id, self.BBOX_BASE3)])
            await self.db_manager.insert_labels(session,
                                                [(bboxes[0].id, self.LABEL_BASE1), (bboxes[1].id, self.LABEL_BASE3)])

            export_data = await self.db_manager.get_data_to_export(session, file1.id, region='top')
            self.assertEqual(1, len(export_data))
            self.assertTrue(o.label.region == 'top' for o in export_data[0].bboxes)


if __name__ == '__main__':
    unittest.main(testLoader=unittest.TestLoader())
