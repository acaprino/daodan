"""The suites start no container: snapshots written here and in `snapshot.py` subprocesses find no engine
(`container.find_engine`), unless a smoke run that needs a real one is asked (`DAODAN_*_SMOKE=1`)."""
import os

if not any(name.startswith("DAODAN_") and name.endswith("_SMOKE") and value == "1"
           for name, value in os.environ.items()):
    os.environ.setdefault("DAODAN_CONTAINER", "off")
