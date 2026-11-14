"""Two whole-program sources for JavaScript and TypeScript beside the SCIP index graph, call site by call site.

The sources are `adapters/ts_compiler.py` (the TypeScript compiler API in batch, run twice: with the project's
install, then with the `@types/*` packages its dependencies lack) and `adapters/js_jelly.py` (Jelly, static
only, with `node_modules` and with `--ignore-dependencies`). The index graph is rebuilt from the snapshot and
the scip-typescript index an earlier `modal_scip.py` run kept on the volume (`scip-inputs/<case>/`), with
`adapters/typescript.py` for the hops. Every snapshot call is then classed by what the index gives there and by
what each source gives at the same site (the callee's last name, line and UTF-8 byte column).

    modal deploy benchmarks/inference-audit/strong_js.py
    python benchmarks/inference-audit/strong_js.py spawn [--label L]
    python benchmarks/inference-audit/strong_js.py fetch [--label L]

`python strong_js.py local --project P --manifest M --index I --out O` runs both sources and the comparison
on a small project (`fixtures/ts` in a scratch copy with its packages installed).
"""
from __future__ import annotations

import collections
import json
import os
import random
import sys
from pathlib import Path

try:
    import modal
except ImportError:  # the local comparison runs without Modal
    modal = None

HERE = Path(__file__).resolve().parent
LOCAL = modal is None or modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import scip_graph  # noqa: E402
from adapters import js_jelly, ts_compiler, typescript  # noqa: E402
if modal is not None:
    from modal_audit import CASES, _source  # noqa: E402

NODE = ("v22.23.4", "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce")  # as modal_scip.py
TOOLS = {"@typescript/typescript6": ts_compiler.VERSION, "@cs-au-dk/jelly": js_jelly.VERSION}
LANGUAGES = ("javascript", "typescript")
SEED = 20261114
# Call sites read in the source before any result of these sources existed: `decl F:L[,F:L...]` (exactly these
# project functions, by the line they start on), `external PACKAGE[|PACKAGE]` (a substring of an external's
# package and no project function), `none` (no project function). The first four are the sites the index
# graph got wrong (13 November); then eight on untyped receivers and eight calls of a callback, picked with
# seed 20261114 among regex matches of the checkout.
HAND = [
    ("backend/migrations/archive/20251023000001-add-unique-constraint-tags.js", 162, "addIndex", "external sequelize"),
    ("backend/modules/caldav/icalendar/vtodo-parser.js", 189, "toJSDate", "external ical.js"),
    ("backend/tests/integration/recurring-tasks.test.js", 365, "create", "external sequelize"),
    ("frontend/components/Inbox/__tests__/QuickCaptureInput.focus.test.tsx", 88, "slice", "external typescript"),
    ("backend/modules/admin/service.js", 840, "findAll", "external sequelize"),
    ("backend/modules/tasks/taskReminderService.js", 14, "findAll", "external sequelize"),
    ("backend/services/entitlementsService.js", 144, "findOrCreate", "external sequelize"),
    ("backend/modules/caldav/api/calendar-controller.js", 106, "create",
     "decl backend/shared/database/BaseRepository.js:24"),  # an instance of a subclass, exported by the module
    ("backend/modules/inbox/repository.js", 77, "update", "external sequelize"),
    ("backend/modules/projects/service.js", 462, "toJSON", "external sequelize"),
    ("backend/modules/tasks/routes.js", 612, "status", "external express"),
    ("backend/modules/oidc/auditService.js", 121, "get", "external express"),
    ("frontend/components/Habits/HabitDayPanel.tsx", 94, "fn",  # guard(fn): two closures here, onSkip's value
     "decl frontend/components/Habits/HabitDayPanel.tsx:104,frontend/components/Habits/HabitDayPanel.tsx:187,"
     "frontend/components/Habits/HabitDetails.tsx:446"),
    ("frontend/components/Note/MissingNotePrompt.tsx", 75, "onClose",  # closeMissingNote, a useCallback
     "decl frontend/components/Note/MarkdownEditor.tsx:298"),
    ("frontend/components/Tag/TagModal.tsx", 76, "onClose",  # three parents
     "decl frontend/hooks/usePersistedModal.ts:64,frontend/components/Tags.tsx:231,frontend/Layout.tsx:238"),
    ("backend/modules/groups/controller.js", 34, "next", "external express"),  # express's own next
    ("backend/modules/webhooks/controller.js", 15, "fn",  # handle(fn), seven closures
     "decl " + ",".join(f"backend/modules/webhooks/controller.js:{line}" for line in (22, 23, 24, 27, 28, 31, 34))),
    ("backend/modules/webhooks/taskEvents.js", 88, "fn",  # afterCommit(options, fn)
     "decl backend/modules/webhooks/taskEvents.js:105,backend/modules/webhooks/taskEvents.js:124,"
     "backend/modules/webhooks/taskEvents.js:136"),
    ("backend/modules/caldav/services/safe-request.js", 107, "callback", "none"),  # Node's lookup callback
    ("backend/modules/backup/routes.js", 27, "cb", "external multer"),  # multer's fileFilter callback
]


