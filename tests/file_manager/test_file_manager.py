import os
import shutil
import time
import unittest
from string import ascii_lowercase
from random import choice

from common.exceptions import *
from file_manager import FileManager


class TestFileManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.my_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(self.my_dir,
                                     ''.join(choice(ascii_lowercase) for _ in range(8)))
        self.file_manager = FileManager(dir_name=self.data_dir)
        # Set a valid image url to test some test cases
        self.valid_image_url = ''

    def tearDown(self) -> None:
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def get_invalid_fields_csv_file(self) -> str:
        file_name = 'invalid_fields.csv'
        with open(os.path.join(self.file_manager.file_dir, file_name), 'w') as f:
            f.write('this,is,invalid,fields,test\n')
        return file_name

    def get_valid_csv_file(self) -> str:
        file_name = 'valid_image_urls.csv'
        with open(os.path.join(self.file_manager.file_dir, file_name), 'w') as f:
            f.write('url\n')
            f.write(f'{self.valid_image_url}')
        return file_name

    def test_create_image_directory(self):
        self.assertFalse(os.path.exists(self.file_manager.image_dir),
                         msg='image directory should be missing before calling create_all()')
        self.file_manager.create_all()
        self.assertTrue(os.path.exists(self.file_manager.image_dir),
                        msg='image directory should be created after calling create_all()')

    def test_create_file_directory(self):
        self.assertFalse(os.path.exists(self.file_manager.file_dir),
                         msg='file directory should be missing before calling create_all()')
        self.file_manager.create_all()
        self.assertTrue(os.path.exists(self.file_manager.file_dir),
                        msg='file directory should be exist after calling create_all()')

    def test_drop_image_directory(self):
        self.file_manager.create_all()
        self.assertTrue(os.path.exists(self.file_manager.image_dir),
                        msg='image directory should be exist after calling create_all()')
        self.file_manager.drop_all()
        self.assertFalse(os.path.exists(self.file_manager.image_dir),
                         msg='image directory should be missing after calling drop_all()')

    def test_drop_file_directory(self):
        self.file_manager.create_all()
        self.assertTrue(os.path.exists(self.file_manager.file_dir),
                        msg='file directory should be exist after calling create_all()')
        self.file_manager.drop_all()
        self.assertFalse(os.path.exists(self.file_manager.file_dir),
                         msg='file directory should be missing after calling drop_all()')

    def test_create_directory_with_no_drop(self):
        self.assertFalse(os.path.exists(self.file_manager.file_dir),
                         msg='file directory should be missing before calling create_all()')

        os.makedirs(self.file_manager.file_dir)
        temp_file = os.path.join(self.file_manager.file_dir, 'temp.txt')
        with open(temp_file, 'w') as f:
            f.write('test')
        self.file_manager.create_all(drop=False)

        self.assertTrue(os.path.exists(temp_file),
                        msg='The file that was already made should still exist')

    def test_create_directory_with_drop(self):
        self.assertFalse(os.path.exists(self.file_manager.file_dir),
                         msg='file directory should be missing before calling create_all()')

        os.makedirs(self.file_manager.file_dir)
        temp_file = os.path.join(self.file_manager.file_dir, 'temp.txt')
        with open(temp_file, 'w') as f:
            f.write('test')
        self.file_manager.create_all(drop=True)

        self.assertFalse(os.path.exists(temp_file),
                         msg='The file that was already made should be removed')

    async def test_save_file(self):
        file_name, content = 'non_empty_file.csv', b'file content'
        self.file_manager.create_all()
        await self.file_manager.save_file(file_name, content)

        self.assertTrue(os.path.exists(os.path.join(self.file_manager.file_dir, file_name)))

    async def test_save_empty_file(self):
        file_name, content = 'empty_file.csv', b''
        self.file_manager.create_all()
        with self.assertRaises(ParameterEmptyError):
            await self.file_manager.save_file(file_name, content)

    async def test_save_duplicate_file(self):
        file_name, content = 'non_empty_file.csv', b'file content'
        self.file_manager.create_all()
        await self.file_manager.save_file(file_name, content)

        with self.assertRaises(ParameterExistError):
            await self.file_manager.save_file(file_name, content)

    async def test_remove_file(self):
        file_name, content = 'non_empty_file.csv', b'file content'
        self.file_manager.create_all()
        await self.file_manager.save_file(file_name, content)
        self.assertTrue(os.path.exists(os.path.join(self.file_manager.file_dir, file_name)))

        await self.file_manager.remove_file(file_name)
        self.assertFalse(os.path.exists(os.path.join(self.file_manager.file_dir, file_name)))

    async def test_read_image_urls_from_file(self):
        self.file_manager.create_all()
        file_name = self.get_valid_csv_file()

        status, content = await self.file_manager.urls_from_file(file_name)
        self.assertTrue(status)
        self.assertEqual(1, len(content))

    async def test_read_image_urls_from_file_with_invalid_csv_field(self):
        self.file_manager.create_all()
        file_name = self.get_invalid_fields_csv_file()

        with self.assertRaises(ParameterValueError):
            await self.file_manager.urls_from_file(file_name)

    async def test_read_image_urls_from_file_with_invalid_csv_field_silently(self):
        self.file_manager.create_all()
        file_name = self.get_invalid_fields_csv_file()

        status, content = await self.file_manager.urls_from_file(file_name, silent=True)
        self.assertFalse(status)

    async def test_read_image_urls_from_non_existent_file(self):
        self.file_manager.create_all()
        file_name = 'non_exist_file.csv'

        self.assertFalse(os.path.exists(os.path.join(self.file_manager.file_dir, file_name)))
        with self.assertRaises(ParameterNotFoundError):
            await self.file_manager.urls_from_file('non_exist_file.csv')

    async def test_download_images_from_url(self):
        self.assertTrue(len(self.valid_image_url) > 0,
                        msg='you should add a valid image url to the variable "valid_image_url"')
        self.file_manager.create_all()

        r = await self.file_manager.download_images([self.valid_image_url])
        self.assertEqual(1, len(r))

    async def test_download_images_from_non_existent_url(self):
        image_url = f'http://non-existent.image.url/{int(time.time())}'

        self.file_manager.create_all()

        r = await self.file_manager.download_images([image_url])
        self.assertEqual(0, len(r))

    async def test_download_images_from_non_image_url(self):
        image_url = 'https://www.google.com/'

        self.file_manager.create_all()

        r = await self.file_manager.download_images([image_url])
        self.assertEqual(0, len(r))

    def test_get_image_file_path_from_hash(self):
        hash_ = '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32'
        hash_dir = os.path.join(self.file_manager.image_dir, hash_[:2])
        os.makedirs(hash_dir)
        hash_path = os.path.join(hash_dir, hash_)

        self.file_manager.create_all()
        with open(hash_path, 'w') as f:
            f.write('temporary file')

        r = self.file_manager.get_image_file_path(hash_)

        self.assertEqual(hash_path, r)

    async def test_get_image_file_path_from_invalid_hash(self):
        with self.assertRaises(ParameterValueError):
            self.file_manager.get_image_file_path('this is not a hex string')

    async def test_get_image_file_path_from_non_existent_hash(self):
        hash_ = '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32'
        with self.assertRaises(ParameterNotFoundError):
            self.file_manager.get_image_file_path(hash_)
