import os
import yaml


def load(filename, dirname=None, read_envs=False):
    if dirname is None:
        dirname = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(dirname, filename), 'r') as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)

    if read_envs:
        load_envs(data, prefix='LAP')
    return data


def load_envs(config, prefix):
    for k, v in config.items():
        if type(v) == dict:
            load_envs(config=v, prefix=f'{prefix}_{k}')
        else:
            v_ = os.environ.get(f'{prefix}_{k}'.upper(), v)
            if v_ == 'true':
                config[k] = True
            elif v_ == 'false':
                config[k] = False
            else:
                config[k] = v_