def _image():
    node_version, node_sha = NODE
    node = f"node-{node_version}-linux-x64.tar.xz"
    tools = " ".join(f"{name}@{version}" for name, version in TOOLS.items())
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "curl", "ca-certificates", "nodejs", "npm", "unzip", "xz-utils")
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(
            f"curl -fsSL https://nodejs.org/dist/{node_version}/{node} -o /tmp/{node}",
            f"echo '{node_sha}  /tmp/{node}' | sha256sum -c -",
            f"mkdir -p /opt/node && tar -xJf /tmp/{node} -C /opt/node --strip-components=1 && rm /tmp/{node}",
            f"mkdir -p /opt/strong-js && cd /opt/strong-js && echo '{{\"private\":true}}' > package.json && "
            f"PATH=/opt/node/bin:$PATH npm install --ignore-scripts --no-audit --no-fund {tools}",
        )
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "probe.py" if LOCAL else Path("/audit/probe.py"), "/audit/probe.py")
        .add_local_file(HERE / "scip_graph.py" if LOCAL else Path("/audit/scip_graph.py"), "/audit/scip_graph.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-strong-js", image=_image()) if modal else None
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True) if modal else None


# --- the index graph at each snapshot call -------------------------------------------------------------------

def index_sites(manifest: Path, index_paths: list) -> tuple[dict, dict]:
    """`{site: [row]}` of the snapshot's JS/TS calls with what the index graph gives there, and its counts."""
    out, counts = collections.defaultdict(list), {}
    snapshot = scip_graph.Snapshot(manifest).__enter__()
    index = scip_graph.Index(snapshot.root)
    for path, prefix in index_paths:
        index.load(Path(path), prefix)
    hops = typescript.hops(index)
    traversal = scip_graph.Traversal(index, snapshot, hops)
    for language in LANGUAGES:
        _graph, references = scip_graph.build(index, snapshot, language, hops, {}, {}, traversal)
        positions = {}
        for identity, rel, kind, _res, _lex, span, parts, _reason in snapshot.references(language):
            if kind == "call":
                site = snapshot.callee(rel, span, parts)
                positions[identity] = (snapshot.checkout.get(rel, rel), site)
        counts[language] = collections.Counter()
        for identity, reference in references.items():
            if reference["kind"] != "call":
                continue
            checkout, site = positions[identity]
            row = {"language": language, "name": reference["name"], "reason": reference["reason"],
                   **_index_answer(reference), "site": f"{checkout}:{site[0]}" if site else reference["site"]}
            counts[language][row["group"]] += 1
            key = f"{checkout}:{site[0]}:{site[1]}" if site else f"no-position {reference['site']} {identity}"
            out[key].append(row)
    return out, {"snapshot": snapshot, "counts": {k: dict(v) for k, v in counts.items()}}


def _index_answer(reference: dict) -> dict:
    ends = reference["ends"]
    targets = sorted({end.target for end in ends if end.cls == "project-callable" and end.target})
    externals = sorted({end.detail for end in ends if end.cls == "external"})
    chains = sorted({"+".join(end.chain) for end in ends if end.cls == "project-callable" and end.target})
    if targets:
        declared = any("declared:" in chain for chain in chains)
        group = "index: project function" + (" via declared hop" if declared else "")
    elif reference["hole"]:
        group = f"hole: {reference['hole']} / {reference['reason']}"
    elif externals:
        group = "index: external"
    else:
        values = sorted({end.detail for end in ends if end.cls == "project-value"})
        group = "index: project value, parameter" if values == ["parameter"] else \
            f"index: project value, {'/'.join(values) or 'none'}"
    return {"group": group, "targets": targets, "externals": externals, "chains": chains}


