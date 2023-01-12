from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from database.core import Base


class File(Base):
    __tablename__ = 'file'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255), unique=True, nullable=False)
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
    size = sa.Column(sa.Integer, nullable=False, comment='Bytes')
    cnt_url = sa.Column(sa.Integer, nullable=True,
                        comment='Number of image urls in the file')
    cnt_image = sa.Column(sa.Integer, nullable=True,
                          comment='Number of image files successfully downloaded from total image urls')
    cnt_bbox = sa.Column(sa.Integer, nullable=True,
                         comment='Number of bboxes extracted by the inference model from total images')
    cnt_download_failure = sa.Column(sa.Integer, nullable=True)
    cnt_duplicated_image = sa.Column(sa.Integer, nullable=True)
    error = sa.Column(sa.Text, nullable=True, comment='Why failed to read the file')
    images = orm.relationship("Image", back_populates="file", cascade="delete")

    def __repr__(self):
        return f'File(id={self.id!r}, name={self.name!r})'

    @property
    def _columns_exclude_updating(self):
        return ['id', 'created_at', 'name', 'size']
