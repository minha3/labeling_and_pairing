import os
import aiofiles
import pickle
import yaml
from typing import List, Optional

from config import CONFIG
from common.exceptions import ParameterError

from app.image.utils import get_image_file_path
from app.bbox.models import BBox
from app.label.utils import label_types, label_names_by_type, translate


def get_export_dir():
    return os.path.join(CONFIG['path']['data'], 'exports')


def group_bboxes_by_image(bboxes: List[BBox]) -> List[dict]:
    images = {}
    for bbox in bboxes:
        if bbox.image.id not in images:
            images[bbox.image.id] = {'image': bbox.image, 'bboxes': [bbox]}
        else:
            images[bbox.image.id]['bboxes'].append(bbox)
    return list(images.values())


async def export_to_yolo(dirname: str, bboxes: List[BBox]) -> Optional[str]:
    images = group_bboxes_by_image(bboxes)
    if len(images) < 2:
        raise ParameterError('Count of reviewed labels should be at least 2 to export.')

    root_dir = os.path.join(get_export_dir(), dirname)
    os.makedirs(root_dir, exist_ok=True)
    cnt_train = max(1, int(len(images) * 0.7))
    idx_range = {'train': range(0, cnt_train), 'val': range(cnt_train, len(images))}

    labels_ = {l: i for i, l in enumerate(sorted(label_names_by_type('region')))}
    config = {'path': dirname, 'train': None, 'val': None, 'test': '',
              'nc': len(labels_), 'names': {v: k for k, v in labels_.items()}}

    for usage in ['train', 'val']:
        bbox_dir = os.path.join(root_dir, 'labels', usage)
        rel_image_dir = os.path.join('images', usage)
        image_dir = os.path.join(root_dir, rel_image_dir)
        label_dir = os.path.join(root_dir, 'annotations', usage)
        os.makedirs(bbox_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(label_dir, exist_ok=True)
        config[usage] = rel_image_dir

        labels = []
        for i in idx_range[usage]:
            image = images[i]['image']
            origin_image_path = get_image_file_path(image.hash)
            rel_origin_image_path = get_image_file_path(image.hash, return_relative=True)
            target_image_path = os.path.join(image_dir, rel_origin_image_path)
            os.makedirs(os.path.dirname(target_image_path), exist_ok=True)
            os.symlink(origin_image_path, target_image_path)

            target_bbox_path = os.path.join(bbox_dir, rel_origin_image_path).replace('.jpg', '.txt')
            os.makedirs(os.path.dirname(target_bbox_path), exist_ok=True)
            async with aiofiles.open(target_bbox_path, 'w') as f:
                for bbox in images[i]['bboxes']:
                    width, height = image.width, image.height
                    bwidth, bheight = bbox.rx2 - bbox.rx1, bbox.ry2 - bbox.ry1
                    await f.write(
                        f'{labels_[bbox.label.region]} {bwidth / 2 + bbox.rx1} {bheight / 2 + bbox.ry1} '
                        f'{bwidth} {bheight}\n')

                    label_data = {'path': os.path.join(rel_image_dir, rel_origin_image_path),
                                  'width': width,
                                  'height': height,
                                  'bbox': [int(width * bbox.rx1), int(height * bbox.ry1),
                                           int(width * bbox.rx2), int(height * bbox.ry2)]}
                    for label_type in bbox.label.column_keys():
                        if label_type in label_types():
                            label_name = getattr(bbox.label, label_type)
                            label_data[translate(label_type)] = translate(label_name, label_type)

                    labels.append(label_data)

        with open(os.path.join(label_dir, 'annotations.pickle'), 'wb') as f:
            pickle.dump(labels, f)

    with open(os.path.join(root_dir, 'configuration.yml'), 'w') as f:
        yaml.safe_dump(config, f)

    return root_dir
