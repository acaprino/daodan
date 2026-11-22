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
    # The owner's own setting must not move what the suites isolate through LOCALAPPDATA or XDG_CACHE_HOME into the
    # real shared folder; `tests/test_shared_dir.py` sets it where it tests it. A smoke run keeps it: it uses the
    # real engine, which is where the setting put it.
    os.environ.pop("DAODAN_SHARED_DIR", None)


@pytest.fixture(scope="session", autouse=True)
def _grammars():
    scripts = str(Path(__file__).resolve().parents[1] / "daodan/core")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from languages import _treesitter
    _treesitter.get_parser("python")