# --- each source at the same sites --------------------------------------------------------------------------

def _arguments_span(root: Path, site: str, trees: dict) -> tuple | None:
    """`((row, byte column), (row, byte column))` of the argument list of the call whose callee is named at
    `site`, None without one; a function starting there is a callback the callee is given, not the callee."""
    rel, line, column = site.rsplit(":", 2)
    if rel not in trees:
        from adapters import js_jelly
        trees[rel] = js_jelly._trees()(Path(root) / rel)
    tree = trees[rel]
    if tree is None:
        return None
    point = (int(line) - 1, int(column))
    node = tree.root_node.descendant_for_point_range(point, (point[0], point[1] + 1))
    while node is not None and node.type not in ("call_expression", "new_expression"):
        node = node.parent
    arguments = node.child_by_field_name("arguments") if node is not None else None
    return (tuple(arguments.start_point), tuple(arguments.end_point)) if arguments is not None else None


def source_sites(edges: list, snapshot, kinds=("call", "new")) -> dict:
    """`{site: {"targets", "arguments", "externals", "other"}}` of one source; `arguments` are the targets that
    start inside the call's own argument list; `other` names project positions that are no function, method or
    class of the snapshot (a parameter, a type, a property)."""
    out = collections.defaultdict(lambda: {"targets": set(), "arguments": set(), "externals": set(), "other": set()})
    trees, spans = {}, {}
    for edge in edges:
        if edge["kind"] not in kinds:
            continue
        cell = out[edge["site"]]
        if edge["external"] is not None:
            package = edge["external"]
            cell["externals"].add(f"{package['manager']} {package['package']}@{package['version']}")
            continue
        rel, line, column = edge["callee"].rsplit(":", 2)
        identity = snapshot.function_at(snapshot.rel.get(rel, rel), int(line), int(column))
        if not identity:
            cell["other"].add(f"{edge['callee']} {edge.get('declaration') or ''}".strip())
            continue
        cell["targets"].add(identity)
        if rel == edge["site"].rsplit(":", 2)[0]:
            if edge["site"] not in spans:
                spans[edge["site"]] = _arguments_span(snapshot.root, edge["site"], trees)
            span = spans[edge["site"]]
            if span is not None and span[0] <= (int(line) - 1, int(column)) < span[1]:
                cell["arguments"].add(identity)
    return out


def _outcome(cell: dict | None) -> str:
    if not cell:
        return "none"
    return "project function" if cell["targets"] - cell["arguments"] else \
        "callback in the arguments" if cell["targets"] else "external" if cell["externals"] else \
        "project, not a function" if cell["other"] else "none"


