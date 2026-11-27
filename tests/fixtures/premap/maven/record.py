"""Record Maven's answers for a case beside this file (`<case>/`) into `<case>.json`, on Modal only:

    modal run tests/modal_pytest.py --command "python tests/fixtures/premap/maven/record.py <case>" \
        --fetch tests/fixtures/premap/maven/<case>.json

The Maven `premap.maven` names (`DOWNLOAD`, checked by its sha256) runs on the image's OpenJDK 17; the case is
copied to `/work` and each command of `maven.commands` runs in its folder there.
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
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "daodan/core"))

from premap import maven  # noqa: E402

HOME = Path("/opt/maven")
WORK = Path("/work")


def main(case: str) -> None:
    url, sha256 = maven.DOWNLOAD[0]
    data = urllib.request.urlopen(url).read()
    assert hashlib.sha256(data).hexdigest() == sha256
    shutil.rmtree(HOME, ignore_errors=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(HOME)
    [bin_dir] = HOME.glob("*/bin")
    for tool in bin_dir.iterdir():
        tool.chmod(0o755)
    shutil.rmtree(WORK, ignore_errors=True)
    shutil.copytree(HERE / case, WORK)

    class Inventory:
        files = sorted(p.relative_to(WORK).as_posix() for p in WORK.rglob("*") if p.is_file())

    class Context:
        inventory = Inventory()

    runs = []
    for command in maven.commands(Context()):
        env = {**os.environ, **command["env"], "PATH": f"{bin_dir}:{os.environ['PATH']}"}
        done = subprocess.run(command["argv"], cwd=WORK / command["cwd"], env=env, capture_output=True, text=True)
        runs.append({"command": command, "result": {"returncode": done.returncode, "stdout": done.stdout,
                                                    "stderr": done.stderr, "root": str(WORK)}})
    record = {"versions": {"maven": maven.VERSION}, "image": "tests/modal_pytest.py", "runs": runs}
    (HERE / f"{case}.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
