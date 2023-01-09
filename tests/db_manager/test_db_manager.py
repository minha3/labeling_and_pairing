import unittest
from string import ascii_lowercase, hexdigits
from random import choice, uniform

from sqlalchemy.exc import IntegrityError

from common import schemas
from common.exceptions import *
from tests.utils import insert_db_data
from label import load_labels, label_names_by_type
from db import DBManager


class TestDBManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.FILE_CREATE1 = schemas.FileCreate(name=''.join(choice(ascii_lowercase) for _ in range(8)),
                                               size=10)
        self.IMAGE_CREATE1 = schemas.ImageCreate(hash=''.join(choice(hexdigits) for _ in range(64)),
                                                 width=600, height=600, url='test_url1')
        self.BBOX_BASE1 = schemas.BBoxBase(rx1=uniform(0, 0.5), ry1=uniform(0, 0.5),
                                           rx2=uniform(0.5, 1.0), ry2=uniform(0.5, 1.0))
        self.LABEL_BASE1 = schemas.LabelBase(region='top', category='top', fabric='padded')

        load_labels()
        db_config = {'dialect': 'sqlite', 'driver': 'aiosqlite', 'dbname': './test_db_manager.db'}
        self.db_manager = DBManager(db_config=db_config)
        await self.db_manager.create_all(drop=True)
        self.DB_DATA = await insert_db_data(db_config['dbname'])

    async def asyncTearDown(self) -> None:
        await self.db_manager.drop_all()
        await self.db_manager.close()

    async def test_insert_file(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_file(session, self.FILE_CREATE1)
            self.assertIsNotNone(r)

    async def test_insert_duplicate_filename(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(IntegrityError, msg='Inserting a file with a duplicate name results in an error'):
                await self.db_manager.insert_file(session, self.DB_DATA[0]['file'])

    async def test_get_existent_file(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_file(session, self.DB_DATA[0]['file'].id)
            self.assertIsNotNone(r)
            self.assertIsNotNone(schemas.File.from_orm(r))

    async def test_get_non_existent_file(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_file(session, int(1e9))

    async def test_get_non_existent_file_silently(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_file(session, int(1e9), silent=True)
            self.assertIsNone(r)

    async def test_insert_images(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_images(session, [self.IMAGE_CREATE1], self.DB_DATA[0]['file'].id)
            self.assertEqual(1, len(r))

    async def test_insert_duplicate_imagehash_on_same_file(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_images(session, self.DB_DATA[0]['images'], self.DB_DATA[0]['file'].id)
            self.assertEqual(0, len(r), msg='Inserting an image with a duplicate hash on same file should be ignored silently')

    async def test_insert_duplicate_imagehash_on_other_files(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_images(session, self.DB_DATA[0]['images'], self.DB_DATA[1]['file'].id)
            self.assertEqual(0, len(r), msg='Inserting an image with a duplicate hash on other files should be ignored silently')

    async def test_get_existent_images(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_images(session, self.DB_DATA[0]['file'].id)
            self.assertGreaterEqual(len(r), 1)
            self.assertIsNotNone(schemas.Image.from_orm(r[0]))

    async def test_get_non_existent_image(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_image(session, int(1e9))

    async def test_get_non_existent_image_silently(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_image(session, int(1e9), silent=True)
            self.assertIsNone(r)

    async def test_delete_image_automatically_in_cascade(self):
        async for session in self.db_manager.get_session():
            await self.db_manager.delete_file(session, self.DB_DATA[0]['file'].id)
            with self.assertRaises(ParameterNotFoundError,
                                   msg='Images should be automatically deleted when a related file is deleted'):
                await self.db_manager.get_image(session, self.DB_DATA[0]['images'][0].id)

    async def test_insert_bboxes(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.insert_bboxes(session, [(self.DB_DATA[0]['images'][0].id, self.BBOX_BASE1)])
            self.assertEqual(1, len(r))

    async def test_get_bboxes_with_image_id(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_bboxes(session, image_id=self.DB_DATA[0]['images'][0].id)
            self.assertEqual(1, len(r))
            o = schemas.BBox.from_orm(r[0])
            self.assertIsNotNone(o)
            self.assertIsNotNone(o.label)

    async def test_get_bboxes_with_file_id(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_bboxes(session, self.DB_DATA[0]['file'].id)
            self.assertEqual(1, len(r))
            o = schemas.BBox.from_orm(r[0])
            self.assertIsNotNone(o)
            self.assertIsNotNone(o.label)

    async def test_delete_bbox_automatically_in_cascade(self):
        async for session in self.db_manager.get_session():
            await self.db_manager.delete_file(session, self.DB_DATA[0]['file'].id)
            with self.assertRaises(ParameterNotFoundError,
                                   msg='BBoxes should be automatically deleted when a related file is deleted'):
                await self.db_manager.get_bbox(session, self.DB_DATA[0]['bboxes'][0].id)

            r = await self.db_manager.get_bboxes(session, file_id=self.DB_DATA[0]['file'].id)
            self.assertEqual(0, len(r),
                             msg='BBoxes should be automatically deleted when a related file is deleted')

    async def test_insert_labels(self):
        async for session in self.db_manager.get_session():
            bboxes = await self.db_manager.insert_bboxes(session, [(self.DB_DATA[0]['images'][0].id, self.BBOX_BASE1)])
            bbox1 = bboxes[0]
            self.assertIsNotNone(bbox1)

            r = await self.db_manager.insert_labels(session, [(bbox1.id, self.LABEL_BASE1)])
            self.assertEqual(1, len(r))

    async def test_get_bbox_with_label(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_bbox(session, bbox_id=self.DB_DATA[0]['bboxes'][0].id)
            self.assertIsNotNone(r)
            self.assertIsNotNone(r.label)
            self.assertIsNotNone(r.label.region)

    async def test_get_bboxes_with_label(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_bboxes(session, file_id=self.DB_DATA[0]['file'].id)
            self.assertGreaterEqual(len(r), 1)
            self.assertIsNotNone(r[0].label)
            self.assertIsNotNone(r[0].label.region)

    async def test_get_bboxes_with_filters(self):
        async for session in self.db_manager.get_session():
            answer = len([o for o in self.DB_DATA[0]['bboxes'] if not o.label.unused])
            r = await self.db_manager.get_bboxes(session, file_id=self.DB_DATA[0]['file'].id, unused=False)
            self.assertEqual(answer, len(r))

            answer = len([o for o in self.DB_DATA[0]['bboxes'] if o.label.reviewed])
            r = await self.db_manager.get_bboxes(session, file_id=self.DB_DATA[0]['file'].id, reviewed=True)
            self.assertEqual(answer, len(r))

    async def test_get_existent_label(self):
        async for session in self.db_manager.get_session():
            r = await self.db_manager.get_label(session, self.DB_DATA[0]['bboxes'][0].label.id)
            self.assertIsNotNone(r)

    async def testget_non_existent_label(self):
        async for session in self.db_manager.get_session():
            with self.assertRaises(ParameterNotFoundError):
                await self.db_manager.get_label(session, int(1e9))

    async def test_update_label(self):
        async for session in self.db_manager.get_session():
            old = self.DB_DATA[0]['bboxes'][0].label.region
            for l in label_names_by_type('region'):
                if l != self.DB_DATA[0]['bboxes'][0].label.region:
                    self.DB_DATA[0]['bboxes'][0].label.region = l
                    break

            label = await self.db_manager.update_label(session, self.DB_DATA[0]['bboxes'][0].label)
            self.assertNotEqual(old, label.region)

    async def test_get_data_to_export_without_filter(self):
        async for session in self.db_manager.get_session():
            answer = len({o.image_id for o in self.DB_DATA[0]['bboxes']})
            export_data = await self.db_manager.get_data_to_export(session, self.DB_DATA[0]['file'].id)
            self.assertEqual(answer, len(export_data))

    async def test_get_data_to_export_with_filters(self):
        async for session in self.db_manager.get_session():
            answer = len({o.image_id for o in self.DB_DATA[0]['bboxes'] if o.label.region == 'top'})
            export_data = await self.db_manager.get_data_to_export(session, self.DB_DATA[0]['file'].id,
                                                                   region='top')
            self.assertEqual(answer, len(export_data))


if __name__ == '__main__':
    unittest.main(testLoader=unittest.TestLoader())
