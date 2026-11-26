"""Writes `index.scip` of this fixture on Modal, with the indexer Daodan pins (`indexers/typescript.py`: VERSION) on the
Node the tests use (`tests/modal_pytest.py`), never on this PC. Run it again after any change to the sources here: the
index states positions.

    export HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
    uv run --no-project --with modal modal run tests/fixtures/http-wrapper/record_index.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # this folder holds sources only (PYTHONDONTWRITEBYTECODE=1 above covers this file's own)
import modal  # noqa: E402

HERE = Path(__file__).resolve().parent
NODE = ("https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.gz",
        "061ec3e3062115705b56b51fa9cc330ab50d34b6969387d4e4b1a50c6809acc2")
FETCH_NODE = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
              "assert hashlib.sha256(data).hexdigest() == '%s'; open('/tmp/node.tar.gz', 'wb').write(data)\"" % NODE)
INDEXER = "@sourcegraph/scip-typescript@0.6.2"
SHIPPED = ("package.json", "tsconfig.json")  # and src/: nothing else, no bytecode
image = (modal.Image.debian_slim(python_version="3.13").apt_install("ca-certificates", "xz-utils")
         .run_commands(FETCH_NODE, "tar -xzf /tmp/node.tar.gz -C /opt && rm /tmp/node.tar.gz",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/node /usr/local/bin/node",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/npm /usr/local/bin/npm",
                       f"npm install --prefix /opt/scip --no-audit --no-fund --ignore-scripts {INDEXER}"))
app = modal.App("daodan-http-wrapper-index", image=image)


@app.function(timeout=900)
def index(files: dict) -> bytes:
    """The index of the files, a project of its own with no dependency: TypeScript's own `lib.dom.d.ts` names `fetch`."""
    work = Path("/work/fx")
    for rel, data in files.items():
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        (work / rel).write_bytes(data)
    subprocess.run(["/opt/scip/node_modules/.bin/scip-typescript", "index", "--cwd", str(work), "--output",
                    "/work/index.scip", "--no-progress-bar"], check=True)
    return Path("/work/index.scip").read_bytes()


@app.local_entrypoint()
def main():
    paths = [*(HERE / name for name in SHIPPED), *sorted((HERE / "src").rglob("*"))]
    files = {path.relative_to(HERE).as_posix(): path.read_bytes() for path in paths if path.is_file()}
    written = (HERE / "index.scip").write_bytes(index.remote(files))
    print(f"{written} bytes written to {HERE / 'index.scip'}")
