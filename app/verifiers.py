from typing import List, Optional
from collections import defaultdict
from fastapi import UploadFile, File, HTTPException, Query

from label import label_types, label_names_by_type
from common import schemas


def verify_csv_file(file: UploadFile = File(...)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail=f"Content type of file should be 'text/csv', not {file.content_type!r}")


def verify_label_filter(filters: List[str] = Query([])) -> Optional[schemas.LabelFilter]:
    if not filters:
        return
    parsed = defaultdict(list)
    for i, filter_ in enumerate(filters):
        if '=' not in filter_ or len(filter_.split('=')) != 2:
            raise HTTPException(status_code=400, detail=f'query string format of filters[{i}] should be "key=value"')

        key, value = filter_.split('=')
        if key not in schemas.LabelFilter.schema()['properties']:
            raise HTTPException(status_code=400, detail=f'Invalid value for filters[{i}]: "{key}"')
        elif key in label_types() and value not in label_names_by_type(key):
            raise HTTPException(status_code=400, detail=f'Invalid value for {key}: "{value}"')
        elif schemas.LabelFilter.schema()['properties'][key]['type'] == 'array':
            parsed[key].append(value)
        else:
            parsed[key] = value

    return schemas.LabelFilter(**parsed)
