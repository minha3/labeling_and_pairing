from abc import ABC, abstractmethod
from typing import List

import aiohttp

from .schemas import ModelRead


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
    async def get_models(self) -> List[ModelRead]:
        pass


class CometApi(ExperimentTrackerApi):
    @property
    def required_configs(self):
        return ['api_key', 'workspace', 'project']

    async def get_models(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=(f"https://comet.com/api/rest/v2/registry-model/details"
                     f"?workspaceName={self._config['workspace']}"
                     f"&modelName={self._config['project']}"),
                headers={'Authorization': self._config['api_key']}
            ) as response:
                if response.status != 200:
                    return []
                data = await response.json()
        models = []
        for model in data['versions']:
            models.append(ModelRead(
                experiment_tracker='comet',
                name=model['experimentModel']['modelName'],
                version=model['version'],
                created_at=str(model['createdAt']),
                status=model['status'],
                download_url=model['restApiUrl'],
            ))
        return models
