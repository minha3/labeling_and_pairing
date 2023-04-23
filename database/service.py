from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import selectable

from common.exceptions import ParameterNotFoundError

from .core import SQLAlchemyModel


def joined_table_names(stmt: selectable):
    joined = set()
    for o in stmt.froms:
        if hasattr(o, 'left'):
            joined.add(o.left.fullname)
        if hasattr(o, 'right'):
            joined.add(o.right.fullname)
    return joined


async def get_one(session: AsyncSession, model: Type[SQLAlchemyModel], id_: int, silent: bool = False) -> SQLAlchemyModel:
    r = await session.get(model, id_)
    if r is None and not silent:
        raise ParameterNotFoundError(f'{model.__name__} {id_}')
    return r
