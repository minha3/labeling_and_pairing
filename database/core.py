import asyncio
from typing import AsyncIterable, Optional, TypeVar
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_scoped_session

from config import CONFIG


engine: Optional[AsyncEngine]

Session = async_scoped_session(sessionmaker(expire_on_commit=False, class_=AsyncSession),
                               scopefunc=asyncio.current_task)


class CustomBase:

    @property
    def _columns_exclude_updating(self):
        return []

    def column_keys(self):
        return self.__table__.columns.keys()

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in self._columns_exclude_updating and k in self.__table__.columns.keys():
                setattr(self, k, v)

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Base = declarative_base(cls=CustomBase)
SQLAlchemyModel = TypeVar('SQLAlchemyModel', bound=Base)


def create_engine(uri: str = None):
    global engine
    if uri is None:
        if CONFIG['db']['dialect'] == 'sqlite':
            uri = '{dialect}+{driver}:///{dbname}'.format(**CONFIG['db'])
        else:
            uri = '{dialect}+{driver}://{user}:{password}@{host}/{dbname}'.format(**CONFIG['db'])
    engine = create_async_engine(uri, echo=False)
    Session.configure(bind=engine)


async def create_tables(drop=False):
    async with engine.begin() as conn:
        if drop:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables(create=False):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        if create:
            await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterable:
    async with Session() as session:
        yield session
    await Session.remove()


async def get_test_session() -> AsyncIterable:
    async with Session() as session:
        yield session
        await session.rollback()
    await Session.remove()


async def dispose_engine():
    await engine.dispose()
