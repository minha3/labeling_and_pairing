import unittest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import IntegrityError
from ..database import create_database, dispose_database, get_session, remove_session
from ..factories import FileFactory, ImageFactory, BBoxFactory, LabelFactory
from db import DBManager
from common import schemas
from common.exceptions import ParameterNotFoundError


class TestDBManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine('sqlite+aiosqlite:///./test_db_manager.db')
        await create_database(self.engine)
        self.session = get_session(self.engine)

    async def asyncTearDown(self) -> None:
        await remove_session(self.session)
        await dispose_database(self.engine)

    async def test_insert_file(self):
        file = FileFactory.build()
        r = await DBManager.insert_file(self.session, schemas.FileCreate(name=file.name, size=file.size))
        self.assertIsNotNone(r)
        self.assertIsNotNone(r.id)

    async def test_insert_duplicate_filename(self):
        file = FileFactory()
        with self.assertRaises(IntegrityError,
                               msg='Inserting a file with a duplicate name results in an error'):
            await DBManager.insert_file(self.session, schemas.FileCreate(name=file.name, size=file.size))

    async def test_get_existent_file(self):
        file = FileFactory()
        r = await DBManager.get_file(self.session, file.id)
        self.assertEqual(file.id, r.id)

    async def test_get_non_existent_file(self):
        with self.assertRaises(ParameterNotFoundError):
            await DBManager.get_file(self.session, int(1e9))

    async def test_get_non_existent_file_silently(self):
        r = await DBManager.get_file(self.session, int(1e9), silent=True)
        self.assertIsNone(r)

    async def test_insert_images(self):
        file = FileFactory()
        image = ImageFactory.build()
        r = await DBManager.insert_images(self.session,
                                          [schemas.ImageCreate(
                                              hash=image.hash, width=image.width, height=image.height, url=image.url)],
                                          file_id=file.id)
        self.assertEqual(1, len(r))
        self.assertIsNotNone(r[0].id)
        self.assertIsNotNone(r[0].file_id)

    async def test_insert_duplicate_imagehash_on_same_file(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        r = await DBManager.insert_images(self.session,
                                          [schemas.ImageCreate(
                                              hash=image.hash, width=image.width, height=image.height, url=image.url)],
                                          file_id=image.file_id)
        self.assertEqual(0, len(r),
                         msg='Inserting an image with a duplicate hash on same file should be ignored silently')

    async def test_insert_duplicate_imagehash_on_other_files(self):
        file1 = FileFactory()
        file2 = FileFactory()
        image = ImageFactory(file=file1)
        r = await DBManager.insert_images(self.session,
                                          [schemas.ImageCreate(
                                              hash=image.hash, width=image.width, height=image.height, url=image.url)],
                                          file_id=file2.id)
        self.assertEqual(0, len(r),
                         msg='Inserting an image with a duplicate hash on other files should be ignored silently')

    async def test_get_existent_images(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        r = await DBManager.get_images(self.session, file_id=image.file_id)
        self.assertEqual(1, len(r))
        self.assertEqual(image.id, r[0].id)

    async def test_get_image(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        r = await DBManager.get_image(self.session, image_id=image.id)
        self.assertIsNotNone(r)

    async def test_get_non_existent_image(self):
        with self.assertRaises(ParameterNotFoundError):
            await DBManager.get_image(self.session, int(1e9))

    async def test_get_non_existent_image_silently(self):
        r = await DBManager.get_image(self.session, int(1e9), silent=True)
        self.assertIsNone(r)

    async def test_delete_image_automatically_in_cascade(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        await DBManager.delete_file(self.session, file_id=image.file_id)
        r = await DBManager.get_images(self.session, file_id=image.file_id)
        self.assertEqual(0, len(r))
        with self.assertRaises(ParameterNotFoundError,
                               msg='Images should be automatically deleted when a related file is deleted'):
            await DBManager.get_image(self.session, image_id=image.id)

    async def test_insert_bboxes(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory.build()
        r = await DBManager.insert_bboxes(self.session,
                                          pairs=[(image.id,
                                                  schemas.BBoxBase(rx1=bbox.rx1, ry1=bbox.ry1,
                                                                   rx2=bbox.rx2, ry2=bbox.ry2))])
        self.assertEqual(1, len(r))
        self.assertIsNotNone(r[0].id)
        self.assertIsNotNone(r[0].image_id)

    async def test_get_bboxes_with_image_id(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        r = await DBManager.get_bboxes(self.session, image_id=bbox.image_id)
        self.assertEqual(1, len(r))
        self.assertEqual(bbox.id, r[0].id)

    async def test_get_bboxes_with_file_id(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        r = await DBManager.get_bboxes(self.session, file_id=file.id)
        self.assertEqual(1, len(r))
        self.assertEqual(bbox.id, r[0].id)

    async def test_delete_bbox_automatically_in_cascade(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        r = await DBManager.get_bbox(self.session, bbox.id)
        self.assertIsNotNone(r)
        await DBManager.delete_file(self.session, file_id=file.id)
        with self.assertRaises(ParameterNotFoundError,
                               msg='BBoxes should be automatically deleted when a related file is deleted'):
            await DBManager.get_bbox(self.session, bbox.id)

    async def test_insert_labels(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        label = LabelFactory.build()
        r = await DBManager.insert_labels(self.session,
                                          pairs=[(bbox.id,
                                                  schemas.LabelBase(region=label.region,
                                                                    style=label.style,
                                                                    category=label.category,
                                                                    fabric=label.fabric))])
        self.assertEqual(1, len(r))
        self.assertIsNotNone(r[0].id)
        self.assertIsNotNone(r[0].bbox_id)

    async def test_get_bbox_with_label(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        label = LabelFactory(bbox=bbox)
        r = await DBManager.get_bbox(self.session, bbox_id=bbox.id)
        self.assertIsNotNone(r)
        self.assertIsNotNone(r.label)
        self.assertEqual(label.id, r.label.id)

    async def test_get_bboxes_with_label(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        label = LabelFactory(bbox=bbox)
        r = await DBManager.get_bboxes(self.session, file_id=file.id)
        self.assertEqual(1, len(r))
        self.assertIsNotNone(r[0].label)
        self.assertEqual(label.id, r[0].label.id)

    async def test_get_bboxes_with_filters(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox1 = BBoxFactory(image=image)
        LabelFactory(unused=False, reviewed=False, bbox=bbox1)
        bbox2 = BBoxFactory(image=image)
        LabelFactory(unused=True, reviewed=True, bbox=bbox2)
        r = await DBManager.get_bboxes(self.session, file_id=file.id, label_filter=schemas.LabelFilter(unused=False))
        self.assertEqual(1, len(r))
        self.assertEqual(bbox1.id, r[0].id)
        self.assertFalse(r[0].label.unused)
        r = await DBManager.get_bboxes(self.session, file_id=file.id, label_filter=schemas.LabelFilter(reviewed=True))
        self.assertEqual(1, len(r))
        self.assertEqual(bbox2.id, r[0].id)
        self.assertTrue(r[0].label.reviewed)

    async def test_get_existent_label(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        label = LabelFactory(unused=False, reviewed=False, bbox=bbox)

        r = await DBManager.get_label(self.session, label_id=label.id)
        self.assertIsNotNone(r)

    async def testget_non_existent_label(self):
        with self.assertRaises(ParameterNotFoundError):
            await DBManager.get_label(self.session, int(1e9))

    async def test_update_label(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox = BBoxFactory(image=image)
        label1 = LabelFactory(bbox=bbox)
        unused = not label1.unused
        reviewed = not label1.reviewed

        r = await DBManager.update_label(self.session, schemas.Label(id=label1.id,
                                                                     bbox_id=bbox.id,
                                                                     region=label1.region,
                                                                     style=label1.style,
                                                                     category=label1.category,
                                                                     fabric=label1.fabric,
                                                                     unused=unused,
                                                                     reviewed=reviewed))
        self.assertIsNotNone(r)
        self.assertEqual(unused, r.unused)
        self.assertEqual(reviewed, r.reviewed)


if __name__ == '__main__':
    unittest.main(testLoader=unittest.TestLoader())
