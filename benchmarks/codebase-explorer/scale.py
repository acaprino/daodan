"""Synthetic explorer exports with a chosen number of visible nodes in the default view (logical, at the root).

    python benchmarks/codebase-explorer/scale.py 100 300 1000 --out DIR

Writes DIR/<n>/visual.json. Of the n visible nodes, 80% are components, 10% external services, 10% stores.
Each component holds one directory of four files with three symbols each. Every file imports a file of its
own component; the first two also import, and call, a file of one of the eight components before it, so
the component graph is layered, as dependencies usually are. One file in five uses an external service.
One flow per store: a symbol calls a symbol of another component, which writes the store; two symbols of
other components read it. The same n always gives the same export.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def entity(ref: str, kind: str, name: str, **fields) -> dict:
    return {"ref": ref, "type": kind, "name": name, "technical": fields.pop("technical", name), "evidence": [],
            "gaps": [], **fields}


def envelope(n: int) -> dict:
    rng = random.Random(n)
    components, externals = int(n * 0.8), n // 10
    stores = n - components - externals
    entities, relations, memberships, flows = [], [], [], []

    def relate(kind: str, source: str, target: str) -> None:
        relations.append({"ref": f"{kind}:{source}->{target}", "kind": kind, "source": source, "target": target,
                          "status": "confirmed", "evidence": []})

    def file_of(c: int, f: int) -> str:
        return f"src/c{c:04d}/f{f}.ts"

    for e in range(externals):
        entities.append(entity(f"external:svc{e:03d}", "external", f"servizio {e}", provenance="declared",
                               status="confirmed", location="external", node_type="servizio o API"))
    for s in range(stores):
        entities.append(entity(f"store:db/t{s:03d}", "store", f"db/t{s:03d}", location="internal", node_type="database"))
    for c in range(components):
        entities.append(entity(f"component:c{c:04d}", "component", f"componente {c}", provenance="declared",
                               status="confirmed", location="internal"))
        entities.append(entity(f"directory:src/c{c:04d}", "directory", f"c{c:04d}", technical=f"src/c{c:04d}",
                               path=f"src/c{c:04d}"))
        for f in range(4):
            path = file_of(c, f)
            entities.append(entity(f"file:{path}", "file", f"f{f}.ts", technical=path, path=path))
            memberships.append({"member": f"file:{path}", "group": f"component:c{c:04d}", "view": "logical"})
            memberships.append({"member": f"file:{path}", "group": f"directory:src/c{c:04d}", "view": "physical"})
            relate("contains", f"directory:src/c{c:04d}", f"file:{path}")
            for k in range(3):
                entities.append(entity(f"symbol:{path}::s{k}", "symbol", f"s{c}_{f}_{k}", technical=f"{path}::s{k}",
                                       freshness="uncovered", location="internal", path=path, lines=[k * 10 + 1, k * 10 + 9]))
                relate("defines", f"file:{path}", f"symbol:{path}::s{k}")
    for c in range(components):
        for f in range(4):
            path = file_of(c, f)
            relate("imports", f"file:{path}", f"file:{file_of(c, (f + 1) % 4)}")
            if f < 2 and c > 0:
                target = file_of(rng.randrange(max(0, c - 8), c), rng.randrange(4))
                relate("imports", f"file:{path}", f"file:{target}")
                relate("calls", f"symbol:{path}::s0", f"symbol:{target}::s1")
            if externals and rng.random() < 0.2:
                relate("uses", f"file:{path}", f"external:svc{rng.randrange(externals):03d}")
    for s in range(stores):
        entry, writer, *readers = (f"symbol:{file_of(c, rng.randrange(4))}::s2" for c in rng.sample(range(components), 4))
        store = f"store:db/t{s:03d}"
        site = lambda ref: f"{ref.split(':', 1)[1].split('::')[0]}:{rng.randrange(1, 40)}"  # noqa: E731
        steps = [{"source": entry, "target": writer, "type": "chiama", "origin": "diretto", "site": site(entry)},
                 {"source": writer, "target": store, "type": "scrive", "origin": "dedotto", "site": site(writer)}]
        steps += [{"source": store, "target": reader, "type": "legge", "origin": "dedotto", "site": site(reader)}
                  for reader in readers]
        flows.append({"ref": f"flow:{entry}#{s}", "entry": entry, "entry_kind": "azione", "complete": True,
                      "nodes": [entry, writer, store, *readers], "steps": steps})
    meta = {"project_root": f"scale-{n}", "run_id": f"scale-{n}", "target": ".", "git": None,
            "snapshot_digest": "synthetic", "modules_digest": "synthetic", "cards_digest": None,
            "created_at": "2026-11-12T00:00:00Z"}
    return {"schema": "daodan/visual@1", "meta": meta, "entities": entities, "relations": relations,
            "memberships": memberships, "gaps": [], "flows": flows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sizes", type=int, nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    for n in args.sizes:
        data = envelope(n)
        target = args.out / str(n) / "visual.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        print(n, "visible;", len(data["entities"]), "entities,", len(data["relations"]), "relations,",
              len(data["flows"]), "flows,", target.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
