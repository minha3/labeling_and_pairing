from typing import Optional
from fastapi import APIRouter, Depends

from common.exceptions import ParameterValueError
from database.core import get_session
from .schemas import LabelRead, LabelUpdate, LabelFilter, LabelStatisticsRead
from .service import update, get_all
from .utils import verify_label_filter, label_statistics

router = APIRouter()


@router.put('/{label_id}', response_model=LabelRead)
async def update_label(label_id: int, label: LabelUpdate, session=Depends(get_session)):
    if label_id != label.id:
        raise ParameterValueError(key='id', value=label.id, should=label_id)
    return await update(session, label)


@router.get('/statistics', response_model=LabelStatisticsRead)
async def get_statistics(file_id: Optional[int] = None,
                         label_filter: Optional[LabelFilter] = Depends(verify_label_filter),
                         session=Depends(get_session)):
    labels = await get_all(session, file_id, label_filter)
    return LabelStatisticsRead(**label_statistics(labels))
