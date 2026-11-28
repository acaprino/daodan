"""Record Gradle's answers for a case into `<case>.json` beside this file, on Modal only:

    modal run tests/modal_pytest.py --command "python tests/fixtures/premap/versions/gradle/record.py <case>" \
        --fetch tests/fixtures/premap/versions/gradle/<case>.json

The case is `tests/fixtures/premap/versions/<case>/`, else the corpus fixture `benchmarks/project-model/fixtures/<case>/`
(a real one, `source.json` alone, cloned at its commit); it is copied to `/work/<case>` and each command of
`gradle.commands` runs in its folder there, with the Gradle `premap.gradle` names (`DOWNLOAD`) on Temurin's JDK 17
(`preparation.TEMURIN`), each checked by its sha256.
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
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / "daodan/core"))

import preparation  # noqa: E402
from premap import gradle  # noqa: E402

OPT = Path("/opt/daodan-record")
CORPUS = REPO / "benchmarks/project-model/fixtures"


def fetch(url: str, sha256: str) -> bytes:
    data = urllib.request.urlopen(url).read()
    assert hashlib.sha256(data).hexdigest() == sha256, url
    return data


def project(case: str, work: Path) -> None:
    own, corpus = HERE.parent / case, CORPUS / case
    source = corpus / "source.json"
    if own.is_dir() or not source.is_file() or {p.name for p in corpus.iterdir()} - {"source.json", "expected.json"}:
        shutil.copytree(own if own.is_dir() else corpus, work, ignore=shutil.ignore_patterns("expected.json"))
        return
    origin = json.loads(source.read_text(encoding="utf-8"))
    subprocess.run(["git", "init", "-q", str(work)], check=True)
    subprocess.run(["git", "-C", str(work), "fetch", "-q", "--depth", "1", origin["repo"], origin["commit"]], check=True)
    subprocess.run(["git", "-C", str(work), "checkout", "-q", "FETCH_HEAD"], check=True)
    shutil.rmtree(work / ".git")


def main(case: str) -> None:
    shutil.rmtree(OPT, ignore_errors=True)
    tarfile.open(fileobj=io.BytesIO(fetch(*preparation.TEMURIN))).extractall(OPT / "jdk", filter="tar")
    zipfile.ZipFile(io.BytesIO(fetch(*gradle.DOWNLOAD[0]))).extractall(OPT / "gradle")
    [jdk] = (OPT / "jdk").glob("*/bin")
    [bin_dir] = (OPT / "gradle").glob("*/bin")
    for tool in [*bin_dir.iterdir(), *jdk.iterdir()]:
        tool.chmod(0o755)
    work = Path("/work") / case
    shutil.rmtree(work, ignore_errors=True)
    project(case, work)

    class Inventory:
        files = sorted(p.relative_to(work).as_posix() for p in work.rglob("*") if p.is_file())

    class Context:
        inventory = Inventory()

    runs = []
    for command in gradle.commands(Context()):
        env = {**os.environ, **command["env"], "JAVA_HOME": str(jdk.parent),
               "PATH": f"{bin_dir}:{jdk}:{os.environ['PATH']}"}
        done = subprocess.run(command["argv"], cwd=work / command["cwd"], env=env, capture_output=True, text=True)
        runs.append({"command": command, "result": {"returncode": done.returncode, "stdout": done.stdout,
                                                    "stderr": done.stderr, "root": str(work)}})
    record = {"source": f"{case}: gradle {gradle.VERSION} on Temurin 17.0.21, Modal's image (tests/modal_pytest.py),"
                        " recorded by record.py", "runs": runs}
    (HERE / f"{case}.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
