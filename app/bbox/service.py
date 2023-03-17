from typing import List, Optional, Tuple

from sqlalchemy import select, asc, desc, func
from sqlalchemy.sql import selectable
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.service import joined_table_names
from app.image.models import Image
from app.label.models import Label
from app.label.schemas import LabelFilter
from .models import BBox
from .schemas import BBoxBase


async def insert(session: AsyncSession, pairs: List[Tuple[int, BBoxBase]]) -> \
        List[Optional[BBox]]:
    result = []
    for image_id, bbox_base in pairs:
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


async def get_all(session: AsyncSession, image_id: int = None, file_id: int = None,
                  label_filter: LabelFilter = None,
                  label_sort: Optional[List[dict]] = None) -> List[BBox]:
    stmt = _stmt_bbox()
    stmt = _stmt_image_id(stmt, image_id)
    stmt = _stmt_file_id(stmt, file_id)
    stmt = _stmt_label_filter(stmt, label_filter)
    stmt = _stmt_label_sort(stmt, label_sort)

    return list(await session.scalars(stmt))


async def get_all_paginated(session: AsyncSession, image_id: int = None, file_id: int = None,
                            label_filter: LabelFilter = None,
                            label_sort: Optional[List[dict]] = None,
                            page: int = 1, items_per_page: int = -1) -> dict:
    stmt = _stmt_bbox()
    stmt = _stmt_image_id(stmt, image_id)
    stmt = _stmt_file_id(stmt, file_id)
    stmt = _stmt_label_filter(stmt, label_filter)
    stmt = _stmt_label_sort(stmt, label_sort)

    total_count = await session.scalar(select(func.count()).select_from(stmt))
    stmt = _stmt_pagination(stmt, page, items_per_page, total_count)

    items = list(await session.scalars(stmt))

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "items_per_page": items_per_page
    }


def _stmt_bbox():
    return select(BBox).options(selectinload(BBox.image)).execution_options(populate_existing=True)


def _stmt_image_id(stmt: selectable, image_id: Optional[int] = None):
    if image_id:
        stmt = stmt.where(BBox.image_id == image_id)
    return stmt


def _stmt_file_id(stmt: selectable, file_id: Optional[int] = None):
    if file_id:
        stmt = stmt.join(Image).where(Image.file_id == file_id)
    return stmt


def _stmt_label_filter(stmt: selectable, label_filter: Optional[LabelFilter] = None):
    if label_filter:
        if Label.__tablename__ not in joined_table_names(stmt):
            stmt = stmt.join(Label)

        for k, v in label_filter.dict(exclude_unset=True, exclude_none=True).items():
            if type(v) == list:
                stmt = stmt.where(getattr(Label, k).in_(v))
            else:
                stmt = stmt.where(getattr(Label, k) == v)
    return stmt


def _stmt_label_sort(stmt: selectable, label_sort: Optional[List[dict]] = None):
    if label_sort:
        if Label.__tablename__ not in joined_table_names(stmt):
            stmt = stmt.join(Label)
        for sort in label_sort:
            direction_func = asc if sort['direction'] == 'asc' else desc
            stmt = stmt.order_by(direction_func(getattr(Label, sort['field'])))
    return stmt


def _stmt_pagination(stmt: selectable, page: int = 1, items_per_page: int = -1, total_count: int = 0):
    total_count = max(0, total_count)
    page = max(1, page)
    items_per_page = (
        min(items_per_page, total_count)
        if items_per_page > 0
        else
        total_count
    )

    return stmt.offset((page - 1) * items_per_page).limit(items_per_page)
