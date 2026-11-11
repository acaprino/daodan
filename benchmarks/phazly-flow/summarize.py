"""Summary of a `flows.py links` result: counts for the README, comparable between two rule sets.

    python benchmarks/phazly-flow/summarize.py LINKS.json [--out SUMMARY.json]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins/codebase-map/skills/map/scripts"))
import flows  # noqa: E402


def summarize(links: dict) -> dict:
    count = collections.Counter
    layer = lambda node: node.split("/", 1)[0]  # noqa: E731
    traced = []
    for entry in links["entries"]:
        flow = flows.trace(links, entry["symbol"], "from")
        symbols = [node for node in flow["nodes"] if "::" in node]
        traced.append({"nodes": len(flow["nodes"]), "layers": len({layer(node) for node in symbols}),
                       "stores": sum(1 for node in flow["nodes"] if node.startswith("store:")),
                       "complete": flow["complete"]})
    stores = links["stores"]
    return {
        "entries": dict(count(entry["kind"] for entry in links["entries"])),
        "edges": {f"{kind} {origin}": number for (kind, origin), number in
                  sorted(count((edge["type"], edge["origin"]) for edge in links["edges"]).items())},
        "routes": links.get("routes"),
        "stores": {"total": len(stores), "by_store": dict(count(name.split("/")[0] for name in stores)),
                   "with_writers_and_readers": sum(1 for s in stores.values() if s["writes"] and s["reads"]),
                   "only_written": sum(1 for s in stores.values() if not s["reads"]),
                   "only_read": sum(1 for s in stores.values() if not s["writes"])},
        "flows": {"total": len(traced), "reach_a_store": sum(1 for f in traced if f["stores"]),
                  "cross_layer": sum(1 for f in traced if f["layers"] > 1),
                  "single_node": sum(1 for f in traced if f["nodes"] == 1),
                  "largest_nodes": max((f["nodes"] for f in traced), default=0),
                  "incomplete": sum(1 for f in traced if not f["complete"])},
        "gaps": dict(count(gap["reason"].split(": route")[0] for gap in links["gaps"]).most_common()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("links", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    summary = summarize(json.loads(args.links.read_text(encoding="utf-8")))
    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
