from typing import List, Optional

from fastapi import APIRouter, Depends

from database.core import get_session
from app.label.schemas import LabelFilter
from app.label.utils import verify_label_filter, verify_label_sort
from .schemas import BBoxPaginated
from .service import get_all_paginated


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

