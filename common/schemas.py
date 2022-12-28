# reference: https://fastapi.tiangolo.com/tutorial/sql-databases/?h=orm_mode#use-pydantics-orm_mode
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageBase(BaseModel):
    hash: str
    width: int
    height: int
    url: str


class ImageCreate(ImageBase):
    pass


class Image(ImageBase):
    id: int
    file_id: int

    class Config:
        orm_mode = True


class FileBase(BaseModel):
    name: str
    size: int


class FileCreate(FileBase):
    pass


class File(FileBase):
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


class LabelBase(BaseModel):
    region: str
    style: Optional[str]
    category: Optional[str]
    fabric: Optional[str]
    print: Optional[str]
    detail: Optional[str]
    color: Optional[str]
    center_back_length: Optional[str]
    sleeve_length: Optional[str]
    neckline: Optional[str]
    fit: Optional[str]
    collar: Optional[str]


class LabelCreate(LabelBase):
    bbox_id: int


class Label(LabelBase):
    id: int
    bbox_id: int
    unused: bool
    reviewed: bool

    class Config:
        orm_mode = True


class BBoxBase(BaseModel):
    rx1: float
    ry1: float
    rx2: float
    ry2: float


class BBoxCreate(BBoxBase):
    image_id: int


class BBox(BBoxBase):
    id: int
    image_id: int
    label: Optional[Label]

    class Config:
        orm_mode = True
