from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from common.exception_handler import exception_handler
from database.core import get_session

from .schemas import ImageRead
from .service import get_all, get_one
from .utils import get_image_file_path

router = APIRouter()


@router.get('', response_model=List[ImageRead])
@exception_handler
async def get_images(file_id: int, session=Depends(get_session)):
    return await get_all(session, file_id)


@router.get('/{image_id}')
@exception_handler
async def get_image(image_id: int, session=Depends(get_session)):
    db_image = await get_one(session, image_id)
    image_path = get_image_file_path(db_image.hash)
    return FileResponse(path=image_path)
