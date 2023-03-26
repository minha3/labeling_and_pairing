from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from database.core import get_session
from .schemas import LabelRead, LabelUpdate, LabelFilter, LabelStatisticsRead
from .service import update, get_all
from .utils import verify_label_filter, label_statistics

router = APIRouter()


@router.put('/{label_id}', response_model=LabelRead)
async def update_label(label_id: int, label: LabelUpdate, session=Depends(get_session)):
    if label_id != label.id:
        raise HTTPException(status_code=400, detail='Resource id in the path and '
                                                    'resource id in the payload is different')
    return await update(session, label)


@router.get('/statistics', response_model=LabelStatisticsRead)
async def get_statistics(file_id: Optional[int] = None,
                         label_filter: Optional[LabelFilter] = Depends(verify_label_filter),
                         session=Depends(get_session)):
    labels = await get_all(session, file_id, label_filter)
    return LabelStatisticsRead(**label_statistics(labels))
