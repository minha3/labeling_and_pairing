import sqlalchemy as sa
from sqlalchemy import orm


from database.core import Base


class Image(Base):
    __tablename__ = 'image'
    id = sa.Column(sa.Integer, primary_key=True)
    file_id = sa.Column(sa.ForeignKey('file.id', ondelete="CASCADE"))
    hash = sa.Column(sa.String(64), unique=True, nullable=False,
                     comment='Hex string to be used as an image identifier')
    width = sa.Column(sa.Integer, nullable=False)
    height = sa.Column(sa.Integer, nullable=False)
    url = sa.Column(sa.String(255), nullable=False)
    file = orm.relationship("File", back_populates="images")
    bboxes = orm.relationship("BBox", back_populates="image", cascade="delete")

    def __repr__(self):
        return f'Image(id={self.id!r}, hash={self.hash!r}, width={self.width!r}, height={self.height!r})'

    @property
    def _columns_exclude_updating(self):
        return ['id', 'file_id', 'hash', 'width', 'height']
