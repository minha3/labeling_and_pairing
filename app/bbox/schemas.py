from typing import Optional, List

from pydantic import BaseModel

from app.label.schemas import LabelRead


class BBoxBase(BaseModel):
    rx1: float
    ry1: float
    rx2: float
    ry2: float


class BBoxCreate(BBoxBase):
    image_id: int


class BBoxRead(BBoxBase):
    id: int
    image_id: int
    label: Optional[LabelRead]

    class Config:
        orm_mode = True


class BBoxPaginated(BaseModel):
    items: List[BBoxRead]
    total: int
    page: int
    items_per_page: int


class BBoxUpdate(BBoxBase):
    id: int
