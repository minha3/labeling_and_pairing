from config import CONFIG
from common.exceptions import ParameterValueError

from .utils import *


def serve_cls(model):
    if model.lower().startswith('yolo'):
        return YoloServeApi
    else:
        return TorchServeApi


def get_config(host):
    config = next((o for o in CONFIG['inference'] if o['host'] == host), None)
    if config is None:
        raise ParameterValueError(
            key='host',
            value=host,
            choice=[o['host'] for o in CONFIG['inference']]
        )
    return config


def upload_path(name, version, project=None, model=None):
    if not project and not model:
        raise ParameterKeyError('Either project or model')
    return f'serving/{project or model}/{version}/{name}'


async def serve(content, name, version, model, project, host, port, number_of_gpu):
    config = get_config(host)
    asset_path = upload_path(name, version, model=model, project=project)

    async with serve_cls(model)(config=config) as api:
        if content:
            await api.upload(content=content, path=asset_path, expanduser=True)

        await api.serve(name=project or model,
                        model=model,
                        version=version,
                        port=port,
                        number_of_gpu=number_of_gpu,
                        serialized_file=asset_path)


async def is_uploaded(name, version, model, project, host):
    config = get_config(host)
    async with SSHClient(config) as client:
        return await client.path_exists(upload_path(name, version, model=model, project=project))
