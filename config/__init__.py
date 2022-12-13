__all__ = ['load_config']

from .loader import load


def load_config(dirname: str = None, read_envs: bool = True) -> dict:
    return load('lap_config.yml', dirname, read_envs=read_envs)
