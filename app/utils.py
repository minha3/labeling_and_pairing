import os
import shutil

from config import CONFIG

file_dir = os.path.join(CONFIG['path']['data'], 'files')
image_dir = os.path.join(CONFIG['path']['data'], 'images')
export_dir = os.path.join(CONFIG['path']['data'], 'exports')


def create_directories(drop=False):
    for target_dir in [file_dir, image_dir, export_dir]:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        elif drop:
            shutil.rmtree(target_dir)
            os.makedirs(target_dir)
