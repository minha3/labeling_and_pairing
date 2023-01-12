from datetime import datetime

from fastapi import APIRouter, Depends

from common.exceptions import ParameterValueError
from common.exception_handler import exception_handler
from database.core import get_session
from app.file.service import get_one as get_file
from app.bbox.service import get_all as get_bboxes
from app.label.schemas import LabelFilter
from app.label.utils import verify_label_filter

from .utils import export_to_yolo

router = APIRouter()


@router.post('')
@exception_handler
async def create(file_id: int, label_filter: LabelFilter = Depends(verify_label_filter),
                 session=Depends(get_session)):
    file = await get_file(session, file_id=file_id, silent=True)
    if file is None:
        raise ParameterValueError(key='file_id', value=file_id)
    dirname = f"{file.name.split('.')[0]}_{datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
    data = await get_bboxes(session, file_id=file_id, label_filter=label_filter)
    dirpath = await export_to_yolo(dirname, data)
    return {'path': dirpath}
