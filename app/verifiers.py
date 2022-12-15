from typing import List
from fastapi import UploadFile, File, HTTPException, Query

from label import label_types, label_names_by_type


def verify_csv_file(file: UploadFile = File(...)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail=f"Content type of file should be 'text/csv', not {file.content_type!r}")


def verify_filter(filters: List[str] = Query([])):
    _filters = {}
    for i, _filter in enumerate(filters):
        if '=' not in _filter or len(_filter.split('=')) != 2:
            raise HTTPException(status_code=400, detail=f"query string format of `filters[{i}]` should be {{label_type}}={{label_name}}")

        label_type, label_name = _filter.split('=')
        if label_type not in label_types():
            raise HTTPException(status_code=400, detail=f"{label_type!r} is invalid for label type")
        if label_name not in label_names_by_type(label_type):
            raise HTTPException(status_code=400, detail=f"{label_name!r} is invalid for {label_type!r}")

        if label_type not in _filters:
            _filters[label_type] = [label_name]
        else:
            _filters[label_type].append(label_name)
    return _filters