def compare(index: dict, snapshot, sources: dict) -> dict:
    """Per index group, what each source gives; the disagreements where the index has a project target."""
    sites = {name: source_sites(edges, snapshot) for name, edges in sources.items()}
    table = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    examples = collections.defaultdict(list)
    disagreements = collections.defaultdict(list)
    relation = collections.defaultdict(collections.Counter)
    for key, rows in index.items():
        for row in rows:
            group = f"{row['language']} | {row['group']}"
            for name, found in sites.items():
                cell = found.get(key)
                outcome = _outcome(cell)
                table[group][name][outcome] += 1
                if outcome in ("project function", "external") and len(examples[(group, name, outcome)]) < 400:
                    examples[(group, name, outcome)].append(
                        f"{key} {row['name']} -> {sorted(cell['targets'])[:3] or sorted(cell['externals'])[:2]}")
                if not row["targets"]:
                    continue
                mine = set(cell["targets"] - cell["arguments"]) if cell else set()
                theirs = set(row["targets"])
                if not mine:
                    relation[name][f"source {outcome}"] += 1
                    continue
                kind = "same" if mine == theirs else "source within index" if mine < theirs else \
                    "index within source" if theirs < mine else "overlap" if mine & theirs else "disjoint"
                relation[name][kind] += 1
                if kind in ("disjoint", "overlap"):
                    disagreements[name].append({"site": key, "name": row["name"], "kind": kind,
                                                "index": sorted(theirs), "index_chains": row["chains"],
                                                "source": sorted(mine)})
    rng = random.Random(SEED)
    rows_out = []  # every call the index leaves without a project target, with what each source gives there
    for key, rows in index.items():
        for row in rows:
            if row["targets"]:
                continue
            entry = {"site": key, "name": row["name"], "group": f"{row['language']} | {row['group']}"}
            for name, found in sites.items():
                cell = found.get(key)
                if cell:
                    entry[name] = {"outcome": _outcome(cell), "targets": sorted(cell["targets"])[:6],
                                   "arguments": sorted(cell["arguments"])[:6],
                                   "externals": sorted(cell["externals"])[:3]}
            rows_out.append(entry)
    out = {"table": {group: {name: dict(counter) for name, counter in by.items()} for group, by in sorted(table.items())},
           "examples": {f"{g} | {n} | {o}": rng.sample(items, min(3, len(items))) for (g, n, o), items in
                        sorted(examples.items())},
           "relation_where_index_has_target": {name: dict(counter) for name, counter in relation.items()},
           "disagreements": dict(disagreements), "rows": rows_out}
    # A source's site no snapshot call names: a different site rule, or a call the snapshot does not record.
    out["source_sites_outside_snapshot"] = {
        name: {"sites": len(found), "outside": len(missing := sorted(key for key in found if key not in index)),
               "examples": rng.sample(missing, min(8, len(missing)))} for name, found in sites.items()}
    return out


def jelly_sample(index: dict, snapshot, edges: list, group: str, size: int = 20) -> list:
    """Jelly edges at sites the index leaves as `group`, `size` of them at random (seed), for reading."""
    found = source_sites(edges, snapshot)
    pool = []
    for key, rows in sorted(index.items()):
        if any(row["group"] == group for row in rows) and key in found:
            cell = found[key]
            for target in sorted(cell["targets"]):
                pool.append({"site": key, "name": rows[0]["name"], "target": target,
                             "argument": target in cell["arguments"]})
            for package in sorted(cell["externals"]):
                pool.append({"site": key, "name": rows[0]["name"], "external": package})
    return random.Random(SEED).sample(pool, min(size, len(pool))) if pool else []


def hand(index: dict, snapshot, sources: dict) -> list:
    sites = {name: source_sites(edges, snapshot) for name, edges in sources.items()}
    by_line = collections.defaultdict(list)
    for key, rows in index.items():
        if not key.startswith("no-position"):
            by_line[key.rsplit(":", 1)[0]] += [(key, row) for row in rows]
    out = []
    for rel, line, name, expected in HAND:
        found = [(key, row) for key, row in by_line.get(f"{rel}:{line}", ()) if row["name"].rsplit(".", 1)[-1] == name]
        kind, _, want = expected.partition(" ")
        if not found:
            out.append({"site": f"{rel}:{line} {name}", "expected": expected, "error": "no snapshot call"})
            continue
        key, row = found[0]

        def right(targets: set, externals: set) -> bool:
            lines = {(target.split("::")[0], target.rsplit("@", 1)[-1].split(":")[0]) for target in targets}
            if kind == "decl":
                return lines == {tuple(item.rsplit(":", 1)) for item in want.split(",")}
            if kind == "external":
                return not targets and any(part in package for part in want.split("|") for package in externals)
            return not targets
        entry = {"site": f"{key} {name}", "expected": expected,
                 "index": {"group": row["group"], "targets": row["targets"], "externals": row["externals"],
                           "right": right(set(row["targets"]), set(row["externals"]))}}
        for source, found_sites in sites.items():
            cell = found_sites.get(key) or {"targets": set(), "externals": set(), "other": set()}
            entry[source] = {"targets": sorted(cell["targets"]), "arguments": sorted(cell.get("arguments", ())), "externals": sorted(cell["externals"]),
                             "other": sorted(cell["other"])[:3], "right": right(cell["targets"], cell["externals"])}
        out.append(entry)
    return out


# --- the @types/* packages a project's dependencies lack ------------------------------------------------------

