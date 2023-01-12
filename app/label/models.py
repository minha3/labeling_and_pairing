from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm


from database.core import Base


class Label(Base):
    __tablename__ = 'label'
    id = sa.Column(sa.Integer, primary_key=True)
    bbox_id = sa.Column(sa.ForeignKey('bbox.id', ondelete="CASCADE"))
    region = sa.Column(sa.String(128), nullable=True, comment='label type')
    style = sa.Column(sa.String(128), nullable=True, comment='label type')
    category = sa.Column(sa.String(128), nullable=True, comment='label type')
    fabric = sa.Column(sa.String(128), nullable=True, comment='label type')
    print = sa.Column(sa.String(128), nullable=True, comment='label type')
    detail = sa.Column(sa.String(128), nullable=True, comment='label type')
    color = sa.Column(sa.String(128), nullable=True, comment='label type')
    center_back_length = sa.Column(sa.String(128), nullable=True, comment='label type')
    sleeve_length = sa.Column(sa.String(128), nullable=True, comment='label type')
    neckline = sa.Column(sa.String(128), nullable=True, comment='label type')
    fit = sa.Column(sa.String(128), nullable=True, comment='label type')
    collar = sa.Column(sa.String(128), nullable=True, comment='label type')
    unused = sa.Column(sa.BOOLEAN, nullable=False, default=False, server_default=sa.false(),
                       comment='Whether the label is unused')
    updated_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed = sa.Column(sa.BOOLEAN, nullable=False, default=False, server_default=sa.false(),
                         comment='Whether review is done')
    bbox = orm.relationship("BBox", back_populates="label", lazy="noload")

    # required in order to access columns with server defaults
    # or SQL expression defaults, subsequent to a flush, without
    # triggering an expired load
    __mapper_args__ = {"eager_defaults": True}

    @property
    def _columns_exclude_updating(self):
        return ['id', 'bbox_id']
