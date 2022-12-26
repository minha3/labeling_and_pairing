from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text, DateTime, REAL, BOOLEAN, true, false
from sqlalchemy.orm import registry


mapper_registry = registry()
metadata = mapper_registry.metadata


image_table = Table('image', metadata,
                    Column('id', Integer, primary_key=True),
                    Column('file_id', ForeignKey('file.id', ondelete="CASCADE")),
                    Column('hash', String(64), unique=True, nullable=False,
                           comment='Hex string to be used as an image identifier'),
                    Column('width', Integer, nullable=False),
                    Column('height', Integer, nullable=False),
                    Column('url', String(255), nullable=False))

file_table = Table('file', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('name', String(255), unique=True, nullable=False),
                   Column('created_at', DateTime, nullable=False, default=datetime.utcnow),
                   Column('size', Integer, nullable=True, comment='Bytes'),
                   Column('cnt_url', Integer, nullable=True,
                          comment='Number of image urls in the file'),
                   Column('cnt_image', Integer, nullable=True,
                          comment='Number of image files successfully downloaded from total image urls'),
                   Column('cnt_region', Integer, nullable=True,
                          comment='Number of regions extracted by the inference model from total images'),
                   Column('cnt_download_failure', Integer, nullable=True),
                   Column('cnt_duplicated_image', Integer, nullable=True),
                   Column('error', Text, nullable=True, comment='Why failed to read the file'))

# Label type columns should be equal to label types defined in the lap_labels.yml file
region_table = Table('region', metadata,
                     Column('id', Integer, primary_key=True),
                     Column('image_id', ForeignKey('image.id', ondelete="CASCADE")),
                     Column('rx1', REAL, nullable=False, comment='Relative x-coordinate of topleft point'),
                     Column('ry1', REAL, nullable=False, comment='Relative y-coordinate of topleft point'),
                     Column('rx2', REAL, nullable=False, comment='Relative x-coordinate of bottomright point'),
                     Column('ry2', REAL, nullable=False, comment='Relative y-coordinate of bottomright point'),
                     Column('region', String(128), nullable=True, comment='label type'),
                     Column('style', String(128), nullable=True, comment='label type'),
                     Column('category', String(128), nullable=True, comment='label type'),
                     Column('fabric', String(128), nullable=True, comment='label type'),
                     Column('print', String(128), nullable=True, comment='label type'),
                     Column('detail', String(128), nullable=True, comment='label type'),
                     Column('color', String(128), nullable=True, comment='label type'),
                     Column('center_back_length', String(128), nullable=True, comment='label type'),
                     Column('sleeve_length', String(128), nullable=True, comment='label type'),
                     Column('neckline', String(128), nullable=True, comment='label type'),
                     Column('fit', String(128), nullable=True, comment='label type'),
                     Column('collar', String(128), nullable=True, comment='label type'),
                     Column('use', BOOLEAN, nullable=False, default=True, server_default=true(), comment='Whether the region is used for labeling'),
                     Column('updated_at', DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
                     Column('reviewed', BOOLEAN, nullable=False, default=False, server_default=false(), comment='Whether review is done'),
                     )

# Label columns should be equal to the labels of label type "region" defined in the lap_labels.yml file
pair_table = Table('pair', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('top', Integer, nullable=True, comment='label of label type "region"'),
                   Column('bottom', Integer, nullable=True, comment='label of label type "region"'),
                   Column('outer', Integer, nullable=True, comment='label of label type "region"'),
                   Column('dress', Integer, nullable=True, comment='label of label type "region"'))
