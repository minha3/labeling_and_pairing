from typing import List, Tuple, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import ParameterNotFoundError
from .models import Label
from .schemas import LabelBase, LabelUpdate


async def insert(session: AsyncSession,
                 pairs: List[Tuple[int, LabelBase]]) -> List[Optional[Label]]:
    result = []
    for bbox_id, label in pairs:
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


async def get_one(session: AsyncSession, label_id: int, silent: bool = False) -> Label:
    r = await session.get(Label, label_id)
    if r is None and not silent:
        raise ParameterNotFoundError(f'Label {label_id}')
    return r


async def update(session: AsyncSession, label: LabelUpdate) -> Label:
    db_label = await get_one(session, label.id)
    db_label.update(**label.dict(exclude_unset=True))
    session.add(db_label)
    await session.commit()
    return db_label
