from db.tables import *
from label import label_types, custom_label

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
    regions = relationship("Region", back_populates="image", cascade="delete")

    def __repr__(self):
        return f'Image(id={self.id!r}, hash={self.hash!r}, width={self.width!r}, height={self.height!r})'

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in ['id', 'file_id'] and k in self.__table__.columns.keys():
                setattr(self, k, v)


class Region(Base):
    __table__ = region_table
    image = relationship("Image", back_populates="regions")

    def __repr__(self):
        return f'Region(id={self.id!r}, image={self.image_id!r} bbox={self.rx1, self.ry1, self.rx2, self.ry2})'

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in ['id', 'image_id', 'rx1', 'rx2', 'ry1', 'ry2'] and k in self.__table__.columns.keys():
                setattr(self, k, v)
            elif k == 'labels':
                self._clear_labels()
                for _k, _v in v.items():
                    if _k in self.__table__.columns.keys():
                        setattr(self, _k, _v)

    def label_to_dict(self):
        labels = {label_type: getattr(self, label_type) for label_type in label_types()}
        labels['custom'] = custom_label(self)
        setattr(self, 'labels', labels)
        return self

    def _clear_labels(self):
        for label_type in label_types():
            setattr(self, label_type, None)
