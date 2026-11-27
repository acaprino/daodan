"""Record the MSBuild evaluations of a case beside this file (`<case>/`) into `<case>.json`, on Modal only:

    modal run tests/modal_pytest.py --command "python tests/fixtures/premap/dotnet/record.py <case>" \
        --fetch tests/fixtures/premap/dotnet/<case>.json

The .NET SDK `premap.dotnet` names (`DOWNLOAD`, checked by its sha512) goes where Daodan's container keeps it; the
case is copied to `/work` and each command of `dotnet.commands` runs in its folder there.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "daodan/core"))

from premap import dotnet  # noqa: E402

SDK = Path("/daodan/state/tools/dotnet")
WORK = Path("/work")


def main(case: str) -> None:
    url, sha512 = dotnet.DOWNLOAD[0]
    data = urllib.request.urlopen(url).read()
    assert hashlib.sha512(data).hexdigest() == sha512
    SDK.mkdir(parents=True, exist_ok=True)
    tarfile.open(fileobj=io.BytesIO(data)).extractall(SDK, filter="data")
    shutil.rmtree(WORK, ignore_errors=True)
    shutil.copytree(HERE / case, WORK)

    class Inventory:
        files = sorted(p.relative_to(WORK).as_posix() for p in WORK.rglob("*") if p.is_file())

    class Context:
        inventory = Inventory()

    runs = []
    for command in dotnet.commands(Context()):
        env = {**os.environ, **command["env"], "DOTNET_ROOT": str(SDK), "PATH": f"{SDK}:{os.environ['PATH']}"}
        done = subprocess.run(command["argv"], cwd=WORK / command["cwd"], env=env, capture_output=True, text=True)
        runs.append({"command": command, "result": {"returncode": done.returncode, "stdout": done.stdout,
                                                    "stderr": done.stderr, "root": str(WORK)}})
    record = {"versions": {"dotnet": dotnet.VERSION}, "image": "tests/modal_pytest.py", "runs": runs}
    (HERE / f"{case}.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