def missing_types(mirror: Path) -> list[str]:
    """`@types/<name>` for each declared dependency installed without its own types and without that package."""
    manifest = json.loads((mirror / "package.json").read_text(encoding="utf-8"))
    names = sorted({*manifest.get("dependencies", {}), *manifest.get("devDependencies", {})})
    modules, out = mirror / "node_modules", []
    for name in names:
        if name.startswith("@types/"):
            continue
        package = modules / name
        try:
            data = json.loads((package / "package.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        typed = data.get("types") or data.get("typings") or (package / "index.d.ts").is_file() or \
            "types" in json.dumps(data.get("exports") or {})
        mangled = "@types/" + (name[1:].replace("/", "__") if name.startswith("@") else name)
        if not typed and not (modules / mangled).exists():
            out.append(mangled)
    return out


def install_types(mirror: Path, work: Path) -> dict:
    """Install the missing `@types/*` that exist on npm (latest) beside the mirror and link in what it lacks."""
    import shutil
    import subprocess
    npm = shutil.which("npm", path=f"{ts_compiler.NODE}{os.pathsep}{os.environ.get('PATH', '')}") or "npm"
    wanted = missing_types(mirror)
    found = {}
    for name in wanted:
        done = subprocess.run([npm, "view", name, "version"], capture_output=True, text=True, timeout=120)
        if done.returncode == 0 and done.stdout.strip():
            found[name] = done.stdout.strip().splitlines()[-1].strip().strip("'")
    extra = work / "types-extra"
    extra.mkdir(parents=True, exist_ok=True)
    (extra / "package.json").write_text('{"private":true}\n', encoding="utf-8")
    result = {"wanted": wanted, "installed": found}
    if found:
        done = subprocess.run([npm, "install", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error",
                               *[f"{name}@{version}" for name, version in found.items()]],
                              cwd=extra, capture_output=True, text=True, timeout=1800)
        result["returncode"], result["stderr"] = done.returncode, done.stderr[-1500:]
        linked = []
        for package in sorted((extra / "node_modules").glob("*")):
            items = sorted(package.glob("*")) if package.name.startswith("@") else [package]
            for item in items:
                destination = mirror / "node_modules" / item.relative_to(extra / "node_modules")
                if item.is_dir() and not destination.exists() and item.name != ".bin":
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(item, destination, symlinks=True)
                    linked.append(item.relative_to(extra / "node_modules").as_posix())
        result["linked"] = linked
    return result


# --- the run ------------------------------------------------------------------------------------------------

def _store(path: Path, edges: list) -> None:
    import gzip
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for edge in edges:
            handle.write(json.dumps(edge) + "\n")


def _load(path: Path) -> list:
    import gzip
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def run_all(project: Path, work: Path, manifest: Path, index_paths: list, files: list[str] | None,
            jelly_timeout: int, keep: Path | None, with_types: bool, reuse: bool = False) -> dict:
    """Both sources and the comparison; with `reuse`, the edges an earlier run kept in `keep` instead."""
    import time
    result, sources, timing = {"code": scip_graph.code_sha256()}, {}, {}
    begun = time.time()
    index, extra = index_sites(manifest, index_paths)
    snapshot = extra["snapshot"]
    timing["index graph"] = round(time.time() - begun, 1)
    result["index_groups"] = extra["counts"]
    if files is None:
        files = sorted({snapshot.checkout.get(rel, rel) for rel, language in snapshot.languages.items()
                        if language in LANGUAGES and rel in snapshot.inventory})
    def typed():
        result["types"] = install_types(work / "mirror-strong-js", work)
        return ts_compiler.analyze(project, work, files, label="types")
    # Jelly with every package last: the run most likely to exhaust memory leaves the others measured.
    runs = [("ts", lambda: ts_compiler.analyze(project, work, files)),
            ("jelly-own", lambda: js_jelly.analyze(project, work, files, dependencies=False, timeout=jelly_timeout)),
            *([("ts-types", typed)] if with_types else []),
            ("jelly-deps", lambda: js_jelly.analyze(project, work, files, dependencies=True, timeout=jelly_timeout))]
    for name, call in runs:
        begun = time.time()
        if reuse and keep is not None and (keep / f"{name}.jsonl.gz").is_file():
            sources[name] = _load(keep / f"{name}.jsonl.gz")
            result[name] = {"reused": str(keep / f"{name}.jsonl.gz")}
            continue
        try:
            found = call()
        except Exception:
            import traceback
            found = {"edges": [], "error": traceback.format_exc()[-3000:]}
        timing[name] = round(time.time() - begun, 1)
        sources[name] = found.pop("edges")
        result[name] = found
        if keep is not None:
            _store(keep / f"{name}.jsonl.gz", sources[name])
        print(name, timing[name], len(sources[name]), found.get("engine"), flush=True)
    begun = time.time()
    result["compare"] = compare(index, snapshot, sources)
    rows = result["compare"].pop("rows")
    if keep is not None:
        _store(keep / "sites.jsonl.gz", rows)
    result["jelly_sample"] = {name: jelly_sample(index, snapshot, sources[name], "hole: no-occurrence / unknown-receiver")
                              for name in ("jelly-deps", "jelly-own")}
    result["hand"] = hand(index, snapshot, sources)
    result["hand_score"] = {name: sum(1 for row in result["hand"] if row.get(name, {}).get("right"))
                            for name in ("index", *sources)}
    timing["compare"] = round(time.time() - begun, 1)
    result["seconds"] = timing
    return result


def strong_case(name: str, case: dict, label: str = "", jelly_timeout: int = 1200, reuse: str = "") -> dict:
    """One case; with `reuse` (a stem), the comparison again over the edges that run kept, engines not rerun."""
    import shutil
    import time
    print("code", scip_graph.code_sha256(), flush=True)
    started = time.time()
    work = Path("/work") / name
    shutil.rmtree(work, ignore_errors=True)
    kept = Path("/results") / TAG / "scip-inputs" / name
    target = _source(work / "src", case, None)
    manifest = work / "snapshot/manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(kept / "manifest.sqlite", manifest)
    inputs = json.loads((kept / "inputs.json").read_text(encoding="utf-8"))
    index_paths = [(kept / Path(path).name, prefix) for path, prefix in
                   inputs["indexers"]["typescript"]["indexes"]]
    stem = f"{name}-{label}" if label else name
    keep = Path("/results") / TAG / "strong-js" / (reuse or stem)
    result = run_all(target, work / "strong", manifest, index_paths, None, jelly_timeout, keep, True, bool(reuse))
    result.update({"case": name, "commit": case["commit"], "container_seconds": round(time.time() - started, 1)})
    destination = Path("/results") / TAG / f"strong-js-{stem}.json"
    destination.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=sorted) + "\n", encoding="utf-8")
    volume.commit()
    return {"seconds": result["container_seconds"]}


