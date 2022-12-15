import os
import shutil
import yaml
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from db.models import *

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lap_config.yml'), 'r') as f:
    test_config = yaml.load(f, Loader=yaml.SafeLoader)

SQLALCHEMY_DATABASE_URL = "{dialect}+{driver}:///{dbname}".format(**test_config['db'])
DB_ENGINE = create_async_engine(SQLALCHEMY_DATABASE_URL)
DB_SESSION = sessionmaker(bind=DB_ENGINE, expire_on_commit=False, class_=AsyncSession)


def obj_to_dict(obj):
    return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}


async def insert_testset():
    my_dir = os.path.dirname(os.path.realpath(__file__))
    shutil.copytree(os.path.join(my_dir, 'pre_downloaded_images'), os.path.join(my_dir, 'images'), dirs_exist_ok=True)
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
            db_regions = []
            for image in file['images']:
                db_image = Image()
                for k, v in image.items():
                    if hasattr(db_image, k) and type(v) != list:
                        setattr(db_image, k, v)
                db_image.file = db_file
                session.add(db_image)
                db_images.append(db_image)
                for region in image['regions']:
                    db_region = Region()
                    for k, v in region.items():
                        if hasattr(db_region, k) and type(v) != list:
                            setattr(db_region, k, v)
                    db_region.image = db_image
                    session.add(db_region)
                    db_regions.append(db_region)
            await session.commit()
            result.append({'file': obj_to_dict(db_file),
                           'images': [obj_to_dict(o) for o in db_images],
                           'regions': [obj_to_dict(o) for o in db_regions]})
    return result
