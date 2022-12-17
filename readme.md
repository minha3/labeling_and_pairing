# Labeling and Pairing

The purpose of this project is practicing some third-party libraries.

- [FastAPI](https://github.com/tiangolo/fastapi) for web framework
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) for database access
- [gRPC](https://github.com/grpc/grpc/tree/master/src/python/grpcio) for remote procedure call (RPC) framework
- [Svelte](https://svelte.dev/) for user interface

The idea of this project is to help review, modify, retrain the labels suggested by a machine learning model.

<img src="./images/sample1.png">

## Processes

- User upload csv files containing image urls.
- API server downloads and saves images and sends it to inference server.
- API server stores the response received from inference server in the database.
- User review images, regions and labels and modify labels.

## Requirements

- Python 3.9
- Node.js v16.x
- SQLite 3 or MySQL 8.0.x

## Quickstart

1. Install requirements.txt

```shell
$ pip install -r requirements.txt
```

2. To generate the gRPC client and server interfaces from your .proto service definition, Compile .proto files

```shell
$ python -m grpc_tools.protoc -Iprotos --python_out=inference/ protos/data.proto
$ python -m grpc_tools.protoc -Iprotos --python_out=inference/ --grpc_python_out=inference/ protos/inference.proto
```

Then 3 files(`data_pb2.py`, `inference_pb2.py`, `inference_pb2_grpc.py`) are generated in inference directory

3. To fix ModuleNotFoundError
- open `inference/inference_pb2.py` and change "import data_pb2 as data__pb2" to "from . import data_pb2 as data__pb2"
- open `inference/inference_pb2_grpc.py` and change "import inference_pb2 as inference__pb2" to "from . import inference_pb2 as inference__pb2"

4. Copy example configuration file and fill in the configuration values

```shell
$ cp config/lap_config.yml.example config/lap_config.yml
```

5. Run api server

```shell
$ PYTHONPATH=. python app/run.py
```

6. Run web server

```shell
$ cd web
$ npm install
$ npm run build
$ npm start
```

## License
[MIT](LICENSE)
