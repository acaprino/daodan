"""Writes the index of this fixture on Modal with Daodan's own Python adapter (`indexers/python.py`: the pinned
scip-python, `requirements.txt` installed by Daodan's uv, the checker's pass after it), never on this PC, with what the
run leaves beside it (`python._beside`: the environment scip-python was told, the checker's lines), and prints the
symbols the index writes outside the project: the table's rows of `requests` are among them. Run it again after any
change to the sources here: the index states positions.

    export HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
    modal run tests/fixtures/http-wrapper-python/record_index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True  # this folder holds sources only (PYTHONDONTWRITEBYTECODE=1 above covers this file's own)
import modal  # noqa: E402

HERE = Path(__file__).resolve().parent
SHIPPED = ("requirements.txt",)  # and app/: nothing else, no bytecode
KEPT = ("scip-python-0.scip", "scip-python-environment-0.json", "scip-python-0.unbound.jsonl")  # what the run leaves
# The packages `tests/modal_pytest.py` gives the suites, which the adapter imports (pytest apart).
PIP = ("uv==0.11.28", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "keyring>=25",
       "PyYAML>=6", "protobuf==7.36.2", "pip-requirements-parser==32.0.1", "jsonpointer==3.0.0")
image = modal.Image.debian_slim(python_version="3.13").apt_install("git", "ca-certificates").pip_install(*PIP)
if modal.is_local():
    image = image.add_local_dir(HERE.parents[2] / "daodan", "/daodan", ignore=["**/__pycache__/**", "**/node_modules/**"])
app = modal.App("daodan-http-wrapper-python-index", image=image)


@app.function(cpu=2, memory=4096, timeout=1800)
def index(files: dict) -> dict:
    """The files the run leaves, by name, and the global symbols the index refers to and defines nowhere."""
    sys.path.insert(0, "/daodan/core")
    import code_graph
    from indexers import python
    project, work = Path("/work/http-wrapper-python"), Path("/work/engine")
    for rel, data in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_bytes(data)
    engine = python.index(project, work, units=[{"root": "", "manifests": ["requirements.txt"]}])
    runs = engine.get("runs") or []
    if len(runs) != 1 or not runs[0].get("index"):
        raise RuntimeError(f"no index: {engine}")
    print("packages", runs[0].get("packages"), "gaps", engine.get("gaps"), flush=True)
    found = code_graph.Index(project)
    found.load(work / KEPT[0])
    symbols = sorted({o.key for occurrences in found.documents.values() for o in occurrences
                      if code_graph.split_symbol(o.key) and o.key not in found.defs})
    return {"files": {name: (work / name).read_bytes() for name in KEPT if (work / name).is_file()},
            "symbols": symbols}


@app.local_entrypoint()
def main():
    paths = [*(HERE / name for name in SHIPPED), *sorted((HERE / "app").rglob("*.py"))]
    files = {path.relative_to(HERE).as_posix(): path.read_bytes() for path in paths if path.is_file()}
    done = index.remote(files)
    for name, data in done["files"].items():
        print(f"{(HERE / name).write_bytes(data)} bytes written to {HERE / name}")
    print("\n".join(done["symbols"]))
