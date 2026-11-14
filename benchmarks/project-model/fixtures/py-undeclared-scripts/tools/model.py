import json

import numpy as np
from sklearn.ensemble import RandomForestClassifier


def fit(x, y):
    return RandomForestClassifier().fit(np.array(x), np.array(y)), json.dumps(y)
