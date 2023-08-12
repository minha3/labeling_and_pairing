from fastapi import APIRouter, Response

from app.model_registry.schemas import AssetRead
from .service import serve, stop


router = APIRouter()


@router.post('')
async def register_model(asset: AssetRead):
    await serve(asset)
    return Response(status_code=201)


@router.delete('')
async def unregister_model(asset: AssetRead):
    await stop(model=asset.model,
               version=asset.version,
               project=asset.project)
    return Response(status_code=204)
