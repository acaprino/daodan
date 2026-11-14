"""Go, a second source: the whole-program call graph (callgraph, VTA) beside the index graph, call site by call site.

Wiring only: the adapter `adapters/go_callgraph.py`; the snapshot, indexes and stored graph `modal_scip.py` kept on
the volume (`inference-audit/scip-inputs/chi/`); `scip_graph.py` and `adapters/go.py`, which rebuild the index
graph's ends at each snapshot call (checked edge for edge against the stored graph). One container: the checkout at
the pinned commit, the callgraph run, the comparison and the hand check. No model, no change to the stored graph.

    modal deploy benchmarks/inference-audit/strong_go.py
    python benchmarks/inference-audit/strong_go.py spawn [--label L]
    python benchmarks/inference-audit/strong_go.py fetch [--label L]

Writes `strong-go-chi[-L].json` (counts, every disagreement on a static call, examples, the hand check, the run) and
`strong-go-chi[-L]-callgraph.json.gz` (the adapter's output) on the volume; fetch copies the first to `results/`.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
import modal_scip  # noqa: E402  (puts the plugin's scripts on the path)
import scip_graph  # noqa: E402
from adapters import go, go_callgraph  # noqa: E402
from modal_audit import CASES, _source  # noqa: E402

TAG = "inference-audit"
CASE = "chi"
LANGUAGE = "go"
WALKERS = ("decl mux_test.go:1831", "decl tree_test.go:516", "decl tree_test.go:567", "decl tree_test.go:594",
           "decl tree_test.go:692", "decl _examples/router-walk/main.go:28")
ENCODERS = ("decl middleware/compress.go:398", "decl middleware/compress.go:406", "decl middleware/compress_test.go:24")
# Fifteen calls through an interface or a function value, read in the source before either result existed. The
# expected targets are every function that can reach the called value along the program's assignments and calls,
# conditions not evaluated: `decl FILE:LINE` per project function (the line of its `func`), `external` when every
# target is outside the project.
HAND = [
    ("mux.go", 517, "fn", ("decl mux.go:214", "decl mux.go:234")),  # updateSubRoutes, two callers
    ("tree.go", 718, "fn", ("decl tree.go:636",)),  # node.walk, only routes() passes a function
    ("tree.go", 887, "Routes", ("decl mux.go:358",)),  # Routes interface: *Mux only
    ("tree.go", 888, "Middlewares", ("decl mux.go:363",)),
    ("tree.go", 913, "walkFn", WALKERS),  # every WalkFunc given to Walk
    ("tree.go", 917, "walkFn", WALKERS),
    ("middleware/maybe.go", 10, "mw", ("decl middleware/maybe_test.go:11",)),
    ("middleware/maybe.go", 12, "maybeFn", ("decl middleware/maybe_test.go:19",)),
    ("middleware/maybe.go", 13, "ServeHTTP", ("external",)),  # mw returns an http.HandlerFunc
    ("middleware/compress.go", 182, "fn", ENCODERS),  # SetEncoder: deflate, gzip, the test's nop
    ("middleware/compress.go", 250, "fn", ENCODERS),
    ("middleware/logger.go", 47, "NewLogEntry", ("decl middleware/logger.go:98",)),  # only DefaultLogFormatter
    ("middleware/logger.go", 52, "Status", ("decl middleware/wrap_writer.go:130",)),  # every wrapper embeds basicWriter
    ("_examples/custom-handler/main.go", 13, "h", ("decl _examples/custom-handler/main.go:26",)),
    ("_examples/router-walk/main.go", 18, "Get", ("decl mux.go:155",)),  # Router interface: *Mux only
]
EXAMPLES = 12

image = modal_scip._image().add_local_file(HERE / "modal_scip.py" if LOCAL else Path("/audit/modal_scip.py"),
                                           "/audit/modal_scip.py")
app = modal.App("daodan-strong-go", image=image)
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _declared(target: str) -> str:
    """`file:line` of a snapshot declaration id (`mux.go::function@100:0`)."""
    return f"{target.split('::')[0]}:{target.rsplit('@', 1)[-1].split(':')[0]}"


def _lparen(lines: list, line: int, column: int) -> tuple | None:
    """The `(` after a callee that ends at `(line, byte column)`, past blanks and type arguments; 1-based column."""
    text = lines[line - 1] if 1 <= line <= len(lines) else b""
    at, depth = column, 0
    while at < len(text) and text[at] in b" \t":
        at += 1
    if text[at:at + 1] == b"[":
        while at < len(text):
            depth += {b"[": 1, b"]": -1}.get(text[at:at + 1], 0)
            at += 1
            if depth == 0:
                break
        while at < len(text) and text[at] in b" \t":
            at += 1
    return (line, at + 1) if text[at:at + 1] == b"(" else None


def _keyword(lines: list, line: int, column: int) -> tuple | None:
    """The `go` or `defer` before a callee that starts at `(line, byte column)`; 1-based column."""
    text = (lines[line - 1] if 1 <= line <= len(lines) else b"")[:column].rstrip(b" \t")
    for word in (b"defer", b"go"):
        before = text[:-len(word)]
        if text.endswith(word) and not (before[-1:].isalnum() or before[-1:] == b"_"):
            return line, len(before) + 1
    return None


def _scip(reference: dict, kinds) -> dict:
    """What the index graph answers at one call: project targets direct or by an alias, through an implementation."""
    direct, implemented, externals, values, tags = set(), set(), set(), [], set()
    for end in reference["ends"]:
        tags.update(end.chain)
        if end.cls == "project-callable" and end.target:
            (implemented if "implementation" in end.chain else direct).add(_declared(end.target))
        elif end.cls == "external":
            externals.add(f"{end.detail} {kinds(end.key)}")
        elif end.cls == "project-value":
            values.append(end.detail)
    return {"direct": direct, "implemented": implemented - direct, "externals": externals, "values": values,
            "tags": tags, "target_kinds": {kinds(end.key) for end in reference["ends"] if end.cls == "project-callable"}}


def _cg(edges: list) -> dict:
    project = {edge["callee"].rsplit(":", 1)[0] for edge in edges if edge["external"] is None}
    externals = {f"{edge['external']['package']} {edge['callee']}" for edge in edges if edge["external"]}
    return {"project": project, "externals": externals, "kinds": {edge["kind"] for edge in edges},
            "descriptions": {edge["description"] for edge in edges}}


def _row(site: str, name: str, scip: dict, cg: dict | None) -> str:
    def short(items):
        return ",".join(sorted(items)[:6]) + (f",+{len(items) - 6}" if len(items) > 6 else "")
    text = f"{site} {name} | index: direct {short(scip['direct'])} impl {short(scip['implemented'])} " \
           f"ext {short(scip['externals'])}"
    if cg is not None:
        text += f" | callgraph {'/'.join(sorted(cg['kinds']))}: {short(cg['project'])} ext {short(cg['externals'])}"
    return text


def _sample(items: list, size: int = EXAMPLES) -> list:
    return items if len(items) <= size else [items[int(i * len(items) / size)] for i in range(size)]


def compare(snapshot, index, references: dict, edges: list, nested: set) -> dict:
    """The five questions, site by site: each snapshot call is joined to the callgraph sites at its `(` or keyword."""
    def kinds(key):
        return scip_graph.node_kind(key, index.info.get(key))
    by_site = collections.defaultdict(list)
    for edge in edges:
        by_site[edge["site"]].append(edge)
    anchors, lines_of, spans, outer, on_line = {}, {}, {}, {}, collections.defaultdict(list)
    for identity, rel, kind, _resolution, _lexical, span, parts, _reason in snapshot.references(LANGUAGE):
        if kind != "call":
            continue
        checkout = snapshot.checkout.get(rel, rel)
        if rel not in lines_of:
            lines_of[rel] = snapshot.paths[rel].read_bytes().split(b"\n") if rel in snapshot.paths else []
        spans[identity] = (checkout, span)
        on_line[f"{checkout}:{span[2]}"].append(f"{'.'.join(parts) or '-'} {span}")
        lparen = _lparen(lines_of[rel], span[2], span[3])
        if lparen:
            anchors.setdefault(f"{checkout}:{lparen[0]}:{lparen[1]}", identity)
        keyword = _keyword(lines_of[rel], span[0], span[1])
        if keyword:  # `defer f()()`: the keyword belongs to the outermost call, the one ending last
            key = f"{checkout}:{keyword[0]}:{keyword[1]}"
            if key not in outer or (span[2], span[3]) > outer[key][0]:
                outer[key] = ((span[2], span[3]), identity)
    for key, (_end, identity) in outer.items():
        anchors.setdefault(key, identity)
    joined = collections.defaultdict(list)
    for site, items in by_site.items():
        if site in anchors:
            joined[anchors[site]] += items
    cg_files = {site.rsplit(":", 2)[0] for site in by_site}
    counts = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    static_disagreements, hand_rows = [], []
    for identity, reference in references.items():
        if reference["kind"] != "call":
            continue
        checkout = spans[identity][0]
        site, name = reference["site"], reference["name"]
        scip = _scip(reference, kinds)
        found = joined.get(identity)
        cg = _cg(found) if found else None
        if cg is None:
            # 4. what the analysis misses that the index has
            if scip_graph.owner(checkout, nested) not in (None, ""):
                reason = "nested module"
            elif reference["hole"]:
                reason = f"both silent: index hole {reference['hole']}"
            elif scip["target_kinds"] and scip["target_kinds"] <= {"class", "type"} or (
                    not scip["direct"] and not scip["implemented"] and scip["externals"] and
                    all(item.rsplit(" ", 1)[-1] in ("class", "type") for item in scip["externals"])):
                reason = "conversion to a type"
            elif checkout not in cg_files:
                reason = "file without callgraph sites"
            else:
                reason = "other"
            has = "project target" if scip["direct"] or scip["implemented"] else \
                "external" if scip["externals"] else "value" if scip["values"] else "nothing"
            counts["4 index only"][f"{reason} | index {has}"] += 1
            examples[f"4 {reason} | index {has}"].append(_row(site, name, scip, None))
            continue
        counts["calls"]["joined"] += 1
        counts["calls"][f"callgraph {'+'.join(sorted(cg['kinds']))}"] += 1
        if len(cg["kinds"]) > 1:
            examples["calls with static and dynamic edges"].append(_row(site, name, scip, cg))
        # 1. calls through an interface the index relates implementations to
        if scip["implemented"]:
            kept, dropped = scip["implemented"] & cg["project"], scip["implemented"] - cg["project"]
            added = cg["project"] - scip["implemented"] - scip["direct"]
            counts["1 interface"]["sites"] += 1
            counts["1 interface"]["candidates"] += len(scip["implemented"])
            counts["1 interface"]["kept"] += len(kept)
            counts["1 interface"]["dropped"] += len(dropped)
            counts["1 interface"]["added"] += len(added)
            counts["1 interface"]["sites with a drop"] += bool(dropped)
            counts["1 interface"]["sites with an addition"] += bool(added)
            counts["1 interface"]["sites kept whole"] += not dropped
            counts["1 interface"]["sites left with no project target"] += not (cg["project"] - scip["direct"])
            if not cg["project"] - scip["direct"]:
                examples["1 left with no project target"].append(_row(site, name, scip, cg))
            if dropped:
                examples["1 dropped"].append(_row(site, name, scip, cg) + f" | dropped {','.join(sorted(dropped))}")
            if added:
                examples["1 added"].append(_row(site, name, scip, cg) + f" | added {','.join(sorted(added))}")
        elif "dynamic method call" in " ".join(cg["descriptions"]):
            added = cg["project"] - scip["direct"]
            counts["1 interface, no implementation in the index"]["sites"] += 1
            counts["1 interface, no implementation in the index"]["added"] += len(added)
            counts["1 interface, no implementation in the index"]["sites with an addition"] += bool(added)
            if added:
                examples["1 added, no implementation in the index"].append(_row(site, name, scip, cg))
        # 2. dynamic callees and functions held in a value
        group = "no name (index hole)" if reference["hole"] == "no-position" else \
            "value hop" if "value" in scip["tags"] and scip["direct"] else \
            "project value" if scip["values"] and not scip["direct"] and not scip["implemented"] else None
        if group:
            counts[f"2 {group}"]["joined"] += 1
            counts[f"2 {group}"]["with a project target"] += bool(cg["project"])
            if group == "value hop":
                counts[f"2 {group}"]["same targets as the index"] += cg["project"] == scip["direct"]
            examples[f"2 {group}{'' if cg['project'] else ', no project target'}"].append(_row(site, name, scip, cg))
        if any("dynamic function call" in item for item in cg["descriptions"]):
            counts["2 every dynamic function call"]["sites"] += 1
            counts["2 every dynamic function call"]["with a project target"] += bool(cg["project"])
        # 3. direct calls: the two sources must agree
        if cg["kinds"] == {"static"}:
            index_targets = scip["direct"] | scip["implemented"]
            counts["3 static"]["sites"] += 1
            if len(cg["project"] | cg["externals"]) > 1:
                counts["3 static"]["sites with more than one callee (wrapper folded)"] += 1
            if cg["project"] == scip["direct"] and (cg["project"] or not index_targets):
                counts["3 static"]["agree"] += 1
            else:
                category = "different targets" if cg["project"] and index_targets else (
                    "only the callgraph has a project target" if cg["project"] else "only the index has a project target")
                counts["3 static"][category] += 1
                static_disagreements.append(f"{category} | {_row(site, name, scip, cg)}")
    for remaining, items in by_site.items():
        if remaining not in anchors:
            counts["callgraph sites without a snapshot call"][items[0]["description"]] += 1
            examples["callgraph sites without a snapshot call"].append(
                f"{remaining} -> {','.join(sorted({edge['callee'] for edge in items}))[:160]} | snapshot calls on the line: "
                f"{on_line.get(remaining.rsplit(':', 1)[0], [])}")
    for rel, line, name, expected in HAND:
        found = [(identity, reference) for identity, reference in references.items() if reference["kind"] == "call"
                 and reference["site"] == f"{rel}:{line}" and reference["name"].rsplit(".", 1)[-1] == name]
        if not found:
            hand_rows.append({"site": f"{rel}:{line} {name}", "expected": expected, "error": "no snapshot call"})
            continue
        identity, reference = found[0]
        scip = _scip(reference, kinds)
        cg = _cg(joined.get(identity, []))
        want = {item.split(" ", 1)[1] for item in expected if item.startswith("decl ")}

        def right(project, externals):
            return project == want and (bool(externals) if "external" in expected else True)
        concrete = scip["implemented"] or scip["direct"]  # an interface member's implementations, not the member
        hand_rows.append({
            "site": f"{rel}:{line} {name}", "expected": list(expected),
            "index": sorted(concrete), "index_interface": sorted(scip["direct"]) if scip["implemented"] else [],
            "index_externals": sorted(scip["externals"]), "index_right": right(concrete, scip["externals"]),
            "callgraph": sorted(cg["project"]), "callgraph_externals": sorted(cg["externals"])[:8],
            "callgraph_kinds": sorted(cg["kinds"]), "callgraph_right": right(cg["project"], cg["externals"])})
    return {"counts": {key: dict(value) for key, value in sorted(counts.items())},
            "static_disagreements": static_disagreements,
            "examples": {key: items if key.startswith(("1 left", "2 ", "callgraph", "calls")) else _sample(items)
                         for key, items in sorted(examples.items())},
            "hand": hand_rows,
            "hand_score": {"checks": len(hand_rows), "index_right": sum(row.get("index_right", 0) for row in hand_rows),
                           "callgraph_right": sum(row.get("callgraph_right", 0) for row in hand_rows)},
            "callgraph_files": len(cg_files)}


def _digest(edges: list) -> str:
    import hashlib
    rows = sorted(json.dumps(edge, sort_keys=True) for edge in edges)
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:16]


@app.function(cpu=4, memory=8192, timeout=1800, volumes={"/results": volume})
def strong_case(label: str = "") -> dict:
    import gzip
    import shutil
    import time
    started = time.time()
    work = Path("/work") / CASE  # the kept snapshot binds its sources here
    shutil.rmtree(work, ignore_errors=True)
    kept = Path("/results") / TAG / "scip-inputs" / CASE
    target = _source(work / "src", CASES[CASE], None)
    manifest = work / "snapshot/manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(kept / "manifest.sqlite", manifest)
    indexers = modal_scip._kept_indexers(kept, json.loads((kept / "inputs.json").read_text(encoding="utf-8")))
    result = {"case": CASE, "commit": CASES[CASE]["commit"], "code": scip_graph.code_sha256()}
    begun = time.time()
    output = go_callgraph.analyze(target, work / "callgraph")
    result["engine"], result["engine_wall_seconds"] = output["engine"], round(time.time() - begun, 1)
    edges = output["edges"]
    result["edges"] = {"total": len(edges), "by_kind": dict(collections.Counter(edge["kind"] for edge in edges)),
                       "by_description": dict(collections.Counter(edge["description"] for edge in edges)),
                       "to_project": sum(edge["external"] is None for edge in edges),
                       "sites": len({edge["site"] for edge in edges})}
    stem = f"strong-go-{CASE}-{label}" if label else f"strong-go-{CASE}"
    destination = Path("/results") / TAG / f"{stem}.json"
    print("callgraph", result["engine_wall_seconds"], result["edges"], flush=True)
    if "returncode" in output["engine"]:  # the tool failed: keep its error, compare nothing
        destination.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        volume.commit()
        return {"error": output["engine"]}
    with gzip.open(Path("/results") / TAG / f"{stem}-callgraph.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(output, handle)
    begun = time.time()
    with scip_graph.Snapshot(manifest) as snapshot:
        index = scip_graph.Index(snapshot.root)
        for info in indexers.values():
            for path, prefix in info.get("indexes", ()):
                index.load(Path(path), prefix)
        hops = go.hops(index)
        traversal = scip_graph.Traversal(index, snapshot, hops)
        graph, references = scip_graph.build(index, snapshot, LANGUAGE, hops, indexers["go"].get("indexer") or {},
                                             {}, traversal)
        with gzip.open(kept / "graph-go.json.gz", "rt", encoding="utf-8") as handle:
            stored = json.load(handle)["edges"]
        result["graph_check"] = {"rebuilt_edges": len(graph["edges"]), "stored_edges": len(stored),
                                 "same": _digest(graph["edges"]) == _digest(stored)}
        nested = scip_graph.manifest_dirs(target, "go.mod") - {""}
        result["nested_modules"] = sorted(nested)
        result.update(compare(snapshot, index, references, edges, nested))
    result["compare_seconds"] = round(time.time() - begun, 1)
    result["seconds"] = round(time.time() - started, 1)
    destination.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=sorted) + "\n", encoding="utf-8")
    volume.commit()
    return {"seconds": result["seconds"], "graph_check": result["graph_check"], "hand_score": result["hand_score"]}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    stem = f"strong-go-{CASE}-{args.label}" if args.label else f"strong-go-{CASE}"
    if args.command == "spawn":
        print(CASE, modal.Function.from_name("daodan-strong-go", "strong_case").spawn(args.label).object_id)
    else:
        data = b"".join(volume.read_file(f"{TAG}/{stem}.json"))
        (HERE / "results" / f"{stem}.json").write_bytes(data.replace(b"\r\n", b"\n"))
        print(stem, len(data))
