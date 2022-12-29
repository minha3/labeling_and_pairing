import asyncio
import os

import uvicorn
import logging

from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Depends, Response
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

from config import load_config
from label import load_labels
from file_manager import FileManager
from db import DBManager
from inference import InferenceClient
from common import schemas
from common.exceptions import *
from app.verifiers import *
from app.exception_handler import exception_handler

CONFIG = load_config(dirname=os.environ.get('LAP_PATH_CONFIG'), read_envs=True)
db_manager = DBManager(db_config=CONFIG['db'])
file_manager = FileManager(data_dir=CONFIG['path']['data'])
inference_client = InferenceClient(config=CONFIG['inference'])

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://0.0.0.0:5001', 'http://localhost:5001'],
    # allow_origins=["*"],
    allow_methods=['*'],
    allow_headers=['*']
)


@app.on_event("startup")
async def startup_event():
    print('start')
    await db_manager.create_all(drop=CONFIG.get('clear'))
    file_manager.create_all(drop=CONFIG.get('clear'))
    load_labels(dir_name=CONFIG['path']['label'])


@app.on_event("shutdown")
def shutdown_event():
    print('shutdown')
    asyncio.get_event_loop().create_task(db_manager.close())


@app.get('/ping')
def ping():
    return Response(status_code=204)


@app.post('/files', response_model=schemas.File, dependencies=[Depends(verify_csv_file)])
@exception_handler
async def create_file(file: UploadFile = File(...), session=Depends(db_manager.get_session)):
    file_info = await file_manager.save_file(file.filename, await file.read())
    r = await db_manager.insert_file(session, file_info)
    if r:
        asyncio.create_task(download_images(schemas.File.from_orm(r)))
    return r


@app.get('/files', response_model=List[schemas.File])
@exception_handler
async def get_files(session=Depends(db_manager.get_session)):
    return await db_manager.get_files(session)


@app.get('/files/{file_id}', response_model=schemas.File)
@exception_handler
async def get_file(file_id: int, session=Depends(db_manager.get_session)):
    return await db_manager.get_file(session, file_id)


@app.delete('/files/{file_id}')
@exception_handler
async def delete_file(file_id: int, session=Depends(db_manager.get_session)):
    db_file = await db_manager.get_file(session, file_id)
    if db_file:
        await file_manager.remove_file(db_file.name)
        await db_manager.delete_file(session, file_id)
    return Response(status_code=204)


async def download_images(file: schemas.File):
    async for session in db_manager.get_session():
        status, content = await file_manager.urls_from_file(file.name, silent=True)
        if status:
            file.cnt_url = len(content)
        else:
            file.cnt_url = -1
            file.error = content
        try:
            await db_manager.update_file(session, file)
        except ParameterError as e:
            logging.critical(f'Failed to update vale {file.cnt_url} '
                             f'to cnt_url column of file "{file.name}". reason: {e}')
            return

        if not status:
            return

        images = await file_manager.download_images(content)

        try:
            db_images = await db_manager.insert_images(session=session, images=images, file_id=file.id)
        except ParameterError as e:
            logging.critical(f'Failed to insert images in file "{file.name}" to DB. reason: {e}')
            return

        try:
            file.cnt_download_failure = file.cnt_url - len(images)
            file.cnt_image = len(db_images)
            file.cnt_duplicated_image = len(images) - len(db_images)
            await db_manager.update_file(session, file)
        except ParameterError as e:
            logging.critical(f'Failed to update values '
                             f'({file.cnt_download_failure}, {file.cnt_image}, {file.cnt_duplicated_image}) '
                             f'to (cnt_download_failure, cnt_image, cnt_duplicated_image) columns '
                             f'of file "{file.name}". reason: {e}')
            return

        if not db_images:
            return

        asyncio.create_task(infer_images(file))


async def infer_images(file: schemas.File):
    async for session in db_manager.get_session():
        if not inference_client.enabled():
            file.cnt_region = -1
            file.error = 'Inference client is disabled'
        elif await inference_client.ping():
            db_images = await db_manager.get_images(session, file.id)
            inference_images = []
            for db_image in db_images:
                image_ = schemas.Image.from_orm(db_image)
                db_image_path = file_manager.get_image_file_path(image_.hash)
                inference_images.append((image_, db_image_path))

            result = await inference_client.infer(inference_images)
            try:
                db_bboxes = await db_manager.insert_bboxes(session=session, pairs=[(o[0], o[1]) for o in result])
                file.cnt_bbox = len(db_bboxes)
            except Exception as e:
                file.cnt_bbox = -1
                file.error = 'Failed to insert bboxes'
                logging.critical(f'Failed to insert bboxes of file {file.id}. reason: {e}')
            else:
                try:
                    await db_manager.insert_labels(session=session,
                                                   pairs=[(db_bboxes[i].id, result[i][2]) for i in range(len(result))
                                                          if db_bboxes[i] and result[i][2]])
                except Exception as e:
                    file.error = 'Failed to insert labels'
                    logging.critical(f'Failed to insert labels of file {file.id}. reason: {e}')
        else:
            file.cnt_region = -1
            file.error = 'Failed to check the health of inference server'

        try:
            await db_manager.update_file(session, file)
        except ParameterError as e:
            logging.critical(f'Failed to update value {file.cnt_region} '
                             f'to cnt_region column of file "{file.name}". reason: {e}')
            return


@app.get('/images', response_model=List[schemas.Image])
@exception_handler
async def get_images(file_id: int, session=Depends(db_manager.get_session)):
    return await db_manager.get_images(session, file_id)


@app.get('/images/{image_id}')
@exception_handler
async def get_image(image_id: int, session=Depends(db_manager.get_session)):
    db_image = await db_manager.get_image(session, image_id)
    image_path = file_manager.get_image_file_path(db_image.hash)
    return FileResponse(path=image_path)


@app.get('/bboxes', response_model=List[schemas.BBox])
@exception_handler
async def get_bboxes(image_id: Optional[int] = None, file_id: Optional[int] = None,
                     unused: Optional[bool] = None, reviewed: Optional[bool] = None,
                     session=Depends(db_manager.get_session)):
    return await db_manager.get_bboxes(session, image_id=image_id, file_id=file_id,
                                       unused=unused, reviewed=reviewed)


@app.put('/labels/{label_id}', response_model=schemas.Label)
@exception_handler
async def update_label(label_id: int, label: schemas.Label, session=Depends(db_manager.get_session)):
    if label_id != label.id:
        raise HTTPException(status_code=400, detail='Resource id in the path and '
                                                    'resource id in the payload is different')
    return await db_manager.update_label(session, label)


@app.get('/export/{file_id}')
@exception_handler
async def export(file_id: int, filters: dict = Depends(verify_filter), session=Depends(db_manager.get_session)):
    file = await db_manager.get_file(session, file_id)
    dirname = f"{file.name.split('.')[0]}_{datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
    data = await db_manager.get_data_to_export(session, file_id, unused=False, reviewed=True, **filters)
    dirpath = await file_manager.export_to_yolo(dirname, data)
    return {'path': dirpath}


if __name__ == '__main__':
    uvicorn.run("app:app", host=CONFIG['http']['host'], port=CONFIG['http']['port'])
