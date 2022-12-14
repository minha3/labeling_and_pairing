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
from urllib.parse import urlparse
from typing import Tuple, Union, List
from aiocsv import AsyncReader

from config import load_config
from common.aiopool import AioTaskPool
from common.schemas import *
from common.exceptions import *


class FileManager:
    def __init__(self, dir_name=None):
        if dir_name is None:
            dir_name = load_config(read_envs=True)['path']['data']
        if dir_name is None:
            raise ParameterError('No data storage path is set. '
                                 'Set the value of the key "path.data" in configuration file. '
                                 'Alternatively, set the value of environment variable "LAP_PATH_DATA"')
        self.image_dir = os.path.join(dir_name, 'images')
        self.file_dir = os.path.join(dir_name, 'files')
        self.csv_fields = ['url']

    def create_all(self, drop=False):
        for target_dir in [self.image_dir, self.file_dir]:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            elif drop:
                shutil.rmtree(target_dir)
                os.makedirs(target_dir)

    def drop_all(self, create=False):
        for target_dir in [self.image_dir, self.file_dir]:
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
                image_dir = os.path.join(self.image_dir, image_hash[:2])
                os.makedirs(image_dir, exist_ok=True)
                image_file = os.path.join(image_dir, image_hash)
                if not os.path.exists(image_file):
                    async with aiofiles.open(image_file, 'wb') as f:
                        await f.write(image_data)

                pil_image = PIL.Image.open(io.BytesIO(image_data))
                return True, ImageCreate(hash=image_hash, width=pil_image.width, height=pil_image.height,
                                         url=image_url, path=image_file)
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

    def get_image_file_path(self, image_hash: str) -> str:
        if not all(c in string.hexdigits for c in image_hash):
            raise ParameterValueError(key='hash', value=image_hash, should='hex string')

        image_path = os.path.join(self.image_dir, image_hash[:2], image_hash)
        if os.path.exists(image_path):
            return image_path
        raise ParameterNotFoundError(image_hash)
