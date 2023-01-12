import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, UploadFile, Response

from config import CONFIG
from common.exceptions import ParameterError
from common.exception_handler import exception_handler
from database.core import get_session
from inference import InferenceClient
from app.image.schemas import ImageRead
from app.image.service import insert as insert_images, get_all as get_images
from app.image.utils import get_image_file_path
from app.bbox.service import insert as insert_bboxes
from app.label.service import insert as insert_labels

from .schemas import FileRead, FileUpdate
from .service import insert, get_all, get_one, delete, update
from .utils import verify_csv_file, save_file, remove_file, urls_from_file, download_images


router = APIRouter()


@router.post('', response_model=FileRead)
@exception_handler
async def create_file(file: UploadFile = Depends(verify_csv_file), session=Depends(get_session)):
    file_info, _ = await save_file(file)
    db_file = await insert(session, file_info)
    if db_file:
        asyncio.create_task(download_images_from_file(FileRead.from_orm(db_file)))
    return db_file


@router.get('', response_model=List[FileRead])
@exception_handler
async def get_files(session=Depends(get_session)):
    return await get_all(session)


@router.get('/{file_id}', response_model=FileRead)
@exception_handler
async def get_file(file_id: int, session=Depends(get_session)):
    return await get_one(session, file_id)


@router.delete('/{file_id}')
@exception_handler
async def delete_file(file_id: int, session=Depends(get_session)):
    db_file = await get_one(session, file_id)
    if db_file:
        await delete(session, file_id)
        await remove_file(db_file.name)
    return Response(status_code=204)


async def download_images_from_file(file: FileRead):
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


async def infer_images(file: FileRead):
    inference_client = InferenceClient(config=CONFIG['inference'])

    async for session in get_session():
        if not inference_client.enabled():
            file.cnt_region = -1
            file.error = 'Inference client is disabled'
        elif await inference_client.ping():
            db_images = await get_images(session, file.id)
            inference_images = []
            for db_image in db_images:
                image_ = ImageRead.from_orm(db_image)
                db_image_path = get_image_file_path(image_.hash)
                inference_images.append((image_, db_image_path))

            result = await inference_client.infer(inference_images)

            try:
                db_bboxes = await insert_bboxes(session=session, pairs=[(o[0], o[1]) for o in result])
                file.cnt_bbox = len(db_bboxes)
            except Exception as e:
                file.cnt_bbox = -1
                file.error = 'Failed to insert bboxes'
                logging.critical(f'Failed to insert bboxes of file {file.id}. reason: {e}')
            else:
                try:
                    await insert_labels(session=session,
                                        pairs=[(db_bboxes[i].id, result[i][2]) for i in range(len(result))
                                               if db_bboxes[i] and result[i][2]])
                except Exception as e:
                    file.error = 'Failed to insert labels'
                    logging.critical(f'Failed to insert labels of file {file.id}. reason: {e}')
        else:
            file.cnt_region = -1
            file.error = 'Failed to check the health of inference server'

        try:
            await update(session, FileUpdate(**file.dict()))
        except ParameterError as e:
            logging.critical(f'Failed to update value {file.cnt_region} '
                             f'to cnt_region column of file "{file.name}". reason: {e}')
            return
