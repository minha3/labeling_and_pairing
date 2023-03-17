import unittest
import os
from sqlalchemy.ext.asyncio import create_async_engine

from app.bbox.schemas import BBoxBase
from app.bbox.service import insert, get_all
from app.label.schemas import LabelFilter

from ..database import create_database, dispose_database, get_session, remove_session
from ..factories import FileFactory, ImageFactory, BBoxFactory, LabelFactory


class TestBBoxService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.dirname = os.path.dirname(os.path.realpath(__file__))
        self.dbname = 'test_bbox_service.db'
        self.engine = create_async_engine(f'sqlite+aiosqlite:///{self.dirname}/{self.dbname}')
        await create_database(self.engine)
        self.session = get_session(self.engine)

    async def asyncTearDown(self) -> None:
        await remove_session(self.session)
        await dispose_database(self.engine)
        os.remove(f'{self.dirname}/{self.dbname}')

    async def test_insert(self):
        image_id = 1
        bbox = BBoxFactory.build()
        r = await insert(self.session,
                         pairs=[(image_id, BBoxBase(rx1=bbox.rx1, ry1=bbox.ry1,
                                                    rx2=bbox.rx2, ry2=bbox.ry2))])
        self.assertEqual(1, len(r))
        self.assertIsNotNone(r[0].id)
        self.assertEqual(image_id, r[0].image_id)

    async def test_get_all_with_image_id(self):
        image = ImageFactory()
        BBoxFactory(image=image)
        BBoxFactory(image=image)
        r = await get_all(self.session, image_id=image.id)
        self.assertEqual(2, len(r))
        self.assertTrue(all(o.image_id == image.id for o in r))

    async def test_get_all_with_file_id(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        BBoxFactory(image=image)
        BBoxFactory(image=image)
        r = await get_all(self.session, file_id=file.id)
        self.assertEqual(2, len(r))
        self.assertTrue(all(o.image.file_id == file.id for o in r))

    async def test_get_all_with_label_filter(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox1 = BBoxFactory(image=image)
        LabelFactory(unused=False, reviewed=False, bbox=bbox1)
        bbox2 = BBoxFactory(image=image)
        LabelFactory(unused=True, reviewed=True, bbox=bbox2)
        r = await get_all(self.session, file_id=file.id, label_filter=LabelFilter(unused=False))
        self.assertEqual(1, len(r))
        self.assertEqual(bbox1.id, r[0].id)
        self.assertFalse(r[0].label.unused)
        r = await get_all(self.session, file_id=file.id, label_filter=LabelFilter(reviewed=True))
        self.assertEqual(1, len(r))
        self.assertEqual(bbox2.id, r[0].id)
        self.assertTrue(r[0].label.reviewed)

    async def test_get_all_with_label_sort_asc(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox1 = BBoxFactory(image=image)
        label1 = LabelFactory(unused=False, reviewed=False, bbox=bbox1)
        bbox2 = BBoxFactory(image=image)
        label2 = LabelFactory(unused=True, reviewed=True, bbox=bbox2)
        r = await get_all(self.session, file_id=file.id,
                          label_sort=[{'field': 'region', 'direction': 'asc'}])
        self.assertEqual(2, len(r))
        self.assertEqual(sorted([label1.region, label2.region]),
                         [o.label.region for o in r])

    async def test_get_all_with_label_sort_desc(self):
        file = FileFactory()
        image = ImageFactory(file=file)
        bbox1 = BBoxFactory(image=image)
        label1 = LabelFactory(unused=False, reviewed=False, bbox=bbox1)
        bbox2 = BBoxFactory(image=image)
        label2 = LabelFactory(unused=True, reviewed=True, bbox=bbox2)
        r = await get_all(self.session, file_id=file.id,
                          label_sort=[{'field': 'region', 'direction': 'desc'}])
        self.assertEqual(2, len(r))
        self.assertEqual(sorted([label1.region, label2.region], reverse=True),
                         [o.label.region for o in r])
