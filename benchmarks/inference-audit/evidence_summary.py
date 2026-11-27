"""Evidence per indexer, read from what the audit runs already wrote in results/ (no run, no new Modal entrypoint).

    python -B benchmarks/inference-audit/evidence_summary.py

One row per file and language:
- `scip-*-full.json` (join.languages.<lang>.cells: A = the second source, B = the index): confirmed = "same project
  target"; false = both answered and differ ("different project target", "mixed: A x, B y" with neither silent);
  holes = "only A has a project target" (the second source found a target the index lacks); seconds and MB are the
  indexer's.
- files with a `report` (graph-*-checks.json, graph-kotlin-klaxon.json): uncertain = sum of `edges_uncertain`,
  holes = sum of the `count` of each `holes` group; no second source there, so confirmed and false stay empty.
Not read: strong-*.json (each engine writes its own shape: no field is the same across them) and the raw graph-*.json
(the same graph as its -checks file, holes listed one by one).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
SILENT = {"none", "not-asked"}  # a side that gave no answer: no disagreement
COLUMNS = ("file", "indexer", "language", "confirmed", "false", "uncertain", "holes", "seconds", "mb")


def cells_row(cells: dict, indexer: dict) -> dict:
    """Confirmed, false arcs and holes from the cells of one language, with the indexer's seconds and MB."""
    false = 0
    for label, count in cells.items():
        if label == "different project target":
            false += count
        elif label.startswith("mixed: A "):
            a, _, b = label.removeprefix("mixed: A ").partition(", B ")
            if not {a, b} & SILENT:
                false += count
    return {"confirmed": cells.get("same project target", 0), "false": false,
            "holes": cells.get("only A has a project target", 0),
            "seconds": indexer.get("seconds"), "mb": indexer.get("peak_rss_mb")}


def report_row(report: dict) -> dict:
    """Uncertain edges and holes of a graph report, with the indexer's seconds and MB."""
    return {"uncertain": sum(report.get("edges_uncertain", {}).values()),
            "holes": sum(group["count"] for group in report.get("holes", [])),
            "seconds": report["indexer"].get("seconds"), "mb": report["indexer"].get("peak_mb")}


def rows(results: Path = RESULTS) -> list[dict]:
    out = []
    for path in sorted(results.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if path.name.startswith("scip-") and path.name.endswith("-full.json"):
            for name, indexer in data["indexers"].items():
                for language, joined in data["join"]["languages"].items():
                    out.append({"file": path.name, "indexer": name, "language": language,
                                **cells_row(joined["cells"], indexer)})
        elif isinstance(data.get("report"), dict):
            report = data["report"]
            out.append({"file": path.name, "indexer": report["indexer"]["name"], "language": report["language"],
                        **report_row(report)})
    return out


if __name__ == "__main__":
    table = rows()
    print("\t".join(COLUMNS))
    for row in table:
        print("\t".join("" if row.get(column) is None else str(row[column]) for column in COLUMNS))
    sys.exit(0 if table else 1)
