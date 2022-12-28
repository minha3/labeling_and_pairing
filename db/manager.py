from typing import List, AsyncIterable, Optional, Tuple

from db.models import *
from config import load_config
from common import schemas
from common.exceptions import *

from sqlalchemy import select, true
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


class DBManager:
    def __init__(self, db_config: dict = None):
        if db_config is None:
            db_config = load_config(read_envs=True)['db']
        if db_config['dialect'] == 'sqlite':
            self.engine = create_async_engine(
                "{dialect}+{driver}:///{dbname}".format(**db_config), encoding='utf-8', echo=False, future=True)
        else:
            self.engine = create_async_engine("{dialect}+{driver}://{user}:{password}@{host}/{dbname}".format(**db_config),
                                              encoding='utf-8', echo=False, future=True)
        self.async_session = sessionmaker(bind=self.engine, expire_on_commit=False, class_=AsyncSession)

    async def close(self):
        await self.engine.dispose()

    async def create_all(self, drop=False):
        async with self.engine.begin() as conn:
            if drop:
                await conn.run_sync(metadata.drop_all)
            await conn.run_sync(metadata.create_all)

    async def drop_all(self, create=False):
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
            if create:
                await conn.run_sync(metadata.create_all)

    async def get_session(self) -> AsyncIterable:
        async with self.async_session() as session:
            yield session

    @staticmethod
    async def insert_file(session: AsyncSession, file: schemas.FileCreate) -> File:
        db_file = File(**file.dict())
        session.add(db_file)
        await session.commit()
        return db_file

    @staticmethod
    async def update_file(session: AsyncSession, file: schemas.File) -> File:
        db_file = await DBManager.get_file(session, file.id)
        db_file.update(**file.dict(exclude_unset=True))
        session.add(db_file)
        await session.commit()
        return db_file

    @staticmethod
    async def get_files(session: AsyncSession) -> List[File]:
        return [o for o in (await session.scalars(select(File)))]

    @staticmethod
    async def get_file(session: AsyncSession, file_id: int, silent=False) -> Optional[File]:
        r = await session.get(File, file_id)
        if r is None and not silent:
            raise ParameterNotFoundError(f'File {file_id}')
        return r

    @staticmethod
    async def delete_file(session: AsyncSession, file_id: int):
        db_file = await DBManager.get_file(session, file_id)
        await session.delete(db_file)
        await session.commit()

    @staticmethod
    async def insert_images(session: AsyncSession, images: List[schemas.ImageCreate], file_id: int) -> List[Image]:
        result = []
        await DBManager.get_file(session, file_id)
        cnt_dup = 0
        for image in images:
            db_image = await session.scalar(select(Image).where(Image.hash == image.hash))
            if db_image is None:
                db_image = Image(hash=image.hash, width=image.width, height=image.height, url=image.url,
                                 file_id=file_id)
                result.append(db_image)
                session.add(db_image)
            else:
                cnt_dup += 1
        await session.commit()
        return result

    @staticmethod
    async def get_images(session: AsyncSession, file_id: int) -> List[Image]:
        return [o for o in (await session.scalars(select(Image).where(Image.file_id == file_id)))]

    @staticmethod
    async def get_image(session: AsyncSession, image_id: int, silent=False) -> Optional[Image]:
        r = await session.get(Image, image_id)
        if r is None and not silent:
            raise ParameterNotFoundError(f'Image {image_id}')
        return r

    @staticmethod
    async def insert_bboxes(session: AsyncSession, pairs: List[Tuple[int, schemas.BBoxBase]], silent=True) -> List[
        Optional[BBox]]:
        result = []
        for image_id, bbox_base in pairs:
            db_image = await DBManager.get_image(session, image_id, silent=silent)
            if db_image is None:
                result.append(None)
                continue
            query = select(BBox).where(BBox.image_id == image_id)
            for k in ['rx1', 'ry1', 'rx2', 'ry2']:
                query = query.where(getattr(BBox, k) == getattr(bbox_base, k))

            db_bbox = await session.scalar(query)

            if db_bbox is None:
                db_bbox = BBox(image_id=image_id, rx1=bbox_base.rx1, ry1=bbox_base.ry1,
                               rx2=bbox_base.rx2, ry2=bbox_base.ry2)
                session.add(db_bbox)
                result.append(db_bbox)
            else:
                result.append(None)
        await session.commit()
        return result

    @staticmethod
    async def get_bboxes(session: AsyncSession, image_id: int = None, file_id: int = None, **kwargs) -> List[BBox]:
        stmt = select(BBox).execution_options(populate_existing=True)
        if image_id:
            stmt = stmt.where(BBox.image_id == image_id)
        elif file_id:
            stmt = stmt.join(Image).where(Image.file_id == file_id)

        join_label = False
        for k, v in kwargs.items():
            if v is not None and hasattr(Label, k):
                stmt = stmt.where(getattr(Label, k) == v)
                join_label = True

        if join_label:
            stmt = stmt.join(Label)

        return list(await session.scalars(stmt))

    @staticmethod
    async def get_bbox(session: AsyncSession, bbox_id: int, silent=False) -> BBox:
        r = await session.get(BBox, bbox_id, populate_existing=True)
        if r is None and not silent:
            raise ParameterNotFoundError(f'BBox {bbox_id}')
        return r

    @staticmethod
    async def insert_labels(session: AsyncSession, pairs: List[Tuple[int, schemas.LabelBase]], silent=True) -> \
            List[Optional[Label]]:
        result = []
        for bbox_id, label in pairs:
            bbox = DBManager.get_bbox(session, bbox_id, silent=silent)
            if bbox is None:
                result.append(None)
                continue
            query = select(Label).where(Label.bbox_id == bbox_id)
            db_label = await session.scalar(query)

            if db_label is None:
                db_label = Label(bbox_id=bbox_id, **label.dict(exclude_unset=True))
                session.add(db_label)
                result.append(db_label)
            else:
                result.append(None)
        await session.commit()
        return result

    @staticmethod
    async def get_label(session: AsyncSession, label_id: int, silent: bool = False) -> Label:
        r = await session.get(Label, label_id)
        if r is None and not silent:
            raise ParameterNotFoundError(f'Label {label_id}')
        return r

    @staticmethod
    async def update_label(session: AsyncSession, label: schemas.Label) -> Label:
        db_label = await DBManager.get_label(session, label.id)
        for k, v in label.dict().items():
            if k not in ['id', 'bbox_id'] and hasattr(db_label, k):
                setattr(db_label, k, v)
        session.add(db_label)
        await session.commit()
        return db_label
