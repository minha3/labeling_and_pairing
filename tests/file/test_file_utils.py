import unittest
import os
import shutil
import time
import io

from fastapi import UploadFile

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_utils')
os.environ['LAP_PATH_DATA'] = DATA_DIR

from common.exceptions import (ParameterEmptyError, ParameterExistError,
                               ParameterValueError, ParameterNotFoundError)
from app.file.utils import (get_file_dirpath, save_file, remove_file,
                            urls_from_file, download_images)


class TestFileUtil(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.non_image_url = 'https://google.com'
        # Set a valid image url to test some test cases
        self.image_url = ''

    def tearDown(self) -> None:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)

    @staticmethod
    def get_faked_file(csv_field=None, content=None):
        os.makedirs(get_file_dirpath(), exist_ok=True)
        file_name = 'faked.csv'
        with open(os.path.join(get_file_dirpath(), file_name), 'w') as f:
            if csv_field:
                f.write(f'{csv_field}\n')
            else:
                f.write('url\n')
            if content:
                f.write(f'{content}\n')
            else:
                f.write('this is faked file\n')
        return file_name

    @staticmethod
    def get_faked_uploadfile(name, content):
        return UploadFile(filename=name, file=io.BytesIO(content))

    async def test_save_file(self):
        file_name, content = 'non_empty_file.csv', b'file content'
        _, file_path = await save_file(self.get_faked_uploadfile(file_name, content))
        self.assertTrue(os.path.exists(file_path))

    async def test_save_empty_file(self):
        file_name, content = 'empty_file.csv', b''
        with self.assertRaises(ParameterEmptyError):
            await save_file(self.get_faked_uploadfile(file_name, content))

    async def test_save_duplicate_file(self):
        file_name, content = 'non_empty_file.csv', b'file content'
        await save_file(self.get_faked_uploadfile(file_name, content))

        with self.assertRaises(ParameterExistError):
            await save_file(self.get_faked_uploadfile(file_name, content))

    async def test_remove_file(self):
        file_name = self.get_faked_file()
        await remove_file(file_name)
        self.assertFalse(os.path.exists(os.path.join(get_file_dirpath(), file_name)))

    async def test_read_image_urls_from_file(self):
        file_name = self.get_faked_file(content=self.non_image_url)

        status, content = await urls_from_file(file_name)
        self.assertTrue(status)
        self.assertEqual(1, len(content))

    async def test_read_image_urls_from_file_with_invalid_csv_field(self):
        file_name = self.get_faked_file(csv_field='invalid,fields')

        with self.assertRaises(ParameterValueError):
            await urls_from_file(file_name)

    async def test_read_image_urls_from_file_with_invalid_csv_field_silently(self):
        file_name = self.get_faked_file(csv_field='invalid,fields')

        status, content = await urls_from_file(file_name, silent=True)
        self.assertFalse(status)

    async def test_read_image_urls_from_non_existent_file(self):
        file_name = 'non_exist_file.csv'

        self.assertFalse(os.path.exists(os.path.join(get_file_dirpath(), file_name)))
        with self.assertRaises(ParameterNotFoundError):
            await urls_from_file('non_exist_file.csv')

    async def test_download_images_from_url(self):
        self.assertTrue(len(self.image_url) > 0,
                        msg='you should add a valid image url to the variable "valid_image_url"')

        r = await download_images([self.image_url])
        self.assertEqual(1, len(r))

    async def test_download_images_from_non_existent_url(self):
        image_url = f'http://non-existent.image.url/{int(time.time())}'

        r = await download_images([image_url])
        self.assertEqual(0, len(r))

    async def test_download_images_from_non_image_url(self):
        r = await download_images([self.non_image_url])
        self.assertEqual(0, len(r))
