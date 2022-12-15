from typing import List, AsyncIterable, Optional

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
                db_image = Image(hash=image.hash, width=image.width, height=image.height, url=image.url, file_id=file_id)
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
    async def insert_regions(session: AsyncSession, regions: List[schemas.RegionCreate]):
        result = []
        for region in regions:
            db_image = await DBManager.get_image(session, region.image_id, silent=True)
            if db_image is None:
                continue
            query = select(Region).where(Region.image_id == region.image_id)
            for k in ['rx1', 'ry1', 'rx2', 'ry2']:
                query = query.where(getattr(Region, k) == getattr(region, k))

            db_region = await session.scalar(query)

            if db_region is None:
                db_region = Region(image_id=region.image_id, rx1=region.rx1, ry1=region.ry1,
                                   rx2=region.rx2, ry2=region.ry2)
            db_region.update(**region.dict(exclude_unset=True))
            result.append(db_region)
            session.add(db_region)
        await session.commit()
        return [o.label_to_dict() for o in result]

    @staticmethod
    async def get_regions(session: AsyncSession, image_id: int = None, file_id: int = None):
        if image_id:
            query = await session.execute(select(Region).where(Region.use == true()).where(Region.image_id == image_id))
        elif file_id:
            query = await session.execute(select(Region).where(Region.use == true()).where(Image.file_id == file_id).join(Image))
        else:
            query = await session.execute(select(Region))

        return [o.label_to_dict() for o in query.scalars()]

    @staticmethod
    async def get_region(session: AsyncSession, region_id: int, silent=False):
        r = await session.get(Region, region_id)
        if r is None and not silent:
            raise ParameterNotFoundError(f'Region {region_id}')
        return r

    @staticmethod
    async def update_region(session: AsyncSession, region: schemas.Region):
        db_region = await DBManager.get_region(session, region.id)
        db_region.update(**region.dict(exclude_unset=True))
        session.add(db_region)
        await session.commit()
        return db_region.label_to_dict()
