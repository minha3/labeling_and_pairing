from fastapi import APIRouter

from app.model_registry.service import download
from app.model_registry.schemas import AssetRead

from .service import serve, is_uploaded


router = APIRouter()


@router.post('')
async def serve_model(asset: AssetRead, host: str, port: int, number_of_gpu: int = 0):
    if not await is_uploaded(name=asset.name,
                             version=asset.version,
                             model=asset.model,
                             project=asset.project,
                             host=host):
        asset_content = await download(experiment_tracker=asset.experiment_tracker,
                                       url=asset.url)
    else:
        asset_content = None

    await serve(content=asset_content,
                name=asset.name,
                version=asset.version,
                model=asset.model,
                project=asset.project,
                host=host,
                port=port,
                number_of_gpu=number_of_gpu)
