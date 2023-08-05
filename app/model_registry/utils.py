__all__ = ['experiment_trackers']

import os
from abc import ABC, abstractmethod
from typing import List

import aiohttp

from .schemas import AssetRead

CHUNK_SIZE = 1024 * 1024 * 5


class ExperimentTrackerApi(ABC):
    def __init__(self, config: dict):
        missing_configs = set(self.required_configs) - set(config.keys())
        if missing_configs:
            raise KeyError(f'Missing required configuration parameters: {missing_configs}')
        self._config = config

    @property
    def required_configs(self):
        return []

    @abstractmethod
    async def get_models(self) -> List[AssetRead]:
        pass

    @abstractmethod
    async def download(self, url) -> bytearray:
        pass


class CometApi(ExperimentTrackerApi):
    @property
    def required_configs(self):
        return ['api_key', 'workspace', 'project']

    @property
    def request_headers(self):
        return {'Authorization': self._config['api_key']}

    @property
    def _model_extensions(self):
        return ['.pt']

    async def get_models(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=(f"https://comet.com/api/rest/v2/registry-model/details"
                     f"?workspaceName={self._config['workspace']}"
                     f"&modelName={self._config['project']}"),
                headers=self.request_headers
            ) as response:
                if response.status != 200:
                    return []
                data = await response.json()
        models = []
        for version in data['versions']:
            for asset in version['assets']:
                _, extension = os.path.splitext(asset['fileName'])
                if extension in self._model_extensions:
                    models.append(AssetRead(
                        experiment_tracker='comet',
                        name=asset['fileName'],
                        version=version['version'],
                        url=(f'https://www.comet.com'
                             f'/api/rest/v2/experiment/asset/get-asset'
                             f"?experimentKey={asset['experimentKey']}"
                             f"&assetId={asset['assetId']}"),
                        created_at=str(asset['createdAt']),
                        status=version['status'],
                        model=version['experimentModel']['modelName'],
                        project=data['modelName']))
        return models

    async def download(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=url,
                headers=self.request_headers
            ) as response:
                if response.status != 200:
                    return
                content = bytearray()
                while chunk := await response.content.read(CHUNK_SIZE):
                    content.extend(chunk)
                return content


experiment_trackers = {
    'comet': CometApi
}
