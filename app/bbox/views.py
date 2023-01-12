from typing import List, Optional

from fastapi import APIRouter, Depends

from common.exception_handler import exception_handler
from database.core import get_session
from app.label.schemas import LabelFilter
from app.label.utils import verify_label_filter
from .schemas import BBoxRead
from .service import get_all


router = APIRouter()


@router.get('', response_model=List[BBoxRead])
@exception_handler
async def get_bboxes(image_id: Optional[int] = None, file_id: Optional[int] = None,
                     label_filter: Optional[LabelFilter] = Depends(verify_label_filter),
                     session=Depends(get_session)):
    return await get_all(session, image_id=image_id, file_id=file_id, label_filter=label_filter)
