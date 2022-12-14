__all__ = ['load_labels', 'label_types', 'label_names_by_type', 'label_types_by_region', 'translate', 'custom_label']
from .label import Label

LABEL = Label()


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


def custom_label(cls: object) -> str:
    return LABEL.custom_label(cls)
