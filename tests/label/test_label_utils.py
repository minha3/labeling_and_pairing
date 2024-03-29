import os
import unittest

from fastapi import HTTPException

from app.label.utils import *
from app.label.schemas import LabelFilter

from ..factories import LabelFactory


class TestLabelUtil(unittest.TestCase):
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

    def test_verify_label_filter(self):
        self.assertEqual(LabelFilter(region=['top', 'bottom']),
                         verify_label_filter(filters=['region=top', 'region=bottom']))

    def test_verify_label_filter_with_invalid_format(self):
        self.assert_http_400(verify_label_filter, filters=['foo', 'bar'])

    def test_verify_label_filter_with_invalid_key(self):
        self.assert_http_400(verify_label_filter, filters=['invalid_label_type=top'])

    def test_verify_label_filter_with_invalid_value(self):
        self.assert_http_400(verify_label_filter, filters=['region=invalid_label_name'])

    def test_verify_label_filter_with_empty(self):
        self.assertEqual(None, verify_label_filter([]))

    def test_verify_label_sort(self):
        self.assertEqual(
            [{'field': 'region', 'direction': 'asc'},
             {'field': 'fabric', 'direction': 'desc'}],
            verify_label_sort('region,-fabric')
        )

    def test_verify_label_sort_with_invalid_value(self):
        self.assert_http_400(verify_label_sort, 'foo,-bar')

    def test_label_statistics(self):
        labels = []
        for region, category, fabric in [
            ('top', 'top', 'padded'),
            ('bottom', 'skirt', 'padded'),
            ('bottom', 'pants', 'jersey'),
        ]:
            labels.append(LabelFactory.build(region=region, category=category, fabric=fabric))

        self.assertEqual({'region': {'top': 1, 'bottom': 2, 'outer': 0, 'dress': 0},
                          'category': {'pants': 1, 'dress': 0, 'skirt': 1, 'top': 1, 'down_jacket': 0},
                          'fabric': {'padded': 2, 'jersey': 1},
                          'sleeve_length': {'long_sleeve': 0, 'short_sleeve': 0}},
                         label_statistics(labels))

    def assert_http_400(self, func, *args, **kwargs):
        with self.assertRaises(HTTPException) as e:
            func(*args, **kwargs)

        self.assertEqual(400, e.exception.status_code)


if __name__ == '__main__':
    unittest.main()
