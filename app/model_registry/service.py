from config import CONFIG
from common.exceptions import ParameterValueError
from .utils import *


async def get_all():
    result = []
    for name, config in CONFIG['experiment_tracker'].items():
        if tracker_cls := experiment_trackers.get(name):
            tracker = tracker_cls(config=config)
            result.extend(await tracker.get_models())
    return result


async def download(experiment_tracker, url):
    if experiment_tracker not in experiment_trackers:
        raise ParameterValueError(key='experiment_tracker',
                                  value=experiment_tracker,
                                  choice=list(experiment_trackers.keys()))
    tracker_config = CONFIG['experiment_tracker'][experiment_tracker]
    tracker_cls = experiment_trackers[experiment_tracker]
    tracker = tracker_cls(config=tracker_config)
    return await tracker.download(url=url)
