from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator


class AssetBase(BaseModel):
    name: str
    version: str
    url: str
    created_at: int
    experiment_tracker: str

    @validator('created_at', pre=True)
    def convert_datetime_to_timestamp(cls, value):
        if isinstance(value, datetime):
            return int(value.timestamp())
        return value


class AssetRead(AssetBase):
    status: Optional[str]
    project: Optional[str]
    model: str
