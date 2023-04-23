from typing import List, Optional

from fastapi import APIRouter, Depends

from common.exceptions import ParameterValueError
from database.core import get_session
from app.label.schemas import LabelFilter
from app.label.utils import verify_label_filter, verify_label_sort
from .schemas import BBoxPaginated, BBoxRead, BBoxUpdate
from .service import get_all_paginated, update


router = APIRouter()


@router.get('', response_model=BBoxPaginated)
async def get_bboxes(image_id: Optional[int] = None, file_id: Optional[int] = None,
                     label_filter: Optional[LabelFilter] = Depends(verify_label_filter),
                     label_sort: Optional[List[dict]] = Depends(verify_label_sort),
                     page: int = 1, items_per_page: int = -1,
                     session=Depends(get_session)):
    bboxes = await get_all_paginated(
        session, image_id=image_id, file_id=file_id,
        label_filter=label_filter, label_sort=label_sort,
        page=page, items_per_page=items_per_page
    )
    return BBoxPaginated.parse_obj(bboxes)


@router.put('/{bbox_id}', response_model=BBoxRead)
async def update_bbox(bbox_id: int, bbox: BBoxUpdate, session=Depends(get_session)):
    if bbox_id != bbox.id:
        raise ParameterValueError(key='id', value=bbox.id, should=bbox_id)
    bbox = await update(session, bbox)
    return BBoxRead.from_orm(bbox)
