from db.tables import *

from sqlalchemy.orm import relationship
Base = mapper_registry.generate_base()


class File(Base):
    __table__ = file_table
    images = relationship("Image", back_populates="file", cascade="delete")

    def __repr__(self):
        return f'File(id={self.id!r}, name={self.name!r})'

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in ['id', 'created_at', 'name', 'size'] and k in self.__table__.columns.keys():
                setattr(self, k, v)


class Image(Base):
    __table__ = image_table
    file = relationship("File", back_populates="images")
    bboxes = relationship("BBox", back_populates="image", cascade="delete")

    def __repr__(self):
        return f'Image(id={self.id!r}, hash={self.hash!r}, width={self.width!r}, height={self.height!r})'

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in ['id', 'file_id'] and k in self.__table__.columns.keys():
                setattr(self, k, v)


class BBox(Base):
    __table__ = bbox_table
    image = relationship("Image", back_populates="bboxes")
    label = relationship("Label", back_populates="bbox", uselist=False, cascade="delete", lazy="selectin")

    def __repr__(self):
        return f'BBox(id={self.id!r}, image={self.image_id!r} bbox={self.rx1, self.ry1, self.rx2, self.ry2})'


class Label(Base):
    __table__ = label_table
    bbox = relationship("BBox", back_populates="label", lazy="noload")

    def column_keys(self):
        return self.__table__.columns.keys()
