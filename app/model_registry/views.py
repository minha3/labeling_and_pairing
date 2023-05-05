from typing import List

from fastapi import APIRouter

from .schemas import ModelRead
from .service import get_all


router = APIRouter()


@router.get('', response_model=List[ModelRead])
async def get_models():
    return await get_all()
