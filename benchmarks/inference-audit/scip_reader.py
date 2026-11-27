"""The SCIP reader of `code_graph.Index.load` against an earlier one (T2.B.2: the hand-written Protocol Buffers reader
before `scip_pb2`): the same index read by both, every field `Index` keeps compared, and the seconds of each read.
No model or graph: what a graph is built from is the `Index`, so the same `Index` is the same graph.

    modal run benchmarks/inference-audit/scip_reader.py --before <commit>

`--before` names the commit whose `daodan/core/code_graph.py` is the earlier reader. The indexes: every committed
fixture index (`tests/fixtures/code-graph/*/index.scip`) and the kept indexes of chi, semver and tududi on the
volume (`inference-audit/scip-inputs/<case>/inputs.json`). Result in `results/scip-reader.json`.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
ROOT = HERE.parents[1] if LOCAL else None
CORE = ROOT / "daodan/core" if LOCAL else None
FIXTURES = ROOT / "tests/fixtures/code-graph" if LOCAL else None
CASES = ("chi", "semver", "tududi")
KEPT = ("tools", "documents", "units", "defs", "info", "implementers", "repeated", "unknown")

AFTER = CORE if LOCAL else Path("/reader/after")
image = (modal.Image.debian_slim(python_version="3.13").pip_install("protobuf==7.36.2")
         .add_local_file(AFTER / "code_graph.py", "/reader/after/code_graph.py")
         .add_local_file(AFTER / "scip_pb2.py", "/reader/after/scip_pb2.py")
         .add_local_dir(FIXTURES if LOCAL else Path("/fixtures"), "/fixtures"))
app = modal.App("daodan-scip-reader", image=image)
volume = modal.Volume.from_name("daodan-flow-results")


def _read(where: Path, index: Path, prefix: str) -> tuple[float, dict]:
    """Seconds of one read in a fresh interpreter, and the sha256 of each field the `Index` keeps."""
    script = (f"import hashlib, json, sys, time; sys.path.insert(0, {str(where)!r}); import code_graph\n"
              f"index = code_graph.Index('/tmp'); begun = time.perf_counter()\n"
              f"index.load({str(index)!r}, {prefix!r}); seconds = time.perf_counter() - begun\n"
              f"value = lambda item: sorted(item.items()) if isinstance(item, dict) else item\n"
              f"kept = {{name: hashlib.sha256(repr(value(getattr(index, name))).encode()).hexdigest()"
              f" for name in {KEPT!r}}}\n"
              f"print(json.dumps({{'seconds': seconds, 'kept': kept}}))")
    done = subprocess.run(["python", "-B", "-c", script], capture_output=True, text=True, check=True)
    out = json.loads(done.stdout)
    return out["seconds"], out["kept"]


@app.function(volumes={"/results": volume}, cpu=2, memory=8192, timeout=1800)
def compare(before: str) -> dict:
    old = Path("/reader/before")
    old.mkdir(parents=True)
    (old / "code_graph.py").write_text(before, encoding="utf-8")
    indexes = [(f"fixture {path.parent.name}", path, "") for path in sorted(Path("/fixtures").glob("*/index.scip"))]
    for case in CASES:
        inputs = json.loads(Path(f"/results/inference-audit/scip-inputs/{case}/inputs.json").read_text(encoding="utf-8"))
        indexes += [(f"{case} {Path(path).name}", Path(path), prefix)
                    for info in inputs["indexers"].values() for path, prefix in info.get("indexes", ())]
    rows = []
    for name, path, prefix in indexes:
        path.read_bytes()  # the volume's file read once before either reader, so that neither pays the first read
        seconds_before, kept_before = _read(old, path, prefix)
        seconds_after, kept_after = _read(Path("/reader/after"), path, prefix)
        rows.append({"index": name, "bytes": path.stat().st_size, "seconds_before": round(seconds_before, 2),
                     "seconds_after": round(seconds_after, 2),
                     "different": [key for key in KEPT if kept_before[key] != kept_after[key]]})
    return {"rows": rows}


@app.local_entrypoint()
def main(before: str):
    text = subprocess.run(["git", "show", f"{before}:daodan/core/code_graph.py"], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    result = {"before": before, "after": head.strip(), **compare.remote(text)}
    (HERE / "results/scip-reader.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for row in result["rows"]:
        print(row)
