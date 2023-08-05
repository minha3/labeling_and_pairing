from typing import Optional

from app.model_registry.schemas import AssetBase, AssetRead


class ServeCreate(AssetBase):
    asset: AssetRead
    host: str
    port: int
    number_of_gpu: int = 0
