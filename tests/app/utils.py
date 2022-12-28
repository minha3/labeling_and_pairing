import os
import shutil
import yaml
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from db.models import *
from common import schemas

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lap_config.yml'), 'r') as f:
    test_config = yaml.load(f, Loader=yaml.SafeLoader)

SQLALCHEMY_DATABASE_URL = "{dialect}+{driver}:///{dbname}".format(**test_config['db'])
DB_ENGINE = create_async_engine(SQLALCHEMY_DATABASE_URL)
DB_SESSION = sessionmaker(bind=DB_ENGINE, expire_on_commit=False, class_=AsyncSession)


async def insert_testset():
    my_dir = os.path.dirname(os.path.realpath(__file__))
    shutil.copytree(os.path.join(my_dir, '../pre_downloaded_images'), os.path.join(my_dir, 'images'), dirs_exist_ok=True)
    async with DB_SESSION() as session:
        with open(os.path.join(my_dir, 'db_data.yml'), 'r') as f:
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
