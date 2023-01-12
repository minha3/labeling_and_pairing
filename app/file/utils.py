import hashlib
import imghdr
import os
import io
from typing import Tuple, Union, List
from urllib.parse import urlparse

import aiofiles
import aiofiles.os
import aiohttp
import PIL.Image
from aiocsv import AsyncReader
from fastapi import UploadFile, File, HTTPException

from config import CONFIG
from common.exceptions import ParameterEmptyError, ParameterExistError, \
    ParameterNotFoundError, ParameterValueError
from common.aiopool import AioTaskPool
from app.image.schemas import ImageBase
from app.image.utils import get_image_file_path

from .schemas import FileCreate


def verify_csv_file(file: UploadFile = File(...)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400,
                            detail=f'Content type of file should be "text/csv", not "{file.content_type}"')
    return file


def verify_url(url: str):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def verify_image_file(filename, content=None):
    return imghdr.what(filename, content) is not None


def get_file_dirpath() -> str:
    return os.path.join(CONFIG['path']['data'], 'files')


async def save_file(name, content) -> Tuple[FileCreate, str]:
    if not content:
        raise ParameterEmptyError(name)
    file_dir = get_file_dirpath()
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, name)
    if os.path.exists(file_path):
        raise ParameterExistError(name)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    return FileCreate(name=name, size=os.path.getsize(file_path)), file_path


async def remove_file(name: str) -> None:
    file_dir = get_file_dirpath()
    file_path = os.path.join(file_dir, name)
    if os.path.exists(file_path):
        await aiofiles.os.remove(file_path)


async def urls_from_file(name: str, silent: bool = False) -> Tuple[bool, Union[str, List[str]]]:
    file_dir = get_file_dirpath()
    file_path = os.path.join(file_dir, name)
    csv_fields = ['url']
    urls = []
    try:
        if not os.path.exists(file_path):
            raise ParameterNotFoundError(file_path)

        async with aiofiles.open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = AsyncReader(f)
            fields = await reader.__anext__()
            if fields == csv_fields:
                async for row in reader:
                    if verify_url(row[0]):
                        urls.append(row[0])
            else:
                raise ParameterValueError(key='First line of csv file', value=','.join(fields),
                                          should=','.join(csv_fields))
        return True, urls
    except StopAsyncIteration:
        raise ParameterEmptyError(file_path)
    except Exception as e:
        if silent:
            return False, str(e)
        else:
            raise e


async def download_images(image_urls: List[str]) -> List[ImageBase]:
    async with aiohttp.ClientSession() as session:
        async with AioTaskPool(tasks=10) as pool:
            for url in image_urls:
                pool.apply(_download_image_task(session, url))
            images = await pool.wait()

    return [o[1] for o in images if type(o) == tuple and o[0]]


async def _download_image_task(session, image_url) -> Tuple[bool, Union[str, ImageBase]]:
    async with session.get(image_url) as response:
        if response.status != 200:
            return False, f'url: {image_url}. response: {response.status}'
        if response.content_length == 0:
            return False, f'url: {image_url}. content-length: 0'

        image_data = await response.read()
        if len(image_data) == 0:
            return False, f'url: {image_url}. data-length: 0'

        if not verify_image_file(None, image_data):
            return False, f'url: {image_url}. failed to determine image type'

        try:
            image_hash = hashlib.sha256(image_data).hexdigest()
            image_file = get_image_file_path(image_hash, not_exist_ok=True)
            image_dir = os.path.dirname(image_file)
            os.makedirs(image_dir, exist_ok=True)
            if not os.path.exists(image_file):
                async with aiofiles.open(image_file, 'wb') as f:
                    await f.write(image_data)

            pil_image = PIL.Image.open(io.BytesIO(image_data))
            return True, ImageBase(hash=image_hash, width=pil_image.width, height=pil_image.height,
                                   url=image_url)
        except Exception as e:
            return False, str(e)


