import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, UploadFile, Response

from common.exceptions import ParameterError
from database.core import get_session
from app.image.service import insert as insert_images
from app.model_inference.service import infer as infer_images

from .schemas import FileRead, FileUpdate
from .service import insert, get_all, get_one, delete, update
from .utils import verify_csv_file, save_file, remove_file, urls_from_file, download_images


router = APIRouter()


@router.post('', response_model=FileRead)
async def create_file(file: UploadFile = Depends(verify_csv_file), session=Depends(get_session)):
    file_info, _ = await save_file(file)
    db_file = await insert(session, file_info)
    if db_file:
        asyncio.create_task(download_and_infer(db_file))
    return db_file


@router.get('', response_model=List[FileRead])
async def get_files(session=Depends(get_session)):
    return await get_all(session)


@router.get('/{file_id}', response_model=FileRead)
async def get_file(file_id: int, session=Depends(get_session)):
    return await get_one(session, file_id)


@router.delete('/{file_id}')
async def delete_file(file_id: int, session=Depends(get_session)):
    db_file = await get_one(session, file_id)
    if db_file:
        await delete(session, file_id)
        await remove_file(db_file.name)
    return Response(status_code=204)


async def download_and_infer(file: FileRead):
    async for session in get_session():
        status, content = await urls_from_file(file.name, silent=True)
        if status:
            file.cnt_url = len(content)
        else:
            file.cnt_url = -1
            file.error = content
        try:
            await update(session, FileUpdate(**file.dict()))
        except ParameterError as e:
            logging.critical(f'Failed to update vale {file.cnt_url} '
                             f'to cnt_url column of file "{file.name}". reason: {e}')
            return

        if not status:
            return

        images = await download_images(content)

        try:
            db_images = await insert_images(session=session, images=images, file_id=file.id)
        except ParameterError as e:
            logging.critical(f'Failed to insert images in file "{file.name}" to DB. reason: {e}')
            return

        try:
            file.cnt_download_failure = file.cnt_url - len(images)
            file.cnt_image = len(db_images)
            file.cnt_duplicated_image = len(images) - len(db_images)
            await update(session, FileUpdate(**file.dict()))
        except ParameterError as e:
            logging.critical(f'Failed to update values '
                             f'({file.cnt_download_failure}, {file.cnt_image}, {file.cnt_duplicated_image}) '
                             f'to (cnt_download_failure, cnt_image, cnt_duplicated_image) columns '
                             f'of file "{file.name}". reason: {e}')
            return

        if not db_images:
            return

    asyncio.create_task(infer_images(file))