if modal is not None:
    strong_case = app.function(cpu=2.0, memory=(4096, 32768), timeout=3 * 3600,
                               volumes={"/results": volume})(strong_case)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "local"))
    parser.add_argument("--case", default="tududi")
    parser.add_argument("--label", default="")
    parser.add_argument("--jelly-timeout", type=int, default=1200)
    parser.add_argument("--reuse", default="", help="compare again over the edges kept under this stem")
    parser.add_argument("--project")
    parser.add_argument("--manifest")
    parser.add_argument("--index")
    parser.add_argument("--work")
    parser.add_argument("--out")
    args = parser.parse_args()
    stem = f"{args.case}-{args.label}" if args.label else args.case
    if args.command == "spawn":
        function = modal.Function.from_name("daodan-strong-js", "strong_case")
        print(args.case, function.spawn(args.case, CASES[args.case], args.label, args.jelly_timeout, args.reuse).object_id)
    elif args.command == "fetch":
        RESULTS.mkdir(parents=True, exist_ok=True)
        data = b"".join(volume.read_file(f"{TAG}/strong-js-{stem}.json"))
        (RESULTS / f"strong-js-{stem}.json").write_bytes(data.replace(b"\r\n", b"\n"))
        print(stem, len(data))
    else:
        value = run_all(Path(args.project), Path(args.work), Path(args.manifest), [(args.index, "")], None,
                        args.jelly_timeout, None, False)
        text = json.dumps(value, indent=1, ensure_ascii=False, default=sorted)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
