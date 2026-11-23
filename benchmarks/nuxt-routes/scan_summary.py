"""What the `scan` step of the pipeline gave for a fixture, kept in `results/pipeline-scan.json`.

    DAODAN_FOLDER=<copy of fixture/nuxt3> PYTHONUTF8=1 python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop scan
    python benchmarks/nuxt-routes/scan_summary.py DIR

`DIR` holds the snapshot and the pre-map the Modal run brought back (`manifest.sqlite`, `premap.json`, `run.json`). Nothing of the
project runs here: the links are Daodan's own reading of the snapshot and of the pre-map, `flows.link_facts` with no rules.
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "daodan/core"))

import binder  # noqa: E402
import flows  # noqa: E402
import semantic_store  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

SOURCES = ("nuxt", "noir", "tsc", "npm", "next", "react-router", "angular")


def main(folder: str) -> None:
    folder = Path(folder)
    record = json.loads((folder / "premap.json").read_text(encoding="utf-8"))
    seconds = json.loads((folder / "run.json").read_text(encoding="utf-8"))["seconds"]
    links = flows.link_facts(folder / "manifest.sqlite", [])
    with open_snapshot(folder / "manifest.sqlite") as store, semantic_store.semantic_reader(store) as db:  # the rows the links bind (`binder.bind`)
        bound = binder.bind(record.get("framework_entries", []), flows.Facts(store, db), semantic_store._Resolver(db))
    mine = [g for g in record["gaps"] if g.get("source", "").startswith("nuxt@")]
    summary = {
        "scan_seconds": seconds,
        "sources": {s["source"].partition("@")[0]: {"state": s["state"], "seconds": s["seconds"]}
                    for s in record["sources"] if s["source"].partition("@")[0] in SOURCES},
        "framework_entries": [{key: row[key] for key in sorted(row) if key != "sources"} for row in bound],
        "source_gaps": mine,
        "noir_entries": sorted([e["method"], e["path"], e["site"]] for e in record.get("noir_entries", [])),
        "links": {
            "entries": {f"{reader} {kind}": count for (reader, kind), count in
                        collections.Counter((e["reader"], e["kind"]) for e in links["entries"]).items()},
            "entry_sites": sorted([e["shape"], e["path"], e["site"], e.get("method")] for e in links["entries"] if e["reader"] == "nuxt"),
            "routes": links["routes"],
            "gaps": dict(collections.Counter(
                "noir: no unique snapshot handler at its site" if "without a unique snapshot handler" in g["reason"] else
                "nuxt: no function found for the exports" if "framework starts" in g["reason"] else g["reason"][:80]
                for g in links["gaps"])),
        },
    }
    out = HERE / "results/pipeline-scan.json"
    out.write_bytes((json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({key: summary[key] for key in ("scan_seconds", "sources", "source_gaps", "links")}, indent=1)[:3500])


if __name__ == "__main__":
    main(sys.argv[1])
