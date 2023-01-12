from asyncio import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from database.core import Base

Session = async_scoped_session(sessionmaker(class_=AsyncSession, expire_on_commit=False), scopefunc=current_task)


async def create_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def dispose_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def get_session(engine):
    Session.configure(bind=engine)
    return Session()


async def remove_session(session):
    await session.rollback()
    await session.close()
    await Session.remove()
