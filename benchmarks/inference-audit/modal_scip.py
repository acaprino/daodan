"""SCIP versus engines on Modal, and the whole graph each index states. No model.

Road A is the product's engine pass (`resolve_edges.py --pass`); road B is a whole-project SCIP index of an
existing indexer read completely by `scip_graph.py`, with the adapter of its language (`adapters/go.py`,
`adapters/rust.py`, `adapters/typescript.py`): every chain the index states followed to its end. One
container per case: the snapshot as `modal_audit.py` builds it and road A (rerun, or the per-call answers a
labelled audit run left on the volume), kept under `scip-inputs/<case>` with the indexes; the adapters'
indexers (rerun with `--reindex`, the kept indexes otherwise); then the graph of each language
(`scip-inputs/<case>/graph-<language>.json.gz`), its counts, the comparison with road A and the hand checks.

    modal deploy benchmarks/inference-audit/modal_scip.py
    python benchmarks/inference-audit/modal_scip.py spawn --cases chi,semver,tududi [--reindex] [--label L]
    python benchmarks/inference-audit/modal_scip.py fetch --cases chi,semver,tududi [--label L]

`python modal_scip.py join --manifest M --index I[=prefix] [--answers A] --out O` runs the join alone, locally.
"""
from __future__ import annotations

import collections
import importlib
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import scip_graph  # noqa: E402
from adapters import go, typescript  # noqa: E402
from modal_audit import CASES, _run, _source  # noqa: E402

