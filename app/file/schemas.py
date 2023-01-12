from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class FileBase(BaseModel):
    name: str
    size: int


class FileCreate(FileBase):
    pass


class FileRead(FileBase):
    id: int
    created_at: datetime
    cnt_url: Optional[int]
    cnt_image: Optional[int]
    cnt_bbox: Optional[int]
    cnt_download_failure: Optional[int]
    cnt_duplicated_image: Optional[int]
    error: Optional[str]

    class Config:
        orm_mode = True


class FileUpdate(BaseModel):
    id: int
    cnt_url: Optional[int]
    cnt_image: Optional[int]
    cnt_bbox: Optional[int]
    cnt_download_failure: Optional[int]
    cnt_duplicated_image: Optional[int]
    error: Optional[str]
