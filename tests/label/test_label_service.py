import unittest
import os
from sqlalchemy.ext.asyncio import create_async_engine

from common.exceptions import ParameterNotFoundError
from app.label.schemas import LabelBase, LabelUpdate
from app.label.service import insert, get_one, update

from ..database import create_database, dispose_database, get_session, remove_session
from ..factories import LabelFactory


class TestLabelService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.dirname = os.path.dirname(os.path.realpath(__file__))
        self.dbname = 'test_label_service.db'
        self.engine = create_async_engine(f'sqlite+aiosqlite:///{self.dirname}/{self.dbname}')
        await create_database(self.engine)
        self.session = get_session(self.engine)

    async def asyncTearDown(self) -> None:
        await remove_session(self.session)
        await dispose_database(self.engine)
        os.remove(f'{self.dirname}/{self.dbname}')

    async def test_insert(self):
        bbox_id = 1
        label = LabelFactory.build()
        r = await insert(self.session,
                         pairs=[(bbox_id,
                                 LabelBase(region=label.region,
                                           style=label.style,
                                           category=label.category,
                                           fabric=label.fabric))])
        self.assertEqual(1, len(r))
        self.assertIsNotNone(r[0].id)
        self.assertEqual(bbox_id, r[0].bbox_id)

    async def test_get_exists(self):
        label = LabelFactory(unused=False, reviewed=False)

        r = await get_one(self.session, label_id=label.id)
        self.assertIsNotNone(r)

    async def testget_non_exists(self):
        with self.assertRaises(ParameterNotFoundError):
            await get_one(self.session, int(1e9))

    async def test_update(self):
        label1 = LabelFactory()
        unused = not label1.unused
        reviewed = not label1.reviewed

        r = await update(self.session, LabelUpdate(id=label1.id,
                                                   unused=unused,
                                                   reviewed=reviewed))
        self.assertIsNotNone(r)
        self.assertEqual(unused, r.unused)
        self.assertEqual(reviewed, r.reviewed)
