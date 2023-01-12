import unittest
import os
from sqlalchemy.ext.asyncio import create_async_engine

from app.file.schemas import FileCreate, FileUpdate
from app.file.service import insert, get_all, get_one, update, delete
from common.exceptions import ParameterExistError, ParameterNotFoundError

from ..database import create_database, dispose_database, get_session, remove_session
from ..factories import FileFactory


class TestFileService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.dirname = os.path.dirname(os.path.realpath(__file__))
        self.dbname = 'test_file_service.db'
        self.engine = create_async_engine(f'sqlite+aiosqlite:///{self.dirname}/{self.dbname}')
        await create_database(self.engine)
        self.session = get_session(self.engine)

    async def asyncTearDown(self) -> None:
        await remove_session(self.session)
        await dispose_database(self.engine)
        os.remove(f'{self.dirname}/{self.dbname}')

    async def test_insert(self):
        file = FileFactory.build()
        r = await insert(self.session, FileCreate(name=file.name, size=file.size))
        self.assertIsNotNone(r)
        self.assertIsNotNone(r.id)

    async def test_insert_duplicate_filename(self):
        file = FileFactory()
        with self.assertRaises(ParameterExistError,
                               msg='Inserting a file with a duplicate name results in an error'):
            await insert(self.session, FileCreate(name=file.name, size=file.size))

    async def test_get_all(self):
        FileFactory()
        FileFactory()
        r = await get_all(self.session)
        self.assertEqual(2, len(r))

    async def test_get_exists(self):
        file = FileFactory()
        r = await get_one(self.session, file.id)
        self.assertIsNotNone(r)

    async def test_get_non_exists(self):
        with self.assertRaises(ParameterNotFoundError):
            await get_one(self.session, int(1e9), silent=False)

    async def test_get_non_exists_silently(self):
        r = await get_one(self.session, int(1e9), silent=True)
        self.assertIsNone(r)

    async def test_update(self):
        file = FileFactory()
        new_cnt_url = file.cnt_url + 1
        r = await update(self.session, FileUpdate(id=file.id, cnt_url=new_cnt_url))
        self.assertEqual(new_cnt_url, r.cnt_url)

    async def test_delete(self):
        file = FileFactory()
        await delete(self.session, file.id)
        with self.assertRaises(ParameterNotFoundError):
            await get_one(self.session, file.id)
