__all__ = ['load_labels', 'label_types', 'label_names_by_type',
           'label_types_by_region', 'translate', 'custom_label',
           'verify_label_filter', 'verify_label_sort']

import os
import yaml
from typing import List, Optional
from collections import defaultdict

from fastapi import Query, HTTPException

from .schemas import LabelFilter


class LabelUtil:
    def __init__(self):
        self._translator = {}
        self._label_types = []
        self._label_types_by_region = {}
        self._labels = {}

    def load_labels(self, label_dir=None):
        if label_dir is None:
            label_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(label_dir, 'lap_labels.yml'), 'r') as f:
            self._labels = yaml.load(f, Loader=yaml.FullLoader)

        self._set_translator()
        self._set_label_types()

    def _set_translator(self):
        self._translator = {}

        def update_translator(_k, _v):
            if _k in self._translator:
                if type(self._translator[_k]) == str:
                    self._translator[_k] = [self._translator[_k], _v]
                else:
                    self._translator[_k].append(_v)
            else:
                self._translator[_k] = _v

        for k, v in self._labels.items():
            if type(v['ko']) == dict:
                for _k, _v in v['ko'].items():
                    update_translator(_v, k)
                    """
                    top:
                      ko:
                       region: 상의
                       category: 탑
                    in the above case, in order to translate (top, region) to 상의
                    and translate (top, category) to 탑
                    """
                    self._translator[(k, _k)] = _v
            else:
                update_translator(v['ko'], k)
                self._translator[k] = v['ko']

    def _set_label_types(self):
        self._label_types = [k for k, v in self._labels.items() if 'labels' in v]
        self._label_types_by_region = {}

        for region_label in self._labels['region']['labels']:
            self._label_types_by_region[region_label] = []
            for label_type in self._label_types:
                if region_label in self._labels[label_type].get('regions', []):
                    self._label_types_by_region[region_label].append(label_type)

    def label_types(self) -> List[str]:
        return self._label_types

    def translate(self, v, v_type=None) -> Optional[str]:
        r = None
        if v_type:
            r = self._translator.get((v, v_type))
        if r is None:
            r = self._translator.get(v)
            r_type = self._translator.get(v_type)
            if type(r) == list and r_type and r_type in self._labels:
                for _r in r:
                    if _r in self._labels[r_type]['labels']:
                        return _r
        return r

    def label_names_by_type(self, label_type) -> List[Optional[str]]:
        if label_type in self._label_types:
            return self._labels[label_type]['labels']
        else:
            return []

    def label_types_by_region(self, region) -> List[str]:
        return self._label_types_by_region.get(region, [])

    def custom_label(self, o):
        for label, condition in self._labels['custom']['condition'].items():
            if eval(condition):
                return label
        return None

    def verify_label_parameter(self, label_type: str, label_name: Optional[str] = None) -> bool:
        if label_type not in LabelFilter.schema()['properties']:
            raise HTTPException(status_code=400, detail=f'Invalid value for field name of label: "{label_type}"')
        elif label_name and label_name not in self.label_names_by_type(label_type):
            raise HTTPException(status_code=400, detail=f'Invalid value for {label_type}: "{label_name}"')

        return True

    def verify_label_filter(self, filters: List[str]) -> Optional[LabelFilter]:
        """
        Validate and parse the filter strings to construct a `LabelFilter`
        :param filters: Each filter should be in the format "label_type=label_name".
                        If a label_type supports multi label names,
                        multiple "label_type=label_name" can be provided
                        for each label_name.

        :return: None if input list of filters is empty.
                 Otherwise, `LabelFilter` object

        :raises: 1.`HTTPException` with status code 400 if the format is incorrect
                    or label_type is invalid
                    or label_name is invalid.
        """
        if not filters:
            return
        parsed = defaultdict(list)
        for i, filter_ in enumerate(filters):
            if '=' not in filter_ or len(filter_.split('=')) != 2:
                raise HTTPException(status_code=400,
                                    detail=f'query string format of filters[{i}] should be "key=value"')

            label_type, label_name = filter_.split('=')
            self.verify_label_parameter(label_type, label_name)
            if LabelFilter.schema()['properties'][label_type]['type'] == 'array':
                parsed[label_type].append(label_name)
            else:
                parsed[label_type] = label_name

        return LabelFilter(**parsed)

    def verify_label_sort(self, sort_by: Optional[str]) -> Optional[List[dict]]:
        """
        Convert the `sort_by` query parameter into a list of `spec` objects that define the
         order of the results.

        :param sort_by: should be in the format `label_type,-label_type`, where each field name is
            a column in the database model.
            `label_type` means the results should be sorted by label_type in ascending order.
            `-label_type` means the results should be sorted by label_type in descending order.

        :return: list of `spec`.
                 The `spec` object has the following properties:
                    `field`: the name of column in the model
                    `direction`: either "asc" or "desc" to indicate the sort direction

        :raises: 1.`HTTPException` with status code 400 if the format is incorrect
                    or label_type is invalid
                    or label_name is invalid.

        :example:
            Input: sort_by="region,-fabric"
            Output: [{'field': 'region', 'direction': 'asc'},
                     {'field': 'fabric', 'direction': 'desc'}]
        """

        if sort_by is None:
            return None

        spec = []
        for label_type in sort_by.split(','):
            direction = 'asc'
            if label_type.startswith('-'):
                direction = 'desc'
                label_type = label_type[1:]

            self.verify_label_parameter(label_type)
            spec.append({'field': label_type, 'direction': direction})

        return spec


LABEL = LabelUtil()


def load_labels(dir_name: str = None):
    LABEL.load_labels(dir_name)


def label_types() -> list:
    return LABEL.label_types()


def label_names_by_type(label_type: str = None) -> list:
    return LABEL.label_names_by_type(label_type)


def label_types_by_region(region: str) -> list:
    return LABEL.label_types_by_region(region)


def translate(v: str, v_type: str = None) -> str:
    return LABEL.translate(v, v_type)


def verify_label_filter(filters: List[str] = Query([])) -> Optional[LabelFilter]:
    return LABEL.verify_label_filter(filters)


def custom_label(cls: object) -> str:
    return LABEL.custom_label(cls)


def verify_label_sort(sort_by: Optional[str] = Query(None)) -> Optional[List[dict]]:
    return LABEL.verify_label_sort(sort_by)