# Road A's per-call answers kept by a labelled audit run at the same commit and plugin: reused, never rerun.
REUSE = {"tududi": "r1"}
NODE = ("v22.23.4", "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce")
ADAPTERS = {"go": "go", "rust": "rust", "javascript": "typescript", "typescript": "typescript"}
SUFFIXES = {"go": (".go",), "rust": (".rs",), "typescript": typescript.SUFFIXES}
EXAMPLES = 20
# Fifteen call sites per language picked at random over every call of the checkout (seed 20261113) and read in
# the source, the expected end written before any graph existed: `decl FILE:LINE` (the declaration that starts
# there), `external PACKAGE[|PACKAGE]` (a substring of `manager package@version`), `value` (a project value
# with no stated alias) or `none` (no function of the project: a builtin, a value of type any, a state setter).
HAND = {
    "chi": [
        ("_examples/fileserver/main.go", 43, "ListenAndServe", "external golang/go"),
        ("_examples/hello-world/main.go", 13, "Use", "decl mux.go:100"),
        ("_examples/rest/main.go", 143, "WithContext", "external golang/go"),
        ("_examples/todos-resource/main.go", 15, "NewRouter", "decl chi.go:62"),
        ("context.go", 155, "TrimSuffix", "external golang/go"),
        ("middleware/client_ip.go", 62, "mustParsePrefixes", "decl middleware/client_ip.go:278"),
        ("middleware/client_ip_bench_test.go", 47, "Join", "external golang/go"),
        ("middleware/client_ip_test.go", 353, "runChain", "decl middleware/client_ip_test.go:845"),
        ("middleware/recoverer.go", 32, "GetLogEntry", "decl middleware/logger.go:75"),
        ("middleware/sunset.go", 34, "ServeHTTP", "external golang/go"),  # net/http Handler, a parameter
        ("middleware/throttle_test.go", 147, "Use", "decl mux.go:100"),
        ("mux_test.go", 428, "len", "none"),
        ("mux_test.go", 1982, "Write", "external golang/go"),  # net/http ResponseWriter, a parameter
        ("tree.go", 416, "len", "none"),
        ("tree.go", 609, "len", "none"),
    ],
    "semver": [
        ("benches/parse.rs", 12, "black_box", "external rust-lang/rust"),
        ("build.rs", 22, "Some", "external rust-lang/rust"),
        ("fuzz/sort_version.rs", 16, "ok", "external rust-lang/rust"),
        ("src/display.rs", 8, "is_empty", "decl src/lib.rs:548"),  # Prerelease::is_empty
        ("src/display.rs", 98, "is_empty", "decl src/lib.rs:548"),
        ("src/display.rs", 151, "write_char", "external rust-lang/rust"),
        ("src/identifier.rs", 196, "ptr_as_str", "decl src/identifier.rs:397"),
        ("src/identifier.rs", 384, "new_unchecked", "external rust-lang/rust"),  # NonZeroUsize
        ("src/identifier.rs", 398, "repr_to_ptr", "decl src/identifier.rs:298"),
        ("src/parse.rs", 48, "strip_prefix", "external rust-lang/rust"),
        ("src/parse.rs", 179, "next", "external rust-lang/rust"),
        ("src/parse.rs", 217, "Ok", "external rust-lang/rust"),
        ("tests/test_version.rs", 48, "version_err", "decl tests/util/mod.rs:12"),
        ("tests/test_version.rs", 179, "version", "decl tests/util/mod.rs:7"),
        ("tests/test_version_req.rs", 292, "assert_match_none", "decl tests/test_version_req.rs:30"),
    ],
    "tududi": [
        ("backend/migrations/archive/20251023000001-add-unique-constraint-tags.js", 162, "addIndex", "value"),
        ("backend/migrations/archive/20261024100000-create-webhooks.js", 162, "addIndexOnce",
         "decl backend/migrations/archive/20261024100000-create-webhooks.js:5"),
        ("backend/modules/caldav/icalendar/vtodo-parser.js", 189, "toJSDate", "external ical.js"),
        ("backend/modules/caldav/services/safe-request.js", 191, "AppError", "decl backend/shared/errors/AppError.js:7"),
        ("backend/modules/daily-plan/routes.js", 32, "put", "external express"),
        ("backend/modules/oidc/configService.js", 95, "require", "external @types/node"),
        ("backend/modules/spreadsheets/analyze.js", 750, "key", "decl backend/modules/spreadsheets/analyze.js:28"),
        ("backend/modules/tasks/routes.js", 654, "findByIdAndUser", "decl backend/modules/tasks/repository.js:13"),
        ("backend/modules/tasks/taskReminderService.js", 3, "require", "external @types/node"),
        ("backend/tests/integration/admin-users-cascade.test.js", 16, "require", "external @types/node"),
        ("backend/tests/integration/recurring-tasks.test.js", 365, "create", "external sequelize"),
        ("backend/tests/integration/spreadsheets-formats.test.js", 492, "map", "none"),
        ("backend/tests/unit/middleware/rateLimitStore.test.js", 19, "beforeAll", "external @types/jest"),
        ("backend/tests/unit/modules/tasks/recurringTaskService.test.js", 677, "expect", "external @types/jest"),
        ("backend/utils/timezone-utils.js", 69, "getDayBoundsInUTC", "decl backend/utils/timezone-utils.js:53"),
        ("e2e/tests/notes-editor.spec.ts", 106, "log", "external typescript|@types/node"),
        ("frontend/Layout.tsx", 216, "setSelectedArea", "none"),
        ("frontend/__tests__/Notes.staleCache.test.tsx", 80, "fn", "external @types/jest"),
        ("frontend/components/Admin/AdminUsersPage.tsx", 1353, "setRolesError", "none"),
        ("frontend/components/Admin/__tests__/AdminUserStatusTable.test.tsx", 87, "getAllByRole", "external @testing-library"),
        ("frontend/components/Admin/__tests__/AdminUsersPage.test.tsx", 216, "toBeEnabled", "external jest"),
        ("frontend/components/Billing/__tests__/UpgradeModal.test.tsx", 75, "getByTestId", "external @testing-library"),
        ("frontend/components/Calendar.tsx", 250, "Date", "external typescript"),
        ("frontend/components/DailyPlan/NowCard.tsx", 75, "push", "external typescript"),
        ("frontend/components/DailyPlan/PlanMyDay.tsx", 797, "useSensor", "external @dnd-kit"),
        ("frontend/components/Inbox/__tests__/QuickCaptureInput.focus.test.tsx", 88, "slice", "external typescript"),
        ("frontend/components/Shared/ShareModal.tsx", 308, "trim", "external typescript"),
        ("frontend/components/Shared/__tests__/MarkdownRenderer.mermaid.test.tsx", 78, "queryByTestId",
         "external @testing-library"),
        ("frontend/components/Task/TaskDetails/__tests__/TaskDetailsHeader.test.tsx", 6, "mock", "external @types/jest"),
        ("frontend/utils/dailyPlanService.ts", 311, "map", "external typescript"),
    ],
}


