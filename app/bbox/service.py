from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

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
                  label_filter: LabelFilter = None) -> List[BBox]:
    stmt = select(BBox).options(selectinload(BBox.image)).execution_options(populate_existing=True)
    if image_id:
        stmt = stmt.where(BBox.image_id == image_id)
    elif file_id:
        stmt = stmt.join(Image).where(Image.file_id == file_id)

    if label_filter:
        stmt = stmt.join(Label)
        for k, v in label_filter.dict(exclude_unset=True, exclude_none=True).items():
            if type(v) == list:
                stmt = stmt.where(getattr(Label, k).in_(v))
            else:
                stmt = stmt.where(getattr(Label, k) == v)

    return list(await session.scalars(stmt))
