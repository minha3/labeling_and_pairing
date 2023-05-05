from config import CONFIG
from .utils import *


async def get_all():
    result = []
    for name, config in CONFIG['experiment_tracker'].items():
        if tracker_cls := eval(config['cls']):
            tracker = tracker_cls(config=config)
            result.extend(await tracker.get_models())
    return result
