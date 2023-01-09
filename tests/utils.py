import os
import shutil
import yaml
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from db.models import *
from common import schemas

MY_DIR = os.path.dirname(os.path.realpath(__file__))


def insert_image_files(dirname=None):
    if dirname is None:
        dirname = os.environ.get('LAP_PATH_DATA')
    shutil.copytree(os.path.join(MY_DIR, 'pre_downloaded_images'), os.path.join(dirname, 'images'),
                    dirs_exist_ok=True)


async def insert_db_data(dbname=None):
    if dbname is None:
        dbname = os.environ.get('LAP_DB_DBNAME')
    sqlalchemy_database_url = f"sqlite+aiosqlite:///{dbname}"
    db_engine = create_async_engine(sqlalchemy_database_url)
    db_session = sessionmaker(bind=db_engine, expire_on_commit=False, class_=AsyncSession)
    async with db_session() as session:
        with open(os.path.join(MY_DIR, 'db_data.yml'), 'r') as f:
            test_data = yaml.load(f, Loader=yaml.SafeLoader)
        result = []
        for file in test_data['files']:
            db_file = File()
            for k, v in file.items():
                if hasattr(db_file, k) and type(v) != list:
                    setattr(db_file, k, v)
            session.add(db_file)
            db_images = []
            db_bboxes = []
            for image in file['images']:
                db_image = Image()
                for k, v in image.items():
                    if k != 'bboxes':
                        setattr(db_image, k, v)
                db_image.file = db_file
                session.add(db_image)
                db_images.append(db_image)
                for bbox in image['bboxes']:
                    db_bbox = BBox()
                    for k, v in bbox.items():
                        if k != 'label':
                            setattr(db_bbox, k, v)
                    db_bbox.image = db_image

                    db_label = Label()
                    for k, v in bbox['label'].items():
                        setattr(db_label, k, v)
                    db_bbox.label = db_label

                    session.add(db_label)
                    session.add(db_bbox)
                    db_bboxes.append(db_bbox)
            await session.commit()
            result.append({'file': schemas.File.from_orm(db_file),
                           'images': [schemas.Image.from_orm(o) for o in db_images],
                           'bboxes': [schemas.BBox.from_orm(o) for o in db_bboxes]})
    return result
