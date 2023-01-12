from pydantic import BaseModel


class ImageBase(BaseModel):
    hash: str
    width: int
    height: int
    url: str


class ImageCreate(ImageBase):
    file_id: int


class ImageRead(ImageBase):
    id: int
    file_id: int

    class Config:
        orm_mode = True
