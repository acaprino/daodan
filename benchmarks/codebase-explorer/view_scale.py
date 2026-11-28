"""The app's view served from an archive of 80,000 entities with 300 nodes in the first graph: time and bytes.

    python benchmarks/codebase-explorer/view_scale.py [--reps 5]

The envelope is `scale.py`'s for VISIBLE nodes, each component with FILES files and the first with WIDE, more than a
block (`app_view.BLOCK`): 334 visible gives 267 components and 33 external services (the first graph's 300 groups)
and 34 stores. Each case is `app_view.view` on it, CASES; its time is the median of `reps` calls in this process, its
weight the bytes of the JSON the service sends (`visual.make_server`: compact, not ASCII-escaped). Pure Python,
nothing of a project runs; `modal_view_scale.py` runs it on a fixed machine.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "daodan" / "core"))

import app_view  # noqa: E402
import scale  # noqa: E402

VISIBLE, FILES, WIDE = 334, 73, 432  # 67 + 266 × (2 + 73 × 4) + (2 + 432 × 4) = 80,001 entities
WIDE_GROUP = "component:c0000"
CASES = {  # name: (open groups, natures, mode)
    "primo grafo": ((), None, "highlight"),
    "gruppo aperto": (("component:c0001",), None, "highlight"),
    "gruppo a blocchi": ((WIDE_GROUP,), None, "highlight"),
    "blocco «altri N»": ((WIDE_GROUP, f"more:{WIDE_GROUP}#1"), None, "highlight"),
    "filtro hide": ((), ["logico"], "hide"),
    "filtro highlight": ((), ["logico"], "highlight"),
}


def served(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def envelope() -> dict:
    return scale.envelope(VISIBLE, FILES, WIDE)


def measure(reps: int = 5) -> dict:
    """The envelope's counts, then for each case the median and slowest milliseconds, bytes, nodes and edges."""
    started = time.perf_counter()
    data = envelope()
    built = time.perf_counter() - started
    result = {"entities": len(data["entities"]), "relations": len(data["relations"]), "flows": len(data["flows"]),
              "envelope_bytes": len(served(data)), "envelope_ms": round(built * 1000), "reps": reps, "cases": {}}
    for name, (groups, natures, mode) in CASES.items():
        times = []
        for _ in range(reps):
            started = time.perf_counter()
            view = app_view.view(data, groups, natures=natures, mode=mode)
            times.append(time.perf_counter() - started)
        result["cases"][name] = {
            "open": list(groups), "natures": natures, "mode": mode, "nodes": len(view["nodes"]),
            "dim": sum(bool(node.get("dim")) for node in view["nodes"]), "edges": len(view["edges"]),
            "more": [node["name"] for node in view["nodes"] if node["kind"] == "more"],
            "ms_median": round(statistics.median(times) * 1000, 1), "ms_max": round(max(times) * 1000, 1),
            "bytes": len(served(view))}
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reps", type=int, default=5)
    print(json.dumps(measure(parser.parse_args(argv).reps), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
