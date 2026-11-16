"""The suites start no container: snapshots written here and in `snapshot.py` subprocesses find no engine
(`container.find_engine`), unless a smoke run that needs a real one is asked (`DAODAN_*_SMOKE=1`).

The grammars are placed once per process, by its first parse (`languages._treesitter._ensure_grammars`): here,
before any test, so none places them under its fake URLs and leaves the tests after it in the process without a
parser (their languages would read `unavailable`)."""
import os
import sys
from pathlib import Path

import pytest

if not any(name.startswith("DAODAN_") and name.endswith("_SMOKE") and value == "1"
           for name, value in os.environ.items()):
    os.environ.setdefault("DAODAN_CONTAINER", "off")


@pytest.fixture(scope="session", autouse=True)
def _grammars():
    scripts = str(Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from languages import _treesitter
    _treesitter.get_parser("python")
