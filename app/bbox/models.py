import sqlalchemy as sa
from sqlalchemy import orm


from database.core import Base


class BBox(Base):
    __tablename__ = 'bbox'
    id = sa.Column(sa.Integer, primary_key=True)
    image_id = sa.Column(sa.ForeignKey('image.id', ondelete="CASCADE"))
    rx1 = sa.Column(sa.REAL, nullable=False, comment='Relative x-coordinate of topleft point')
    ry1 = sa.Column(sa.REAL, nullable=False, comment='Relative y-coordinate of topleft point')
    rx2 = sa.Column(sa.REAL, nullable=False, comment='Relative x-coordinate of bottomright point')
    ry2 = sa.Column(sa.REAL, nullable=False, comment='Relative y-coordinate of bottomright point')
    image = orm.relationship("Image", back_populates="bboxes")
    label = orm.relationship("Label", back_populates="bbox", uselist=False, cascade="delete", lazy="selectin")

    def __repr__(self):
        return f'BBox(id={self.id!r}, image={self.image_id!r} bbox={self.rx1, self.ry1, self.rx2, self.ry2})'

    @property
    def _columns_exclude_updating(self):
        return ['id', 'image_id', 'rx1', 'ry1', 'rx2', 'ry2']