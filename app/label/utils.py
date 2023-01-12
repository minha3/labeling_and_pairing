__all__ = ['load_labels', 'label_types', 'label_names_by_type',
           'label_types_by_region', 'translate', 'custom_label',
           'verify_label_filter']

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

    def verify_label_filter(self, filters: List[str] = Query([])) -> Optional[LabelFilter]:
        if not filters:
            return
        parsed = defaultdict(list)
        for i, filter_ in enumerate(filters):
            if '=' not in filter_ or len(filter_.split('=')) != 2:
                raise HTTPException(status_code=400,
                                    detail=f'query string format of filters[{i}] should be "key=value"')

            key, value = filter_.split('=')
            if key not in LabelFilter.schema()['properties']:
                raise HTTPException(status_code=400, detail=f'Invalid value for filters[{i}]: "{key}"')
            elif key in self.label_types() and value not in self.label_names_by_type(key):
                raise HTTPException(status_code=400, detail=f'Invalid value for {key}: "{value}"')
            elif LabelFilter.schema()['properties'][key]['type'] == 'array':
                parsed[key].append(value)
            else:
                parsed[key] = value

        return LabelFilter(**parsed)


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
