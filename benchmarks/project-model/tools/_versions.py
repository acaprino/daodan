"""Shared pieces of the `versions` adapters: a subprocess wrapper, path and tool-name normalisers, and the child
process the Modal driver measures. Not an adapter. Standard library only."""
from __future__ import annotations

import importlib
import json
import os
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

# Tool names as the corpus writes them. Only spellings that differ; any other name is lower-cased as it comes.
CANON = {"nodejs": "node", "golang": "go", "rustc": "rust", "cpython": "python", "jdk": "java", "jre": "java",
         "temurin": "java", "openjdk": "java", "node.js": "node", "gradle-wrapper": "gradle"}


def canon(name) -> str:
    s = str(name or "").strip().lower()
    return CANON.get(s, s)


def sh(cmd, cwd, env: dict | None = None, timeout: int = 600) -> dict:
    """Run a command without a shell; never raises. `env` entries are added to the inherited environment."""
    full = dict(os.environ)
    full.update({k: v for k, v in (env or {}).items() if v is not None})
    try:
        done = subprocess.run([str(c) for c in cmd], cwd=str(cwd), env=full, capture_output=True, text=True,
                              errors="replace", timeout=timeout)
        return {"rc": done.returncode, "out": done.stdout, "err": done.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"rc": -1, "out": exc.stdout or "", "err": f"timeout after {timeout}s"}
    except OSError as exc:
        return {"rc": -2, "out": "", "err": f"{type(exc).__name__}: {exc}"}


def rel(path, root) -> str | None:
    """`path` relative to `root` as POSIX, or None when it is outside."""
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except (ValueError, OSError):
        return None


def confine() -> bool:
    """True when the driver asks the installing adapters to keep every cache inside the work directory."""
    return os.environ.get("PMV_CONFINE") == "1"


# ---------------------------------------------------------------- child process of the driver

def child(tool: str, project: str, work: str, out: str) -> None:
    """Run adapter `tool` once and write {output, seconds, peak_mb, error} to `out`. Peak memory is the largest
    descendant of this process, so the adapter's own interpreter is not counted."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    record = {"output": None, "error": None}
    start = time.time()
    try:
        module = importlib.import_module(tool)
        record["version"] = getattr(module, "VERSION", None)
        record["output"] = module.run(project, work)
    except Exception as exc:  # noqa: BLE001 - the driver needs the failure, not a traceback
        record["error"] = f"{type(exc).__name__}: {exc}"
    record["seconds"] = round(time.time() - start, 2)
    record["peak_mb"] = round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1)
    Path(out).write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    child(*sys.argv[1:5])
