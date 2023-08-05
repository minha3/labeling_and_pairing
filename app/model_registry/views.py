from typing import List

from fastapi import APIRouter

from .schemas import AssetRead
from .service import get_all


router = APIRouter()


@router.get('', response_model=List[AssetRead])
async def get_models():
    return await get_all()
