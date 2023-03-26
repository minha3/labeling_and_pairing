from typing import List, Tuple, Optional

from sqlalchemy import select
from sqlalchemy.sql import selectable
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import ParameterNotFoundError
from app.bbox.models import BBox
from app.image.models import Image
from app.file.models import File
from .models import Label
from .schemas import LabelBase, LabelUpdate, LabelFilter


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


async def get_all(session: AsyncSession, file_id: Optional[int] = None,
                  label_filter: Optional[LabelFilter] = None):
    stmt = select(Label)
    stmt = _stmt_file_id(stmt, file_id)
    stmt = _stmt_label_filter(stmt, label_filter)

    return [o for o in await session.scalars(stmt)]


def _stmt_file_id(stmt: selectable, file_id: Optional[int] = None):
    if file_id is not None:
        stmt = stmt.join(BBox).filter(Label.bbox_id == BBox.id)
        stmt = stmt.join(Image).filter(BBox.image_id == Image.id)
        stmt = stmt.join(File).filter(Image.file_id == file_id)
    return stmt


def _stmt_label_filter(stmt: selectable, label_filter: Optional[LabelFilter] = None):
    if label_filter:
        for k, v in label_filter.dict(exclude_unset=True, exclude_none=True).items():
            if type(v) == list:
                stmt = stmt.where(getattr(Label, k).in_(v))
            else:
                stmt = stmt.where(getattr(Label, k) == v)
    return stmt
