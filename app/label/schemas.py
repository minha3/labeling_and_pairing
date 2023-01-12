from typing import Optional, List

from pydantic import BaseModel


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


class LabelRead(LabelBase):
    id: int
    bbox_id: int
    unused: bool
    reviewed: bool

    class Config:
        orm_mode = True


class LabelUpdate(LabelBase):
    id: int
    region: Optional[str]
    unused: Optional[bool]
    reviewed: Optional[bool]


class LabelFilter(BaseModel):
    region: Optional[List[str]]
    style: Optional[List[str]]
    category: Optional[List[str]]
    fabric: Optional[List[str]]
    print: Optional[List[str]]
    detail: Optional[List[str]]
    color: Optional[List[str]]
    center_back_length: Optional[List[str]]
    sleeve_length: Optional[List[str]]
    neckline: Optional[List[str]]
    fit: Optional[List[str]]
    collar: Optional[List[str]]
    unused: Optional[bool]
    reviewed: Optional[bool]
