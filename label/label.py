import os
import yaml


class Label:
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

    def label_types(self):
        return self._label_types

    def translate(self, v, v_type=None):
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

    def label_names_by_type(self, label_type=None):
        if label_type is None:
            r = {}
            for l_type in self._label_types:
                r[l_type] = self._labels[l_type]['labels']
            return r
        elif label_type in self._label_types:
            return self._labels[label_type]['labels']
        else:
            return []

    def label_types_by_region(self, region):
        result = {}
        if region is None:
            label_types = self._label_types
        else:
            label_types = self._label_types_by_region.get(region, [])
        for k in label_types:
            result[k] = self.label_names_by_type(k)
        return result

    def custom_label(self, o):
        for label, condition in self._labels['custom']['condition'].items():
            if eval(condition):
                return label
        return None
