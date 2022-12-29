import aiohttp
import aiofiles
import aiofiles.os
import hashlib
import io
import os
import PIL.Image
import shutil
import string
import imghdr
import yaml
import pickle
from urllib.parse import urlparse
from typing import Tuple, Union, List
from aiocsv import AsyncReader

from config import load_config
from common.aiopool import AioTaskPool
from common.schemas import *
from common.exceptions import *
from db.models import Image as DBImage
from label import *


class FileManager:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = load_config(read_envs=True)['path']['data']
        if data_dir is None:
            raise ParameterError('No data storage path is set. '
                                 'Set the value of the key "path.data" in configuration file. '
                                 'Alternatively, set the value of environment variable "LAP_PATH_DATA"')
        self.image_dir = os.path.join(data_dir, 'images')
        self.file_dir = os.path.join(data_dir, 'files')
        self.export_dir = os.path.join(data_dir, 'exports')
        self.csv_fields = ['url']

    def create_all(self, drop=False):
        for target_dir in [self.image_dir, self.file_dir, self.export_dir]:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            elif drop:
                shutil.rmtree(target_dir)
                os.makedirs(target_dir)

    def drop_all(self, create=False):
        for target_dir in [self.image_dir, self.file_dir, self.export_dir]:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            if create:
                os.makedirs(target_dir)

    async def save_file(self, name, content) -> FileCreate:
        if not content:
            raise ParameterEmptyError(name)
        file_path = os.path.join(self.file_dir, name)
        if os.path.exists(file_path):
            raise ParameterExistError(name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return FileCreate(name=name, size=os.path.getsize(file_path))

    async def remove_file(self, name: str) -> None:
        file_path = os.path.join(self.file_dir, name)
        if os.path.exists(file_path):
            await aiofiles.os.remove(file_path)

    async def download_images(self, image_urls: List[str]) -> List[ImageCreate]:
        async with aiohttp.ClientSession() as session:
            async with AioTaskPool(tasks=10) as pool:
                for url in image_urls:
                    pool.apply(self._download_image_task(session, url))
                images = await pool.wait()

        return [o[1] for o in images if type(o) == tuple and o[0]]

    async def _download_image_task(self, session, image_url) -> Tuple[bool, Union[str, ImageCreate]]:
        async with session.get(image_url) as response:
            if response.status != 200:
                return False, f'url: {image_url}. response: {response.status}'
            if response.content_length == 0:
                return False, f'url: {image_url}. content-length: 0'

            image_data = await response.read()
            if len(image_data) == 0:
                return False, f'url: {image_url}. data-length: 0'

            if not self.verify_image_file(None, image_data):
                return False, f'url: {image_url}. failed to determine image type'

            try:
                image_hash = hashlib.sha256(image_data).hexdigest()
                image_file = self.get_image_file_path(image_hash, not_exist_ok=True)
                image_dir = os.path.dirname(image_file)
                os.makedirs(image_dir, exist_ok=True)
                if not os.path.exists(image_file):
                    async with aiofiles.open(image_file, 'wb') as f:
                        await f.write(image_data)

                pil_image = PIL.Image.open(io.BytesIO(image_data))
                return True, ImageCreate(hash=image_hash, width=pil_image.width, height=pil_image.height,
                                         url=image_url)
            except Exception as e:
                return False, str(e)

    @staticmethod
    def verify_image_file(filename, content=None):
        return imghdr.what(filename, content) is not None

    @staticmethod
    def verify_url(url: str):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    async def urls_from_file(self, name: str, silent: bool = False) -> Tuple[bool, Union[str, List[str]]]:
        file_path = os.path.join(self.file_dir, name)
        urls = []
        try:
            if not os.path.exists(file_path):
                raise ParameterNotFoundError(file_path)

            async with aiofiles.open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = AsyncReader(f)
                fields = await reader.__anext__()
                if fields == self.csv_fields:
                    async for row in reader:
                        if self.verify_url(row[0]):
                            urls.append(row[0])
                else:
                    raise ParameterValueError(key='First line of csv file', value=','.join(fields),
                                              should=','.join(self.csv_fields))
            return True, urls
        except StopAsyncIteration:
            raise ParameterEmptyError(file_path)
        except Exception as e:
            if silent:
                return False, str(e)
            else:
                raise e

    def get_image_file_path(self, image_hash: str, not_exist_ok=False, return_relative=False) -> str:
        if not all(c in string.hexdigits for c in image_hash):
            raise ParameterValueError(key='hash', value=image_hash, should='hex string')

        relative_path = os.path.join(image_hash[:2], f'{image_hash}.jpg')
        full_path = os.path.join(self.image_dir, relative_path)
        if not not_exist_ok and not os.path.exists(full_path):
            raise ParameterNotFoundError(image_hash)

        if return_relative:
            return relative_path
        else:
            return full_path

    async def export_to_yolo(self, dirname: str, images: List[DBImage]) -> Optional[str]:
        if len(images) < 2:
            raise ParameterError('Count of reviewed labels should be at least 2 to export.')

        root_dir = os.path.join(self.export_dir, dirname)
        os.makedirs(root_dir, exist_ok=True)
        cnt_train = max(1, int(len(images) * 0.7))
        idx_range = {'train': range(0, cnt_train), 'val': range(cnt_train, len(images))}

        labels_ = {l: i for i, l in enumerate(sorted(label_names_by_type('region')))}
        config = {'path': dirname, 'train': None, 'val': None, 'test': '',
                  'nc': len(labels_), 'names': {v: k for k, v in labels_.items()}}

        for usage in ['train', 'val']:
            bbox_dir = os.path.join(root_dir, 'labels', usage)
            rel_image_dir = os.path.join('images', usage)
            image_dir = os.path.join(root_dir, rel_image_dir)
            label_dir = os.path.join(root_dir, 'annotations', usage)
            os.makedirs(bbox_dir, exist_ok=True)
            os.makedirs(image_dir, exist_ok=True)
            os.makedirs(label_dir, exist_ok=True)
            config[usage] = rel_image_dir

            labels = []
            for i in idx_range[usage]:
                image = images[i]
                origin_image_path = self.get_image_file_path(image.hash)
                rel_origin_image_path = self.get_image_file_path(image.hash, return_relative=True)
                target_image_path = os.path.join(image_dir, rel_origin_image_path)
                os.makedirs(os.path.dirname(target_image_path), exist_ok=True)
                os.symlink(origin_image_path, target_image_path)

                target_bbox_path = os.path.join(bbox_dir, rel_origin_image_path).replace('.jpg', '.txt')
                os.makedirs(os.path.dirname(target_bbox_path), exist_ok=True)
                async with aiofiles.open(target_bbox_path, 'w') as f:
                    for bbox in image.bboxes:
                        width, height = image.width, image.height
                        bwidth, bheight = bbox.rx2 - bbox.rx1, bbox.ry2 - bbox.ry1
                        await f.write(
                            f'{labels_[bbox.label.region]} {bwidth / 2 + bbox.rx1} {bheight / 2 + bbox.ry1} '
                            f'{bwidth} {bheight}\n')

                        label_data = {'path': os.path.join(rel_image_dir, rel_origin_image_path),
                                      'width': width,
                                      'height': height,
                                      'bbox': [int(width * bbox.rx1), int(height * bbox.ry1),
                                               int(width * bbox.rx2), int(height * bbox.ry2)]}
                        for label_type in bbox.label.column_keys():
                            if label_type in label_types():
                                label_name = getattr(bbox.label, label_type)
                                label_data[translate(label_type)] = translate(label_name, label_type)

                        labels.append(label_data)

            with open(os.path.join(label_dir, 'annotations.pickle'), 'wb') as f:
                pickle.dump(labels, f)

        with open(os.path.join(root_dir, 'configuration.yml'), 'w') as f:
            yaml.safe_dump(config, f)

        return root_dir
