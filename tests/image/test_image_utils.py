import unittest
import os
import shutil

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_utils')
os.environ['LAP_PATH_DATA'] = DATA_DIR

from common.exceptions import ParameterValueError, ParameterNotFoundError
from app.image.utils import get_image_dirpath, get_image_file_path


class TestImageUtil(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)

    def test_get_image_file_path_from_hash(self):
        hash_ = '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32'
        hash_dir = os.path.join(get_image_dirpath(), hash_[:2])
        os.makedirs(hash_dir)
        hash_path = os.path.join(hash_dir, f'{hash_}.jpg')

        with open(hash_path, 'w') as f:
            f.write('temporary file')

        r = get_image_file_path(hash_)
        self.assertEqual(hash_path, r)

    async def test_get_image_file_path_from_invalid_hash(self):
        with self.assertRaises(ParameterValueError):
            get_image_file_path('this is not a hex string')

    async def test_get_image_file_path_from_non_existent_hash(self):
        hash_ = '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32'
        with self.assertRaises(ParameterNotFoundError):
            get_image_file_path(hash_)
