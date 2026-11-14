import os

import yaml


def load(path):
    with open(os.path.join(path, "conf.yml")) as fh:
        return yaml.safe_load(fh)