def _image():
    import resolve_edges as rx
    go_asset, go_sha = rx.GO_ASSETS["linux-x64"]
    ra_asset, ra_sha = rx.RUST_ANALYZER_ASSETS["linux-x64"]
    node_version, node_sha = NODE
    node = f"node-{node_version}-linux-x64.tar.xz"
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "curl", "ca-certificates", "nodejs", "npm", "unzip", "xz-utils")
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(
            f"curl -fsSL https://nodejs.org/dist/{node_version}/{node} -o /tmp/{node}",
            f"echo '{node_sha}  /tmp/{node}' | sha256sum -c -",
            f"mkdir -p /opt/node && tar -xJf /tmp/{node} -C /opt/node --strip-components=1 && rm /tmp/{node}",
            f"PATH=/opt/node/bin:$PATH npm install -g --ignore-scripts --no-audit --no-fund "
            f"@sourcegraph/scip-typescript@{typescript.VERSION}",
            f"curl -fsSL https://go.dev/dl/{go_asset} -o /tmp/{go_asset}",
            f"echo '{go_sha}  /tmp/{go_asset}' | sha256sum -c -",
            f"tar -xzf /tmp/{go_asset} -C /opt && rm /tmp/{go_asset}",
            f"GOBIN=/opt/scip/bin GOPATH=/tmp/gopath GOFLAGS= GOTOOLCHAIN=local /opt/go/bin/go install "
            f"github.com/scip-code/scip-go/cmd/scip-go@{go.VERSION} && rm -rf /tmp/gopath",
            f"curl -fsSL https://github.com/rust-lang/rust-analyzer/releases/download/{rx.RUST_ANALYZER_RELEASE}/"
            f"rust-analyzer-{ra_asset} -o /tmp/ra.gz",
            f"echo '{ra_sha}  /tmp/ra.gz' | sha256sum -c -",
            "gunzip -c /tmp/ra.gz > /opt/scip/bin/rust-analyzer && chmod 755 /opt/scip/bin/rust-analyzer && rm /tmp/ra.gz",
        )
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "probe.py" if LOCAL else Path("/audit/probe.py"), "/audit/probe.py")
        .add_local_file(HERE / "scip_graph.py" if LOCAL else Path("/audit/scip_graph.py"), "/audit/scip_graph.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-scip-audit", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _adapter(language: str):
    return importlib.import_module(f"adapters.{ADAPTERS[language]}")


def _sample(items: list, size: int = EXAMPLES) -> list:
    if len(items) <= size:
        return items
    step = len(items) / size
    return [items[int(i * step)] for i in range(size)]


def _road_b(reference: dict) -> tuple[str, set, str, scip_graph.End | None]:
    """(class, project targets, detail, shortest end to a target) of road B at one reference."""
    ends = reference["ends"]
    callable_ends = [end for end in ends if end.cls == "project-callable" and end.target]
    if callable_ends:
        return "project-declaration", {end.target for end in callable_ends}, "", \
            min(callable_ends, key=lambda end: len(end.chain))
    if reference["hole"]:
        return reference["hole"], set(), reference["hole"], None
    external = next((end for end in ends if end.cls == "external"), None)
    if external is not None:
        return "external", set(), external.detail, None
    value = next((end for end in ends if end.cls == "project-value"), None)
    return ("project-value", set(), value.detail, None) if value else ("none", set(), "no end", None)


def _road_a(answer, lexical_target):
    """The graph the product keeps: the engine's answer wins, the lexical target stays otherwise."""
    if answer is not None:
        verdict, target_id = answer[0], answer[1]
        if verdict.startswith("edge-") and target_id:
            return "project-declaration", target_id, "engine"
        if verdict == "external-definition":
            return "external", None, "engine"
    if lexical_target:
        return "project-declaration", lexical_target, "lexical"
    if answer is None:
        return "not-asked", None, "-"
    if answer[0] in ("project-not-a-symbol", "ambiguous-target", "binding"):
        return "project-other", None, answer[0]
    return "none", None, answer[0]


def _chain(end: scip_graph.End) -> str:
    return " -> ".join([*end.chain, end.target or f"{end.cls} {end.detail}"[:120]])


def _compare(references: dict, answers: dict) -> dict:
    """Road B beside road A, per reference kind, with examples."""
    counters = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    mismatched = 0
    for identity, reference in references.items():
        kind, site = reference["kind"], f"{reference['site']} {reference['name']}"
        b_cls, b_targets, b_detail, best = _road_b(reference)
        implemented = {end.target for end in reference["ends"] if end.cls == "project-callable"
                       and "implementation" in end.chain}
        counters[f"b {kind}"][b_cls if b_cls != "project-value" else f"project-value {b_detail}"] += 1
        if best is not None:
            hops = len(best.chain)
            counters[f"hops {kind}"][str(hops) if hops < 3 else "3+"] += 1
            counters[f"hop kinds {kind}"]["+".join(best.chain) or "direct"] += 1
            if hops and kind == "call":
                examples[f"chain {'+'.join(best.chain)}"].append(f"{site}: {_chain(best)}")
        if b_cls == "external":
            counters[f"external packages {kind}"][b_detail] += 1
        if implemented:
            counters["implementations"][f"{kind} with implementations"] += 1
            counters["implementations"][f"{kind} implementations listed"] += len(implemented)
        if kind == "read":
            lexical = reference["lexical"] if reference["resolution"] == "resolved" else None
            if lexical and b_targets:
                counters["reads vs lexical"]["same" if lexical in b_targets else "different"] += 1
            elif lexical:
                counters["reads vs lexical"]["only lexical"] += 1
            elif b_targets:
                counters["reads vs lexical"]["only B"] += 1
            else:
                counters["reads vs lexical"]["neither"] += 1
            continue
        answer = answers.get(identity)
        if answer is not None and (answer[2] != reference["site"].rsplit(":", 1)[0]):
            mismatched += 1
        lexical = reference["lexical"] if reference["resolution"] == "resolved" else None
        a_cls, a_target, a_source = _road_a(answer, lexical)
        counters["a"][a_cls] += 1
        if a_target:
            counters["a target source"][a_source] += 1
        reached = "through an implementation only" if b_targets and b_targets <= implemented else \
            "direct or alias" if b_targets else ""
        counters["matrix"][f"A {a_cls} | B {b_cls}{' (' + reached + ')' if reached else ''}"] += 1
        if a_target and b_targets:
            cell = "same project target" if a_target in b_targets else "different project target"
            if a_target in implemented and a_target not in b_targets - implemented:
                counters["implementations"]["A matched only through an implementation"] += 1
        elif a_target:
            cell = "only A has a project target"
        elif b_targets:
            cell = "only B has a project target"
        elif a_cls == "external" and b_cls == "external":
            cell = "both external"
        else:
            cell = f"mixed: A {a_cls}, B {b_cls}"
        counters["cells"][cell] += 1
        detail = f"{site} | A {a_cls} {a_target or a_source} | B {b_cls} {_chain(best) if best else b_detail}"
        if cell == "only A has a project target":
            counters["only A by B"][f"{b_cls} {b_detail}"[:80]] += 1
            examples[f"only A (B {b_cls})"].append(detail)
        elif cell in ("different project target", "only B has a project target"):
            examples[f"{cell} ({reached})"].append(detail)
    out = {key: dict(value.most_common(40)) for key, value in sorted(counters.items())}
    out["examples"] = {key: _sample(items) for key, items in sorted(examples.items())}
    out["answer_file_mismatches"] = mismatched
    return out


def _hand(checks: list, references: dict, answers: dict) -> list:
    """Each hand-read call site beside what road B and road A give there."""
    by_site = collections.defaultdict(list)
    for identity, reference in references.items():
        if reference["kind"] == "call":
            by_site[reference["site"]].append((identity, reference))
    rows = []
    for rel, line, name, expected in checks:
        found = [(identity, reference) for identity, reference in by_site.get(f"{rel}:{line}", ())
                 if reference["name"].rsplit(".", 1)[-1] == name]
        if not found:
            rows.append({"site": f"{rel}:{line} {name}", "expected": expected, "b": "no snapshot reference",
                         "b_right": False, "a_right": False})
            continue
        identity, reference = found[0]
        b_cls, b_targets, b_detail, _best = _road_b(reference)
        externals = sorted({end.detail for end in reference["ends"] if end.cls == "external"})
        lexical = reference["lexical"] if reference["resolution"] == "resolved" else None
        a_cls, a_target, _source = _road_a(answers.get(identity), lexical)
        kind, _, want = expected.partition(" ")

        def right(targets, cls, packages):
            if kind == "decl":
                return any(target.split("::")[0] == want.rsplit(":", 1)[0] and
                           target.rsplit("@", 1)[-1].split(":")[0] == want.rsplit(":", 1)[1] for target in targets)
            if kind == "external":
                return any(part in package for part in want.split("|") for package in packages)
            if kind == "value":
                return not targets and cls == "project-value"
            return not targets

        rows.append({"site": f"{rel}:{line} {name}", "expected": expected, "b": b_cls, "b_targets": sorted(b_targets),
                     "b_detail": b_detail, "b_externals": externals,
                     "b_chains": [_chain(end) for end in reference["ends"]][:6],
                     "b_right": right(b_targets, b_cls, externals), "a": a_cls, "a_target": a_target,
                     "a_right": right({a_target} if a_target else set(), a_cls, ["engine"] if a_cls == "external" else [])
                     if kind != "external" else a_cls == "external"})
    return rows


def join(manifest: Path, indexes: list, answers_path: Path | None, indexers: dict | None = None,
         hand: list = (), graph_dir: Path | None = None) -> dict:
    """The graph of each language of the snapshot, its counts, road A beside road B, and the hand checks."""
    import gzip
    import sqlite3
    import time
    answers = {}
    if answers_path is not None and Path(answers_path).is_file():
        db = sqlite3.connect(answers_path)
        for row in db.execute("SELECT reference_id, verdict, target_id, file, line, column FROM answers"):
            answers[row[0]] = row[1:]
        db.close()
    with scip_graph.Snapshot(manifest) as snapshot:
        index = scip_graph.Index(snapshot.root)
        for path, prefix in indexes:
            index.load(Path(path), prefix)
        languages = sorted({language for rel, language in snapshot.languages.items()
                            if language in ADAPTERS and rel in snapshot.inventory})
        hops, timing = {}, {}
        for name in sorted({ADAPTERS[language] for language in languages}):
            begun = time.time()
            hops.update(_adapter(next(lang for lang in languages if ADAPTERS[lang] == name)).hops(index))
            timing[f"hops {name}"] = round(time.time() - begun, 1)
        traversal = scip_graph.Traversal(index, snapshot, hops)
        out = {"index_tools": index.tools, "documents_written_twice": sum(1 for n in index.repeated.values() if n > 1),
               "unknown_fields": dict(index.unknown), "hops": len(hops), "answers": len(answers), "languages": {}}
        references_all = {}
        for language in languages:
            begun = time.time()
            adapter = _adapter(language)
            rels = sorted(snapshot.checkout[rel] for rel in snapshot.inventory
                          if snapshot.languages.get(rel) == language and rel in snapshot.checkout)
            absent = [rel for rel in rels if rel not in index.documents]
            reasons = adapter.missing(index, absent) if hasattr(adapter, "missing") and absent else {}
            info = (indexers or {}).get(ADAPTERS[language], {}).get("indexer") or {}
            graph, references = scip_graph.build(index, snapshot, language, hops, info, reasons, traversal)
            references_all.update(references)
            out["languages"][language] = {"graph": scip_graph.report(graph), "road_a": _compare(references, answers)}
            if graph_dir is not None:
                Path(graph_dir).mkdir(parents=True, exist_ok=True)
                with gzip.open(Path(graph_dir) / f"graph-{language}.json.gz", "wt", encoding="utf-8") as handle:
                    json.dump(graph, handle)
            timing[f"graph {language}"] = round(time.time() - begun, 1)
            print("join", timing, flush=True)
        out["hand"] = _hand(list(hand), references_all, answers)
        out["hand_score"] = {"checks": len(out["hand"]), "b_right": sum(row["b_right"] for row in out["hand"]),
                             "a_right": sum(row["a_right"] for row in out["hand"])}
        out["seconds"] = timing
        out["symbols_walked"] = len(traversal.memo)
    return out


def _inputs(name: str, case: dict, target: Path, work: Path, manifest: Path) -> tuple[dict, Path]:
    """The snapshot and road A's per-call answers of a case, built in the container."""
    import shutil
    import time
    started = time.time()
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest),
          "--no-engine", "--no-index"])
    result = {"snapshot_seconds": round(time.time() - started, 1)}
    import resolve_edges as rx
    reuse = REUSE.get(name)
    if reuse:
        answers = work / "answers.sqlite"
        shutil.copyfile(Path("/results") / TAG / f"answers-{name}-{reuse}.sqlite", answers)
        audit = json.loads((Path("/results") / TAG / f"audit-{name}-{reuse}.json").read_text(encoding="utf-8"))
        result["road_a"] = {"source": f"answers-{name}-{reuse}.sqlite", "seconds": audit.get("pass_seconds"),
                            "peak_rss_mb": None, "coverage": audit.get("graph_use", {}).get("coverage")}
    else:
        report = work / "engine-report.json"
        run = scip_graph.measured([sys.executable, f"{SCRIPTS}/resolve_edges.py", str(manifest), "--pass",
                                   "--report-out", str(report)], SCRIPTS, None, 3 * 3600)
        answers = rx.default_answers_path(manifest)
        result["road_a"] = {"source": "rerun", "seconds": run["seconds"], "peak_rss_mb": run["peak_mb"],
                            "returncode": run["returncode"], "stderr_tail": run["stderr_tail"][-800:]}
        try:
            summary = json.loads(report.read_text(encoding="utf-8"))
            result["road_a"]["coverage"] = {name: engine.get("resolution", {}).get("by_language")
                                            for name, engine in (summary.get("engines") or {}).items()}
        except (OSError, ValueError) as error:
            result["road_a"]["coverage"] = repr(error)
    return result, Path(answers)


