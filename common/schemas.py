# reference: https://fastapi.tiangolo.com/tutorial/sql-databases/?h=orm_mode#use-pydantics-orm_mode
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageBase(BaseModel):
    hash: str
    width: int
    height: int
    url: str
    path: Optional[str]


class ImageCreate(ImageBase):
    pass


class Image(ImageBase):
    id: int

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
    cnt_region: Optional[int]
    cnt_download_failure: Optional[int]
    cnt_duplicated_image: Optional[int]
    error: Optional[str]

    class Config:
        orm_mode = True


class RegionBase(BaseModel):
    image_id: int
    rx1: float
    ry1: float
    rx2: float
    ry2: float
    labels: dict


class RegionCreate(RegionBase):
    pass


class Region(RegionBase):
    id: int
    use: bool

    class Config:
        orm_mode = True
