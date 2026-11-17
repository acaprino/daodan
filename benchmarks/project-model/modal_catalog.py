"""The corpus check, ANAGRAFICA.md and the score tables on Modal, nothing run on this PC.

    python benchmarks/project-model/modal_catalog.py                  # check, ANAGRAFICA.md, tables of every tool
    python benchmarks/project-model/modal_catalog.py syft,trivy js    # the tables of some tools on some fixtures

The launcher starts `modal run` on this file. In a container with no network, over the benchmark folder as it is on
disk, `score.py --check all`, `catalog.py` and `score.py <tools> <fixtures>` run; the client prints the check and
the tables, writes ANAGRAFICA.md, the only file it writes, and ends with the check's exit code.
"""
from __future__ import annotations

import contextlib
import io
import os
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REMOTE = "/pm"  # a container path: a POSIX string, whatever runs the client
PROXIES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

if __name__ == "__main__":  # the launcher: Modal's client does not go through a proxy of this shell
    environment = {key: value for key, value in os.environ.items() if key not in PROXIES}
    environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    raise SystemExit(subprocess.run(["modal", "run", str(Path(__file__).resolve()), "--args",
                                     shlex.join(sys.argv[1:])], env=environment).returncode)

import modal  # noqa: E402

image = modal.Image.debian_slim(python_version="3.13")
if modal.is_local():
    image = image.add_local_dir(HERE, REMOTE, ignore=["**/__pycache__/**"])
app = modal.App("daodan-pm-catalog", image=image)


@app.function(cpu=1, memory=2048, timeout=600, block_network=True)
def run(tools: str, fixtures: str) -> dict:
    """The check's output and exit code, ANAGRAFICA.md's text and the tables, from the uploaded folder."""
    sys.path.insert(0, REMOTE)
    import catalog
    import score

    with contextlib.redirect_stdout(io.StringIO()) as check:
        code = score.run_check("all")
    with contextlib.redirect_stdout(io.StringIO()) as tables:
        score.run_tables(tools, fixtures)
    return {"check": check.getvalue(), "code": code, "catalog": catalog.render(*catalog.load()),
            "tables": tables.getvalue()}


@app.local_entrypoint()
def main(args: str = ""):
    tools, fixtures = (shlex.split(args) + ["all", "all"])[:2]
    out = run.remote(tools, fixtures)
    print(out["check"] + out["tables"], end="")
    with open(HERE / "ANAGRAFICA.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(out["catalog"])
    print(f"\nwrote {HERE / 'ANAGRAFICA.md'}")
    if out["code"]:
        raise SystemExit(out["code"])
