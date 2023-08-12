from config import CONFIG
from app.model_registry.service import download
from app.model_registry.schemas import AssetRead
from .utils import *


def upload_path(filename, model, version, project=None):
    _, file_extension = os.path.splitext(filename)
    return f'serving/{project or model}_{version}{file_extension}'


async def serve(asset: AssetRead):
    asset_path = upload_path(asset.filename, asset.model, asset.version, project=asset.project)

    async with serve_cls(asset.model)(config=CONFIG['inference_server']) as api:
        if await api.path_exists(asset_path, expanduser=True):
            content = None
        else:
            content = await download(experiment_tracker=asset.experiment_tracker, url=asset.url)

        serialized_path = await api.upload(content=content, path=asset_path, expanduser=True)

        await api.serve(model=asset.project or asset.model,
                        version=asset.version,
                        serialized_file=serialized_path)


async def stop(model, version, project=None):
    async with serve_cls(model)(config=CONFIG['inference_server']) as api:
        await api.stop(model=project or model,
                       version=version)
