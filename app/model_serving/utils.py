import os
from abc import ABC, abstractmethod
from string import Template

import asyncssh

from common.exceptions import ParameterKeyError, OperationError

CHUNK_SIZE = 1024 * 1024 * 5


def serve_cls(model):
    if model.lower().startswith('yolo'):
        return YoloServeApi
    else:
        return TorchServeApi


class SSHClient:
    """
    Example:
    >>> config = {'host': '123.456.7.8', 'username': 'name', 'client_key_path': '~/.ssh/pem'}
    >>> async with SSHClient(config) as client:
    >>>    await client.path_exists(path='rel_path/for/example', expanduser=True)
    True
    """
    def __init__(self, config: dict):
        missing_configs = set(self.required_configs) - set(config.keys())
        if missing_configs:
            raise ParameterKeyError(missing_configs)
        self._config = config
        self._conn = None

    @property
    def required_configs(self):
        return ['host', 'username', 'client_key_path']

    async def __aenter__(self):
        self._conn = await asyncssh.connect(
            self._config['host'],
            username=self._config['username'],
            client_keys=[self._config['client_key_path']]
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()
        await self._conn.wait_closed()
        return False

    async def path_exists(self, path, expanduser=False):
        if expanduser:
            result = await self._conn.run('echo $HOME')
            if result.exit_status != 0:
                print(result.stderr, end='')
                return
            home_path = result.stdout.strip()
            path = os.path.join(home_path, path)

        result = await self._conn.run(f'ls {path}')
        if result.exit_status == 0:
            return True
        return False

    async def upload(self, content, path, expanduser=False):
        if expanduser:
            result = await self._conn.run('echo $HOME')
            if result.exit_status != 0:
                print(result.stderr, end='')
                raise OperationError(f"Failed to upload model to inference server {self._config['host']}."
                                     f"reason={result.stderr}")
            home_path = result.stdout.strip()
            path = f'{home_path}/{path}'

        result = await self._conn.run(f'ls {path}')
        if result.exit_status == 0:
            return

        result = await self._conn.run(f'mkdir -p {os.path.dirname(path)}')
        if result.exit_status != 0:
            print(result.stderr, end='')
            raise OperationError(f"Failed to upload model to inference server {self._config['host']}."
                                 f"reason={result.stderr}")

        async with self._conn.start_sftp_client() as sftp:
            try:
                async with sftp.open(path, 'wb') as f:
                    for i in range(0, len(content), CHUNK_SIZE):
                        await f.write(content[i:i + CHUNK_SIZE])
            except Exception as e:
                await sftp.remove(path)
                print(e)
                raise OperationError(f"Failed to upload model to inference server {self._config['host']}."
                                     f"reason={e}")
        return True


class ServeApi(SSHClient, ABC):

    @abstractmethod
    async def serve(self, model, version, serialized_file):
        pass

    @abstractmethod
    async def stop(self, model, version):
        pass


class TorchServeApi(ServeApi):
    @property
    def required_configs(self):
        return ['host', 'username', 'client_key_path', 'number_of_gpu',
                'inference_port', 'management_port',
                'grpc_inference_port', 'grpc_management_port']

    def _ts_handler(self, model):
        """
        Handler can be TorchServe's inbuilt handler name
        or path to a py file to handle custom TorchServe inference logic.
        :return:
        """
        raise NotImplementedError

    async def archive(self, model, version, serialized_file):
        """
        Reference: https://github.com/pytorch/serve/tree/3a7187cf9b5a405e0a725654790afe24564b03dd/model-archiver#torch-model-archiver-command-line-interface
        Run torch-model-archiver CLI to make a .mar file
        :param model: A valid model name must begin with a letter of the alphabet
                      and can only contain letters, digits, underscores `_`, dashes `-` and periods `.`.
        :param version: Model's version
        :param serialized_file: A serialized file (.pt or .pth) should be a checkpoint in case of torchscript
                                and state_dict in case of eager mode.
        :return:
        """
        result = await self._conn.run('command -v torch-model-archiver')
        if result.exit_status != 0:
            raise OperationError(f"Failed to archive model on inference server {self._config['host']}."
                                 f"reason=torch-model-archiver is not installed on inference server")

        ts_handler = self._ts_handler(model)
        serialized_dir = os.path.dirname(serialized_file)
        archive_path = f'{serialized_dir}/{model}_{version}.mar'

        result = await self._conn.run(f'ls {archive_path}')
        if result.exit_status == 0:
            return archive_path

        # upload custom handler file to serving dir
        if ts_handler.endswith('.py') and os.path.exists(ts_handler):
            ts_handler_file = os.path.basename(ts_handler)
            async with self._conn.start_sftp_client() as sftp:
                try:
                    await sftp.put(
                        ts_handler,
                        f'{serialized_dir}/{ts_handler_file}'
                    )
                except Exception as e:
                    print(e)
                    raise OperationError(f"Failed to archive model on inference server {self._config['host']}."
                                         f"reason={e}")
            handler = f'{serialized_dir}/{ts_handler_file}'
        else:
            handler = ts_handler

        # archive
        result = await self._conn.run(
            f'/usr/local/bin/torch-model-archiver'
            f' --force'
            f' --model-name {model}'
            f' --version {version}'
            f' --serialized-file {serialized_file}'
            f' --handler {handler}'
            f' --export-path {serialized_dir}'
        )
        if result.exit_status != 0:
            print(result.stderr, end='')
            raise OperationError(f"Failed to archive model on inference server {self._config['host']}."
                                 f"reason={result.stderr}")

        temp_archive_path = f'{serialized_dir}/{model}.mar'

        # append version to archived file
        if self.path_exists(temp_archive_path):
            result = await self._conn.run(f'mv {temp_archive_path} {archive_path}')
            if result.exit_status != 0:
                print(result.stderr, end='')
                raise OperationError(f"Failed to archive model on inference server {self._config['host']}."
                                     f"reason={result.stderr}")

        return archive_path

    async def serve(self, model, version, serialized_file):
        result = await self._conn.run('command -v torchserve')
        if result.exit_status != 0:
            raise OperationError(f"Failed to serve model on inference server {self._config['host']}."
                                 f"reason=torchserve is not installed on inference server")

        archived = await self.archive(model=model,
                                      version=version,
                                      serialized_file=serialized_file)

        archived_dir = os.path.dirname(archived)

        with open(f'{os.path.dirname(os.path.realpath(__file__))}/torchserve.properties', 'r') as f:
            content = f.read()
        config_template = Template(content)
        config_content = config_template.substitute(
            number_of_gpu=self._config['number_of_gpu'],
            inference_port=self._config['inference_port'],
            management_port=self._config['management_port'],
            grpc_inference_port=self._config['grpc_inference_port'],
            grpc_management_port=self._config['grpc_management_port'],
        )
        config_path = f'{archived_dir}/torchserve.properties'
        async with self._conn.start_sftp_client() as sftp:
            try:
                async with sftp.open(config_path, 'w') as f:
                    await f.write(config_content)
            except Exception as e:
                await sftp.remove(config_path)
                print(e)
                raise OperationError(f"Failed to serve model on inference server {self._config['host']}."
                                     f"reason={e}")

        result = await self._conn.run('torchserve --stop')
        if result.exit_status != 0:
            print(result.stderr, end='')
            raise OperationError(f"Failed to serve model on inference server {self._config['host']}."
                                 f"reason={result.stderr}")

        result = await self._conn.run(
            f'torchserve --start'
            f' --model-store {os.path.dirname(archived)}'
            f' --models {archived}'
            f' --ts-config {config_path}'
            f' > {os.path.dirname(archived)}/serve.log 2>&1 &'
        )
        print(result.stdout, end='')
        print(result.stderr, end='')

    async def stop(self, model, version):
        result = await self._conn.run('torchserve --stop')
        if result.exit_status != 0:
            print(result.stderr, end='')
            raise OperationError(f"Failed to serve model on inference server {self._config['host']}."
                                 f"reason={result.stderr}")


class YoloServeApi(TorchServeApi):
    async def upload(self, content, path, expanduser=False):
        await super().upload(content, path, expanduser)
        return await self.export_to_onnx(path)

    async def export_to_onnx(self, path):
        onnx_path = f'{os.path.splitext(path)[0]}.onnx'

        result = await self._conn.run(f'ls {onnx_path}')
        if result.exit_status == 0:
            return onnx_path

        result = await self._conn.run(f'/usr/local/bin/yolo export'
                                      f' model={path} format=onnx')
        if result.exit_status != 0:
            print(result.stderr)
            raise OperationError(f"Failed to convert .pt to .onnx on inference server {self._config['host']}."
                                 f"reason={result.stderr}")

        result = await self._conn.run(f'ls {onnx_path}')
        if result.exit_status != 0:
            print(result.stderr)
            raise OperationError(f"Failed to convert .pt to .onnx on inference server {self._config['host']}."
                                 f"reason={result.stderr}")

        return onnx_path

    def _ts_handler(self, model):
        return f'{os.path.dirname(os.path.realpath(__file__))}/yolov8_handler.py'
