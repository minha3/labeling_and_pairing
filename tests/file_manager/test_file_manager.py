import os
import shutil
import time
import yaml
import dataclasses
import unittest
from string import ascii_lowercase
from random import choice

from common.exceptions import *
from file_manager import FileManager
from label import load_labels


class TestFileManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.my_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(self.my_dir,
                                     ''.join(choice(ascii_lowercase) for _ in range(8)))
        self.file_manager = FileManager(data_dir=self.data_dir)
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

    def get_valid_image_hash(self) -> str:
        hash_ = '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32'
        hash_path = self.file_manager.get_image_file_path(hash_, not_exist_ok=True)
        os.makedirs(os.path.dirname(hash_path))

        with open(hash_path, 'w') as f:
            f.write('temporary file')
        return hash_

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
        self.file_manager.create_all()

        hash_ = '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32'
        hash_dir = os.path.join(self.file_manager.image_dir, hash_[:2])
        os.makedirs(hash_dir)
        hash_path = os.path.join(hash_dir, f'{hash_}.jpg')

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

    async def test_export_images_to_yolo_format(self):
        load_labels()
        self.file_manager.create_all()
        hash_ = self.get_valid_image_hash()

        @dataclasses.dataclass
        class Label:
            region: str

            @staticmethod
            def column_keys():
                return ['region']

        @dataclasses.dataclass
        class Region:
            rx1: float
            ry1: float
            rx2: float
            ry2: float
            label: Label

        @dataclasses.dataclass
        class Image:
            hash: str
            width: int
            height: int
            bboxes: list

        label = Label(region='top')
        region1 = Region(rx1=0.1, ry1=0.1, rx2=0.3, ry2=0.3, label=label)
        region2 = Region(rx1=0.4, ry1=0.4, rx2=0.7, ry2=0.7, label=label)
        image = Image(hash=hash_, width=600, height=600, bboxes=[region1, region2])

        dirpath = await self.file_manager.export_to_yolo('test_export_yolo', [image, image])
        files = []
        for root, dirs, files_ in os.walk(dirpath):
            for f in files_:
                files.append(os.path.join(root, f))

        self.assertEqual(7, len(files),
                         msg='yolo dataset should have one configuration file, two image file, two bbox file and two label file')
        self.assertEqual(1, len([o for o in files if o.endswith('.yml')]),
                         msg='yolo dataset should have configuration file to refer to label information')
        self.assertEqual(2, len([o for o in files if o.endswith('.txt')]),
                         msg='one bbox file should be created for each image')
        self.assertEqual(2, len([o for o in files if o.endswith('.jpg')]),
                         msg='one image file should be created for each image')
        self.assertEqual(2, len([o for o in files if o.endswith('.pickle')]),
                         msg='one label file should be created')

        config_file = [o for o in files if o.endswith('.yml')][0]
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        self.assertTrue('nc' in config, msg='configuration file should have number of label names')
        self.assertEqual(int, type(config['nc']), msg='type of number of label names should be integer')
        self.assertTrue('names' in config, msg='configuration file should have list of label names')

        annotation_file = [o for o in files if o.endswith('.txt')][0]
        with open(annotation_file, 'r') as f:
            for l in f:
                tokens = l.strip().split(' ')
                self.assertEqual(5, len(tokens), msg='each annotation should consist of five elements')
                self.assertTrue(tokens[0].isdigit(), msg='1st element of annotation should be index of label name')
                self.assertTrue(0.0 <= float(tokens[1]) <= 1.0, msg='2nd element of annotation should be the ratio of '
                                                                    'center x coordinate value to the width of image')
                self.assertTrue(0.0 <= float(tokens[2]) <= 1.0, msg='3rd element of annotation should be he ratio of '
                                                                    'center y coordinate value to the height of image')
                self.assertTrue(0.0 <= float(tokens[3]) <= 1.0, msg='4th element of annotation should be the ratio of '
                                                                    'width of bounding box to the width of image')
                self.assertTrue(0.0 <= float(tokens[4]) <= 1.0, msg='5th element of annotation should be the ratio of '
                                                                    'height of bounding box to the height of image')
