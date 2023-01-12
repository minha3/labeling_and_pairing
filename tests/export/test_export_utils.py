import unittest
import os
import yaml
import shutil

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_service')
os.environ['LAP_PATH_DATA'] = DATA_DIR

from app.image.utils import get_image_file_path
from app.export.utils import export_to_yolo
from ..factories import ImageFactory, LabelFactory, BBoxFactory


class TestExportService(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)

    def fake_image_file(self, hash_=None) -> str:
        if hash_ is None:
            hash_ = '6dc982440b8174cdf7f6251637c3f8d7acd32d2cc606746d5b1495ba86a34e32'
        hash_path = get_image_file_path(hash_, not_exist_ok=True)
        os.makedirs(os.path.dirname(hash_path))

        with open(hash_path, 'w') as f:
            f.write('temporary file')
        return hash_

    async def test_export_images_to_yolo_format(self):
        def fake_bbox():
            image = ImageFactory.build()
            self.fake_image_file(hash_=image.hash)
            label = LabelFactory.build()
            bbox = BBoxFactory.build()
            bbox.image_id, bbox.image, bbox.label = image.id, image, label
            return bbox

        bbox1 = fake_bbox()
        bbox2 = fake_bbox()

        dirpath = await export_to_yolo('test_export_yolo', [bbox1, bbox2])
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