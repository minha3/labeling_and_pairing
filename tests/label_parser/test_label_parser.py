import os
import unittest

from label import *


class TestLabelParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_labels(os.path.dirname(os.path.realpath(__file__)))

    def test_label_types(self):
        self.assertEqual({'region', 'category', 'sleeve_length', 'fabric'}, set(label_types()),
                         msg='Label type means a set of labels of the same attributes.'
                             'So Label type is a layer having "labels" in a lower layer.')

    def test_label_names_by_type(self):
        self.assertEqual({'top', 'bottom', 'outer', 'dress'}, set(label_names_by_type('region')),
                         msg='It should return "region.labels"')
        self.assertEqual({'top', 'pants', 'skirt', 'dress', 'down_jacket'}, set(label_names_by_type('category')),
                         msg='It should return "category.labels"')

    def test_label_types_included_in_region(self):
        self.assertTrue('sleeve_length' in label_types_by_region('top'),
                        msg='"top" is in "sleeve_length.regions"')

    def test_label_types_not_included_in_region(self):
        self.assertTrue('sleeve_length' not in label_types_by_region('bottom'),
                        msg='"bottom" is not in "sleeve_length.regions"')

    def test_translate_ko_to_en(self):
        self.assertEqual('bottom', translate('하의'))

    def test_translate_ko_to_multiple_en(self):
        self.assertEqual({'down_jacket', 'padded'}, set(translate('패딩')))

    def test_translate_ko_to_en_with_label_type(self):
        self.assertEqual('down_jacket', translate('패딩', '카테고리'))
        self.assertEqual('padded', translate('패딩', '소재'))

    def test_extract_custom_label_from_region_entity(self):
        class MockRegion:
            def __init__(self, category, fabric):
                self.category = category
                self.fabric = fabric
        region = MockRegion(category='top', fabric='jersey')
        self.assertEqual('sweetshirt', custom_label(region))


if __name__ == '__main__':
    unittest.main()
