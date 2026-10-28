"""Shared run paths and frozen-writing helpers for the adapter retest."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUN = ROOT / '.daodan/runs/2026-10-27-julia-adapter-retest'
PRIOR = ROOT / '.daodan/runs/2026-10-27-julia-cpu-pilot'
BASE_PATH = ROOT / 'evals/julia-criteria-ablation/experiment.py'


def load_base():
    """The frozen prior experiment module: identity chain, guard and configuration."""
    spec = importlib.util.spec_from_file_location('retest_base', BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def write_path(path, value, *, frozen=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if frozen:
        with path.open('xb') as stream:
            stream.write(encoded(value))
    else:
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_bytes(encoded(value))
        temporary.replace(path)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(2 ** 20), b''):
            digest.update(chunk)
    return digest.hexdigest()