def _indexers(target: Path, work: Path, manifest: Path) -> dict:
    """Each adapter's indexer over the checkout, for the snapshot's files of its languages."""
    import sqlite3
    connection = sqlite3.connect(manifest)
    coverage = connection.execute("SELECT file, language FROM sem_coverage WHERE status='ast'").fetchall()
    connection.close()
    out = {}
    for name in sorted({ADAPTERS[language] for _, language in coverage if language in ADAPTERS}):
        files = sorted(rel for rel, language in coverage if ADAPTERS.get(language) == name
                       and rel.endswith(SUFFIXES[name]))
        try:
            out[name] = importlib.import_module(f"adapters.{name}").index(target, work, files)
        except Exception:
            import traceback
            out[name] = {"error": traceback.format_exc()[-3000:], "indexes": []}
    return out


def _kept_indexers(kept: Path, inputs: dict) -> dict:
    """The indexes an earlier run kept, in the adapters' shape (older runs named them by tool)."""
    tools = {"scip-go": "go", "rust-analyzer": "rust", "scip-typescript": "typescript"}
    out = {}
    for key, info in (inputs.get("indexers") or {}).items():
        name = tools.get(key, key)
        indexer = info.get("indexer") if isinstance(info.get("indexer"), dict) else {
            "name": key, "version": info.get("version"), "seconds": info.get("seconds"),
            "peak_mb": info.get("peak_rss_mb")}
        out[name] = {**info, "indexer": indexer,
                     "indexes": [[str(kept / Path(path).name), prefix] for path, prefix in info.get("indexes", ())]}
    return out


