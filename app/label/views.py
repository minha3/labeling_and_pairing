from fastapi import APIRouter, Depends, HTTPException

from database.core import get_session
from .schemas import LabelRead, LabelUpdate
from .service import update

router = APIRouter()


@router.put('/{label_id}', response_model=LabelRead)
async def update_label(label_id: int, label: LabelUpdate, session=Depends(get_session)):
    if label_id != label.id:
        raise HTTPException(status_code=400, detail='Resource id in the path and '
                                                    'resource id in the payload is different')
    return await update(session, label)
