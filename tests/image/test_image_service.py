import unittest
import os
from sqlalchemy.ext.asyncio import create_async_engine

from app.image.schemas import ImageBase
from app.image.service import insert, get_all, get_one
from common.exceptions import ParameterNotFoundError

from ..database import create_database, dispose_database, get_session, remove_session
from ..factories import FileFactory, ImageFactory


class TestImageService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.dirname = os.path.dirname(os.path.realpath(__file__))
        self.dbname = 'test_image_service.db'
        self.engine = create_async_engine(f'sqlite+aiosqlite:///{self.dirname}/{self.dbname}')
        await create_database(self.engine)
        self.session = get_session(self.engine)

    async def asyncTearDown(self) -> None:
        await remove_session(self.session)
        await dispose_database(self.engine)
        os.remove(f'{self.dirname}/{self.dbname}')

    async def test_insert(self):
        file = FileFactory()
        image = ImageFactory.build()
        r = await insert(self.session,
                         [ImageBase(
                             hash=image.hash, width=image.width, height=image.height, url=image.url)],
                         file_id=file.id)
        self.assertEqual(1, len(r))
        self.assertIsNotNone(r[0].id)
        self.assertEqual(file.id, r[0].file_id)

    async def test_insert_duplicate_imagehash_on_same_file(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        r = await insert(self.session,
                         [ImageBase(
                             hash=image.hash, width=image.width, height=image.height, url=image.url)],
                         file_id=image.file_id)
        self.assertEqual(0, len(r),
                         msg='Inserting an image with a duplicate hash on same file should be ignored silently')

    async def test_insert_duplicate_imagehash_on_other_files(self):
        file1 = FileFactory()
        file2 = FileFactory()
        image = ImageFactory(file=file1)
        r = await insert(self.session,
                         [ImageBase(
                             hash=image.hash, width=image.width, height=image.height, url=image.url)],
                         file_id=file2.id)
        self.assertEqual(0, len(r),
                         msg='Inserting an image with a duplicate hash on other files should be ignored silently')

    async def test_get_all(self):
        file = FileFactory()
        ImageFactory(file=file)
        ImageFactory(file=file)
        r = await get_all(self.session, file_id=file.id)
        self.assertEqual(2, len(r))
        self.assertTrue(all(o.file_id == file.id for o in r))

    async def test_get_exists(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        r = await get_one(self.session, image_id=image.id)
        self.assertIsNotNone(r)
        self.assertEqual(file.id, r.file_id)

    async def test_get_non_exists(self):
        with self.assertRaises(ParameterNotFoundError):
            await get_one(self.session, int(1e9), silent=False)

    async def test_get_non_exists_silently(self):
        r = await get_one(self.session, int(1e9), silent=True)
        self.assertIsNone(r)
