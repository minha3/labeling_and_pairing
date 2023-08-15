import logging

from config import CONFIG
from common.exceptions import ParameterError
from database.core import get_session
from app.file.schemas import FileRead, FileUpdate
from app.file.service import update as update_file
from app.image.service import get_all as get_images
from app.image.schemas import ImageRead
from app.image.utils import get_image_file_path
from app.bbox.service import insert as insert_bboxes
from app.label.service import insert as insert_labels
from .utils import TorchServeClient


async def infer(file: FileRead):
    inference_images = []

    async for session in get_session():
        db_images = await get_images(session, file.id)
        for db_image in db_images:
            image_ = ImageRead.from_orm(db_image)
            db_image_path = get_image_file_path(image_.hash)
            inference_images.append((image_, db_image_path))

        if not inference_images:
            file.cnt_bbox = 0
        else:
            try:
                inference_client = TorchServeClient(config=CONFIG['inference_server'])
                result = await inference_client.infer(inference_images)
            except Exception as e:
                file.cnt_bbox = -1
                file.error = f'Failed to get inference result'
                logging.critical(f'Failed to get inference result. reason: {e}')
            else:
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

        try:
            await update_file(session, FileUpdate(**file.dict()))
        except ParameterError as e:
            logging.critical(f'Failed to update file {file.id}. reason: {e}')
            return
