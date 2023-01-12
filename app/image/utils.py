import string
import os

from config import CONFIG
from common.exceptions import ParameterValueError, ParameterNotFoundError


def get_image_dirpath() -> str:
    return os.path.join(CONFIG['path']['data'], 'images')


def get_image_file_path(image_hash: str, not_exist_ok=False, return_relative=False) -> str:
    if not all(c in string.hexdigits for c in image_hash):
        raise ParameterValueError(key='hash', value=image_hash, should='hex string')

    relative_path = os.path.join(image_hash[:2], f'{image_hash}.jpg')
    full_path = os.path.join(get_image_dirpath(), relative_path)
    if not not_exist_ok and not os.path.exists(full_path):
        raise ParameterNotFoundError(image_hash)

    if return_relative:
        return relative_path
    else:
        return full_path
