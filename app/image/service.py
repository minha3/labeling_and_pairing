from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import ParameterNotFoundError

from .models import Image
from .schemas import ImageBase


async def get_all(session: AsyncSession, file_id: int) -> List[Image]:
    return [o for o in (await session.scalars(select(Image).where(Image.file_id == file_id)))]


async def get_one(session: AsyncSession, image_id: int, silent=False) -> Optional[Image]:
    r = await session.get(Image, image_id)
    if r is None and not silent:
        raise ParameterNotFoundError(f'Image {image_id}')
    return r


async def insert(session: AsyncSession, images: List[ImageBase], file_id: int) -> List[Image]:
    result = []
    cnt_dup = 0
    for image in images:
        db_image = await session.scalar(select(Image).where(Image.hash == image.hash))
        if db_image is None:
            db_image = Image(hash=image.hash, width=image.width, height=image.height, url=image.url,
                             file_id=file_id)
            result.append(db_image)
            session.add(db_image)
        else:
            cnt_dup += 1
    await session.commit()
    return result
