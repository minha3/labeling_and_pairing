from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import registry


mapper_registry = registry()
metadata = mapper_registry.metadata


image_table = sa.Table('image', metadata,
                       sa.Column('id', sa.Integer, primary_key=True),
                       sa.Column('file_id', sa.ForeignKey('file.id', ondelete="CASCADE")),
                       sa.Column('hash', sa.String(64), unique=True, nullable=False,
                                 comment='Hex string to be used as an image identifier'),
                       sa.Column('width', sa.Integer, nullable=False),
                       sa.Column('height', sa.Integer, nullable=False),
                       sa.Column('url', sa.String(255), nullable=False))

file_table = sa.Table('file', metadata,
                      sa.Column('id', sa.Integer, primary_key=True),
                      sa.Column('name', sa.String(255), unique=True, nullable=False),
                      sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
                      sa.Column('size', sa.Integer, nullable=True, comment='Bytes'),
                      sa.Column('cnt_url', sa.Integer, nullable=True,
                                comment='Number of image urls in the file'),
                      sa.Column('cnt_image', sa.Integer, nullable=True,
                                comment='Number of image files successfully downloaded from total image urls'),
                      sa.Column('cnt_bbox', sa.Integer, nullable=True,
                                comment='Number of bboxes extracted by the inference model from total images'),
                      sa.Column('cnt_download_failure', sa.Integer, nullable=True),
                      sa.Column('cnt_duplicated_image', sa.Integer, nullable=True),
                      sa.Column('error', sa.Text, nullable=True, comment='Why failed to read the file'))

bbox_table = sa.Table('bbox', metadata,
                      sa.Column('id', sa.Integer, primary_key=True),
                      sa.Column('image_id', sa.ForeignKey('image.id', ondelete="CASCADE")),
                      sa.Column('rx1', sa.REAL, nullable=False, comment='Relative x-coordinate of topleft point'),
                      sa.Column('ry1', sa.REAL, nullable=False, comment='Relative y-coordinate of topleft point'),
                      sa.Column('rx2', sa.REAL, nullable=False, comment='Relative x-coordinate of bottomright point'),
                      sa.Column('ry2', sa.REAL, nullable=False, comment='Relative y-coordinate of bottomright point'),
                      )

# Label type columns should be equal to label types defined in the lap_labels.yml file
label_table = sa.Table('label', metadata,
                       sa.Column('id', sa.Integer, primary_key=True),
                       sa.Column('bbox_id', sa.ForeignKey('bbox.id', ondelete="CASCADE")),
                       sa.Column('region', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('style', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('category', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('fabric', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('print', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('detail', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('color', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('center_back_length', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('sleeve_length', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('neckline', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('fit', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('collar', sa.String(128), nullable=True, comment='label type'),
                       sa.Column('unused', sa.BOOLEAN, nullable=False, default=False, server_default=sa.false(),
                                 comment='Whether the label is unused'),
                       sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
                       sa.Column('reviewed', sa.BOOLEAN, nullable=False, default=False, server_default=sa.false(),
                                 comment='Whether review is done'),
                       )
