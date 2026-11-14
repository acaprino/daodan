import numpy as np
import pandas as pd
import requests
from tqdm import tqdm


def load(url):
    rows = requests.get(url).json()
    return pd.DataFrame(tqdm(rows)).assign(z=np.zeros(len(rows)))
