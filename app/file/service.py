from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from common.exceptions import ParameterNotFoundError, ParameterExistError
from .models import File
from .schemas import FileCreate, FileUpdate


async def get_all(session: AsyncSession) -> List[File]:
    return [o for o in (await session.scalars(select(File)))]


async def get_one(session: AsyncSession, file_id: int, silent=False) -> Optional[File]:
    r = await session.get(File, file_id)
    if r is None and not silent:
        raise ParameterNotFoundError(f'File {file_id}')
    return r


async def insert(session: AsyncSession, file: FileCreate) -> File:
    try:
        db_file = File(**file.dict())
        session.add(db_file)
        await session.commit()
        return db_file
    except IntegrityError:
        raise ParameterExistError(file.name)


async def update(session: AsyncSession, file: FileUpdate) -> File:
    db_file = await get_one(session, file.id)
    db_file.update(**file.dict(exclude_unset=True))
    session.add(db_file)
    await session.commit()
    return db_file


async def delete(session: AsyncSession, file_id: int):
    db_file = await get_one(session, file_id)
    await session.delete(db_file)
    await session.commit()