@app.function(cpu=4, memory=16384, timeout=4 * 3600, volumes={"/results": volume})
def scip_case(name: str, case: dict, label: str = "", reindex: bool = False) -> dict:
    """One case: snapshot and road A from the volume when an earlier run kept them, built and kept otherwise;
    the indexers (again with `reindex`, from the volume otherwise; kept either way); the graphs and the join."""
    import shutil
    import time
    print("code", scip_graph.code_sha256(), flush=True)  # compared with the checkout before trusting the run
    started = time.time()
    work = Path("/work") / name  # the kept snapshot binds its sources here
    shutil.rmtree(work, ignore_errors=True)  # a warm container may have run this case before
    kept = Path("/results") / TAG / "scip-inputs" / name
    target = _source(work / "src", case, None)  # the checkout the snapshot verifies its sources against
    manifest = work / "snapshot/manifest.sqlite"
    answers = work / "answers.sqlite"
    if (kept / "inputs.json").is_file():
        manifest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(kept / "manifest.sqlite", manifest)
        if (kept / "answers.sqlite").is_file():
            shutil.copyfile(kept / "answers.sqlite", answers)
        inputs = json.loads((kept / "inputs.json").read_text(encoding="utf-8"))
        result = {"case": name, "commit": case["commit"], "inputs": f"kept, {kept}", **inputs}
    else:
        inputs, road_a_answers = _inputs(name, case, target, work, manifest)
        result = {"case": name, "commit": case["commit"], "inputs": f"built, kept in {kept}", **inputs}
        kept.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(manifest, kept / "manifest.sqlite")
        if road_a_answers.is_file():
            shutil.copyfile(road_a_answers, kept / "answers.sqlite")
            if road_a_answers.resolve() != answers.resolve():
                shutil.copyfile(road_a_answers, answers)
        reindex = True
    indexers = _kept_indexers(kept, inputs)
    if reindex:
        fresh = _indexers(target, work, manifest)
        result["reindexed"] = {}
        for adapter, info in fresh.items():
            result["reindexed"][adapter] = {"error": info.get("error"), "indexer": info.get("indexer"),
                                            "index_bytes": [run.get("index_bytes") for run in info.get("runs", [])],
                                            "kept_bytes": [Path(path).stat().st_size for path, _ in
                                                           indexers.get(adapter, {}).get("indexes", ())
                                                           if Path(path).is_file()]}
            if info.get("indexes"):  # a failed indexer leaves the kept indexes in place
                kept.mkdir(parents=True, exist_ok=True)
                for path, _prefix in info["indexes"]:
                    shutil.copyfile(path, kept / Path(path).name)
                info["indexes"] = [[str(kept / Path(path).name), prefix] for path, prefix in info["indexes"]]
                indexers[adapter] = info
        inputs = {**{key: value for key, value in inputs.items() if key != "indexers"}, "indexers": indexers}
        (kept / "inputs.json").write_text(json.dumps(inputs, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        volume.commit()
    result["indexers"], result["code"] = indexers, scip_graph.code_sha256()
    indexes = [(Path(path), prefix) for info in indexers.values() for path, prefix in info.get("indexes", ())]
    begun = time.time()
    try:
        result["join"] = join(manifest, indexes, answers if answers.is_file() else None, indexers, HAND.get(name, ()),
                              kept) if indexes else {"error": "no index"}
    except Exception:
        import traceback
        result["join"] = {"error": traceback.format_exc()[-3000:]}
    result["join_seconds"] = round(time.time() - begun, 1)
    result["seconds"] = round(time.time() - started, 1)
    stem = f"{name}-{label}" if label else name
    destination = Path("/results") / TAG / f"scip-{stem}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "join"))
    parser.add_argument("--cases", default="chi,semver,tududi")
    parser.add_argument("--label", default="")
    parser.add_argument("--reindex", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--index", action="append", default=[])
    parser.add_argument("--answers")
    parser.add_argument("--out")
    args = parser.parse_args()
    chosen = [c.strip() for c in args.cases.split(",") if c.strip()]
    if args.command == "spawn":
        function = modal.Function.from_name("daodan-scip-audit", "scip_case")
        for name in chosen:
            print(name, function.spawn(name, CASES[name], args.label, args.reindex).object_id)
    elif args.command == "fetch":
        RESULTS.mkdir(parents=True, exist_ok=True)
        for name in chosen:
            stem = f"{name}-{args.label}" if args.label else name
            data = b"".join(volume.read_file(f"{TAG}/scip-{stem}.json"))
            (RESULTS / f"scip-{stem}.json").write_bytes(data.replace(b"\r\n", b"\n"))
            print(name, len(data))
    else:
        value = join(Path(args.manifest), [(Path(p.split("=")[0]), p.partition("=")[2]) for p in args.index],
                     Path(args.answers) if args.answers else None,
                     graph_dir=Path(args.out).parent if args.out else None)
        text = json.dumps(value, indent=1, ensure_ascii=False, default=str)
        Path(args.out).write_text(text + "\n", encoding="utf-8") if args.out else print(text)
