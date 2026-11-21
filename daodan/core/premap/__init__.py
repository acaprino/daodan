"""The pre-map of a snapshot: what the project holds and how each unit is analysed, before any indexer.

`premap.json` (`daodan/premap/v1`) beside the manifest, in Daodan's store, never in the project; the shape is
in `references/premap.md`: the project's structure and the toolchains it declares, never the libraries its
units use (each analyzer's build tool resolves those in the container while it indexes; a source stating them
fails). A source is a thin adapter in this package (`NAME`, `VERSION`, `RANK`) that states
facts in that shape: Daodan detects nothing on its own. A reader reads files and runs nothing (`run(context)`).
A model source is a build system's own command: `commands(context)` describes it as data, a runner the caller
supplies executes it in Daodan's container, and `read(context, commands, results)` reads its output; without a
runner it is `not_run`. The readers run first: the toolchains they state go to a runner that takes `toolchains`,
which prepares them, so a model command runs on the version the project declares; the gaps of that preparation
ride on the answers (`gaps`) and are the source's. The model sources run in `SOURCES`' order, each reading what
those before it state (`Context.stated`). The join keeps one entry per fact with the sources that state it
(`tool@version`).
Where two sources give a field different values, the value of the source with precedence stays (`RANKS`: a
model command, a file reader, a scanner; between equals, the earlier in `SOURCES`) and the other goes to the
entry's `conflicts` with its source; a unit's `registries`, where some of its dependencies come from as each
source reads it, add up. What no source establishes is a gap with its class. Deterministic for the
same snapshot, source versions and command outputs.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import time

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import confinement  # noqa: E402
from build_units import normalize_pypi_name  # noqa: E402
import module_derive  # noqa: E402
import modules  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402

from premap import (autotools, bazel, cargo, cmake, compose, dockerfile, dotnet, enry, gitmodules, go, gradle,  # noqa: E402
                    jvm_files, make, maven, meson, module_graph, npm, npm_lock, npm_tests, project_files, python_build,
                    python_tests, renovate, requirements, sbt, suffix_table, tsc, uv)

SCHEMA = "daodan/premap/v1"
FILE = "premap.json"
RULE = "premap@" + SCHEMA  # the source of what the pre-map derives itself: `run` and the coverage gaps
RANKS = ("model", "reader", "scanner")
SOURCES = (module_graph, python_build, requirements, python_tests, npm_lock, npm_tests, jvm_files, project_files,
           gitmodules, autotools, enry, renovate, compose, dockerfile, go, cargo, uv, tsc, npm, cmake, meson, bazel, make,
           gradle, maven, sbt, dotnet)
IDENTITY = {  # the fields that make two entries one fact, from the strictest to the loosest
    "languages": (("language",),),
    "excluded": (("path",),),
    "units": (("root", "kind", "name", "manifest"), ("root", "kind", "name"), ("root", "kind")),
    "workspace": (("root", "tool"),),  # two build systems in one folder are two workspaces
    "toolchains": (("tool", "declared_in", "version"), ("tool", "declared_in")),
    "tests": (("root", "runner"),),  # how the tests of a folder run: the dynamic step's command
    "services": (("declared_in",),),  # a service container a CI job starts beside its steps: the dynamic step's too
    "compose": (("declared_in",),),  # a CI step that starts Docker Compose: what `compose` reads
    "ci_steps": (("declared_in", "tests"),),  # a step a CI job runs before the tests of an entry: the dynamic step's
    "docker_builds": (("dockerfile", "context"),),  # a Dockerfile's stages as BuildKit reads them (`dockerfile`)
    "packages": (("ecosystem", "name", "declared_in"),),  # declared package/image signs for the stack step
}
EXECUTES = {  # unit kinds whose model or index exists only when the build runs project code
    "gradle-project": "Gradle runs the build scripts for the model and the compile tasks the index needs",
    "maven-module": "Maven runs the build's plugins to compile the module the index reads",
    "sbt-project": "sbt compiles and runs the build definition",
    "dotnet-project": "MSBuild evaluates the project files and runs their targets",
    "msbuild-project": "MSBuild evaluates the project files and runs their targets",
    "cmake-target": "the compile commands come from cmake configure, which runs the project's CMake scripts",
    "meson-target": "the compile commands come from meson setup, which runs meson.build",
    "make-target": "the compile commands come from running make",
    "autotools-project": "the compile commands come from autoreconf, configure and make, which run its scripts",
    "bazel-target": "Bazel evaluates the BUILD files and runs the repository rules",
    "bazel-module": "Bazel evaluates the BUILD files and runs the repository rules",
    "swift-package": "SwiftPM compiles and runs Package.swift",
    "mix-project": "Mix evaluates mix.exs and expands the project's macros",
    "xcode-target": "the build settings come from xcodebuild",
}
ALSO = {"typescript": ("TSX",)}  # Linguist's other programming languages inside one of the snapshot's


class Context:
    """What a source reads: the snapshot (`store`, `inventory`, hash-verified text) and its build modules
    (`module_derive.build_graph`, in memory: no `modules.json`); for a model command's source, `stated`, the facts
    the sources that ran before it state, joined (`compose` reads the steps `renovate` reads)."""

    def __init__(self, manifest: Path, store):
        self.manifest, self.store = Path(manifest), store
        self.root = Path(store["root"])
        self.inventory = modules._Inventory(store)
        self._graph = None
        self.stated: dict = {}

    @property
    def graph(self) -> dict:
        if self._graph is None:
            self._graph = module_derive.build_graph(self.inventory)
        return self._graph


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def label(source) -> str:
    return f"{source.NAME}@{source.VERSION}"


# ---------------------------------------------------------------------- join

def _canonical(value) -> str:
    if isinstance(value, list):
        return json.dumps(sorted(_canonical(v) for v in value))
    return json.dumps(value, sort_keys=True)


def _same(facet: str, field: str, a, b) -> bool:
    # Names fold as PEP 503 does: uv prints `acme-cli` for `acme_cli`; a unit's name is compared only between
    # entries of the same root and kind.
    if (facet, field) == ("units", "name") and a and b:
        return normalize_pypi_name(a) == normalize_pypi_name(b)
    if (facet, field) in (("toolchains", "declared_in"), ("packages", "declared_in")) and a and b:
        return str(a).split("#", 1)[0] == str(b).split("#", 1)[0]
    if (facet, field) == ("packages", "name") and a and b:
        return str(a).casefold() == str(b).casefold()
    return _canonical(a) == _canonical(b)


def _set(entry: dict, facet: str, field: str, key: str | None, value, source: str) -> None:
    holder = entry["config"] if key is not None else entry
    name, where = (key, f"config.{key}") if key is not None else (field, field)
    if name not in holder:
        holder[name] = value
        entry["_from"][where] = source
    elif (facet, where) == ("units", "registries"):  # each source states where some dependencies come from
        holder[name] = sorted({*holder[name], *value})
    elif not _same(facet, field, holder[name], value):
        entry.setdefault("conflicts", []).append({"field": where, "value": value, "source": source,
                                                  "kept_from": entry["_from"][where]})


def _add(facet: str, entries: list[dict], item: dict, source: str) -> None:
    match = None
    for level in IDENTITY[facet]:
        if any(item.get(field) is None for field in level):
            continue
        found = [e for e in entries if source not in e["sources"]
                 and all(field in e and _same(facet, field, e[field], item[field]) for field in level)]
        if len(found) == 1:
            match = found[0]
        if found:
            break
    if match is None:
        match = {"sources": [], "_from": {}}
        entries.append(match)
    match["sources"].append(source)
    for field, value in item.items():
        if field == "config" and isinstance(value, dict):
            match.setdefault("config", {})
            for key, inner in value.items():
                _set(match, facet, field, key, inner, source)
        else:
            _set(match, facet, field, None, value, source)


def join(parts: list[dict]) -> dict:
    """The facts of `parts` (`{"source", "rank", "facts", "covers"}`) as one entry per fact; see the module's
    docstring. `covers` (`{kind: [folders]}`) is where a source answers for every unit of a kind: a unit of that kind
    and folder no such source states goes to `superseded`, a gap each."""
    order = sorted(range(len(parts)), key=lambda i: (RANKS.index(parts[i]["rank"]), i))
    out: dict[str, list[dict]] = {}
    for i in order:
        for facet, items in (parts[i].get("facts") or {}).items():
            if facet not in IDENTITY:
                raise ValueError(f"{parts[i]['source']}: no facet {facet} in the pre-map")
            entries = out.setdefault(facet, [])
            for item in items:
                _add(facet, entries, item, parts[i]["source"])
    for entries in out.values():
        for entry in entries:
            entry.pop("_from")
    covers = {(kind, root): part["source"] for part in parts for kind, roots in (part.get("covers") or {}).items()
              for root in roots}
    kept, superseded = [], []
    for unit in out.get("units", []):
        by = covers.get((unit["kind"], unit["root"]))
        (superseded if by and by not in unit["sources"] else kept).append(unit)
    if superseded:
        out["units"] = kept
        out["superseded"] = [{"kind": "superseded", "path": u["root"], "source": RULE,
                              "detail": f"{u['kind']} {u.get('name')} of {', '.join(u['sources'])}: "
                                        f"{covers[(u['kind'], u['root'])]} answers for this folder without it"}
                             for u in superseded]
    return out


# ------------------------------------------------------- what the join derives

def _inside(rel: str, root: str) -> bool:
    return root == "." or rel == root or rel.startswith(root + "/")


def _run_facts(record: dict, context: Context) -> list[dict]:
    """Each unit's `run`: whether its model or index runs project code, and why; and the gap of what Daodan
    reads without running it."""
    gaps = []
    for unit in record["units"]:
        why = EXECUTES.get(unit["kind"])
        unit["run"] = {"executes_project_code": bool(why),
                       "reason": f"{unit.get('manifest') or unit['root']}: {why}" if why else ""}
        name = unit.get("name") or unit["root"]
        script = (unit.get("config") or {}).get("build_script")
        if unit["kind"] == "cargo-crate" and script:
            gaps.append({"kind": "not_executed", "unit": name, "path": script, "source": RULE,
                         "detail": "a build script is present and Daodan's index does not run it: the code it "
                                   "generates and the cfg flags it sets are unknown"})
        setup = modules._join(unit["root"], "setup.py")
        if unit["kind"] == "python-project" and setup in context.inventory.headers:
            gaps.append({"kind": "not_executed", "unit": name, "path": setup, "source": RULE,
                         "detail": "setup.py is read, not run: what it computes at run time (dependencies, "
                                   "packages) is unknown"})
    return gaps


def _analyzers() -> list:
    """The analyzers' declarations (`indexers.analyzers`), loaded through the pass: an adapter imports it back."""
    import engine_pass  # noqa: F401
    import indexers
    return indexers.analyzers()


def indexed_by() -> dict[str, frozenset]:
    """The unit kinds able to index each language, in Linguist's spelling: the ones its analyzer declares
    (`LANGUAGES`, `UNIT_KINDS`). An analyzer that takes no unit reads the snapshot's files wherever they are, and a
    language no analyzer lists has no row: its gap is `no_analyzer`."""
    return {suffix_table.NAMES.get(language, language): frozenset(analyzer.UNIT_KINDS)
            for analyzer in _analyzers() if analyzer.UNIT_KINDS for language in analyzer.LANGUAGES}


def _unlisted(record: dict) -> list[dict]:
    """Each programming language go-enry counts that no analyzer lists: its code is in no graph. A language whose
    type the answer does not give is no gap: the type is go-enry's, never guessed. Nor is one whose every file is a
    build definition (`build`, `enry.build_definition`): what it declares is the pre-map's own facts."""
    listed = {name for analyzer in _analyzers() for language in analyzer.LANGUAGES
              for name in (suffix_table.NAMES.get(language, language), *ALSO.get(language, ()))}
    return [{"kind": "no_analyzer", "language": item["language"], "files": item["files"], "source": RULE,
             "detail": f"{item['files']} {item['language']} files and no analyzer lists the language: their code is "
                       "in no graph"}
            for item in record.get("languages", [])
            if item.get("type") == "programming" and not item.get("build") and item["language"] not in listed]


def _coverage(record: dict, context: Context) -> list[dict]:
    """Code of a language that no unit able to index it holds, per outermost folder."""
    excluded = [e["path"].rstrip("/") for e in record.get("excluded", [])]
    table = indexed_by()
    roots = {language: [u["root"] for u in record["units"] if u["kind"] in kinds] for language, kinds in table.items()}
    loose: dict[str, list[str]] = {}
    for rel, header in context.inventory.headers.items():
        language = suffix_table.NAMES.get(header.get("language"))
        if language not in table or any(_inside(rel, e) for e in excluded):
            continue
        if not any(_inside(rel, root) for root in roots[language]):
            loose.setdefault(language, []).append(rel)
    gaps = []
    for language, files in sorted(loose.items()):
        folders = sorted({PurePosixPath(rel).parent.as_posix() for rel in files})
        outer = [f for f in folders if not any(other != f and _inside(f, other) for other in folders)]
        kinds = ", ".join(sorted(table[language]))
        for folder in outer:
            held = sum(1 for rel in files if _inside(rel, folder))
            gaps.append({"kind": "code_outside_units", "path": folder, "language": language, "files": held,
                         "detail": f"{held} {language} files that no unit of kind {kinds} holds", "source": RULE})
    return gaps


# ------------------------------------------------------------------ views

def _relative(path: str, root: str) -> str:
    return path if root == "." else "." if path == root else path[len(root) + 1:]


def roots(record: dict, kinds, tools=()) -> set[str]:
    """The folders an indexer runs in: the roots of the units of `kinds` and of the workspaces of `tools`, ''
    for the project's root. An indexer looks for no manifest on its own."""
    found = {u["root"] for u in record.get("units", []) if u["kind"] in kinds}
    found |= {w["root"] for w in record.get("workspace", []) if w.get("tool") in tools}
    return {"" if root == "." else root for root in found}


def python_runs(record: dict) -> list[dict]:
    """The indexer stage's Python runs: one per outermost Python root, a `python-project` unit or a uv
    workspace that no other one holds, the units inside folded into it (one run reads its whole folder). Each
    run: `root` ('' for the project's root), `name` (the outer unit's, None for a virtual workspace),
    `manifests` (the files declaring the packages of every folded unit: manifests, requirements files, `uv.lock`
    where uv read one), `source_roots` (declared ones, relative to the run's root)."""
    units = [u for u in record.get("units", []) if u["kind"] == "python-project"]
    workspaces = [w for w in record.get("workspace", []) if w.get("tool") == "uv"]
    roots = {u["root"] for u in units} | {w["root"] for w in workspaces}
    # Python files no unit holds (`code_outside_units`) are code too: the checkout is then the run, the projects
    # inside it folded in, each keeping its folder as the root of its own imports (`unit_roots`).
    loose = roots and "." not in roots and any(
        gap["kind"] == "code_outside_units" and gap.get("language") == "Python" for gap in record.get("gaps", []))
    if loose:
        folded, roots = sorted(roots), roots | {"."}
    outer = sorted(r for r in roots if not any(other != r and _inside(r, other) for other in roots))
    runs = []
    for root in outer:
        held = [u for u in units if _inside(u["root"], root)]
        manifests = {u["manifest"] for u in held if u.get("manifest")}
        manifests |= {rel for u in held for rel in (u.get("config") or {}).get("requirements", [])}
        locked = [w["root"] for w in workspaces if _inside(w["root"], root)]
        locked += [u["root"] for u in held if any(s.startswith(f"{uv.NAME}@") for s in u["sources"])
                   and not any(_inside(u["root"], w) for w in locked)]
        for folder in locked:  # the lock is read with the pyproject beside it
            manifests |= {name if folder == "." else f"{folder}/{name}" for name in ("pyproject.toml", "uv.lock")}
        top = next((u for u in held if u["root"] == root), None)
        runs.append({"root": "" if root == "." else root, "name": top.get("name") if top else None,
                     "manifests": sorted(manifests),
                     "source_roots": sorted({_relative(s, root) for u in held for s in u.get("source_roots", [])}),
                     **({"unit_roots": folded} if loose else {})})
    return runs


# --------------------------------------------------------------- lifecycle

def _inputs(store, sources) -> str:
    value = [logical_digest(store), store["root"], [label(s) for s in sources], SCHEMA]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _failed(status: dict, error: Exception) -> dict:
    if hasattr(error, "install"):  # runtime.Unavailable's contract
        status.update(state="unavailable", reason=error.reason, install=error.install)
        return {"kind": "source_unavailable", "source": status["source"], "detail": error.reason,
                "remedy": error.install}
    status.update(state="failed", reason=f"{type(error).__name__}: {error}")
    return {"kind": "source_failed", "source": status["source"], "detail": status["reason"]}


def _takes_toolchains(runner) -> bool:
    try:
        return "toolchains" in inspect.signature(runner).parameters
    except (TypeError, ValueError):
        return False


def _run(source, context: Context, runner, toolchains=()) -> tuple[dict, dict | None, list[dict]]:
    started = time.monotonic()
    status = {"source": label(source), "rank": source.RANK}
    try:
        if hasattr(source, "commands"):
            commands = source.commands(context)
            if not commands:
                result = None
            elif runner is None:
                status.update(state="not_run", commands=len(commands), seconds=round(time.monotonic() - started, 3))
                return status, None, [{"kind": "model_not_run", "source": status["source"],
                                       "detail": f"{len(commands)} model commands not run yet: they run in "
                                                 "Daodan's container, and their facts are missing until then"}]
            else:
                try:
                    results = runner(commands, toolchains=toolchains) if _takes_toolchains(runner) else runner(commands)
                except Exception as error:  # no container here (`container.Gap`): not run, retried when one answers
                    if not (hasattr(error, "cause") and hasattr(error, "remedy")):
                        raise
                    status.update(state="not_run", commands=len(commands),
                                  seconds=round(time.monotonic() - started, 3))
                    return status, None, [{"kind": "model_not_run", "source": status["source"],
                                           "detail": f"{len(commands)} model commands not run: {error.cause}",
                                           "remedy": error.remedy}]
                if len(results) != len(commands):
                    raise ValueError(f"the runner answered {len(results)} of {len(commands)} commands")
                prepared = [g for r in results for g in r.get("gaps") or ()]
                result = source.read(context, commands, [{k: v for k, v in r.items() if k != "gaps"} for r in results])
                if prepared:
                    result = {**(result or {"facts": {}}), "gaps": [*prepared, *((result or {}).get("gaps") or ())]}
        else:
            result = source.run(context)
        stated = set((result or {}).get("facts") or {}) - set(IDENTITY)
        if stated:  # structure only: a library a unit uses is resolved by its analyzer's build tool
            raise ValueError(f"no facet {', '.join(sorted(stated))} in the pre-map")
    except Exception as error:  # an adapter's every failure is the source's gap, never the pre-map's end
        gap = _failed(status, error)
        status["seconds"] = round(time.monotonic() - started, 3)
        return status, None, [gap]
    status.update(state="not_needed" if result is None else "ran", seconds=round(time.monotonic() - started, 3))
    if result is None:
        return status, None, []
    if result.get("version"):  # the version that answered, when it is not the pinned one
        status["source"] = f"{source.NAME}@{result['version']}"
    name = status["source"]
    return (status, {"source": name, "rank": source.RANK, "facts": result.get("facts") or {},
                     "covers": result.get("covers") or {}},
            [{**gap, "source": name} for gap in result.get("gaps") or []])


def derive(manifest: Path, store, sources=None, runner=None, report=None) -> dict:
    """The pre-map of the snapshot in `store`; `runner(commands) -> results` runs the model commands, each
    `{tool, argv, cwd, env}` under the project's root, each result `{returncode, stdout, stderr, root}` with
    `root` the project's absolute path where it ran."""
    sources = tuple(SOURCES if sources is None else sources)
    context = Context(manifest, store)
    ran: dict[int, tuple] = {}
    readers = [i for i, s in enumerate(sources) if not hasattr(s, "commands")]
    for i in readers + [i for i in range(len(sources)) if i not in readers]:
        context.stated = {} if i in readers else join([part for _, part, _ in ran.values() if part])
        toolchains = context.stated.get("toolchains", ())
        ran[i] = _run(sources[i], context, runner, toolchains)
        if report is not None:  # `report(status, done, total)`: each source as it ends
            report(ran[i][0], len(ran), len(sources))
    statuses, parts, gaps = [], [], []
    for i in range(len(sources)):  # the sources' order: the join's precedence between equals
        status, part, found = ran[i]
        statuses.append(status)
        if part:
            parts.append(part)
        gaps.extend(found)
    record = {"schema": SCHEMA,
              "binding": {"manifest": str(Path(manifest).resolve()), "logical_digest": logical_digest(store),
                          "root": store["root"]},
              "inputs_digest": _inputs(store, sources), "sources": statuses, **join(parts)}
    if any(p["ecosystem"] == "pypi" for p in record.get("packages", ())):
        record["packages"] = module_graph.external_packages(context.graph, record["packages"])
    gaps.extend(record.pop("superseded", []))
    record.setdefault("units", [])
    for unit in record["units"]:
        unit.setdefault("depends_on", [])
    record["units"].sort(key=lambda u: (u["root"], u["kind"], u.get("name") or ""))
    record["gaps"] = gaps + _run_facts(record, context) + _coverage(record, context) + _unlisted(record)
    return record


def write(manifest: Path, sources=None, runner=None, report=None) -> dict:
    """Derive and publish `premap.json` beside the manifest."""
    manifest = Path(manifest).resolve()
    target = path(manifest)
    confinement.reject_link_chain(target)
    with open_snapshot(manifest) as store:
        record = derive(manifest, store, sources, runner, report)
        if logical_digest(store) != record["binding"]["logical_digest"]:
            raise ValueError("snapshot changed during the pre-map; retry")
    descriptor, name = tempfile.mkstemp(prefix=".premap-", dir=target.parent)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    os.replace(name, target)
    return json.loads(target.read_text(encoding="utf-8"))


def state(manifest: Path, sources=None, runner=None) -> dict:
    """fresh, stale, missing or corrupt, without touching the pre-map; with a runner, a pre-map whose model
    commands did not run is stale."""
    manifest = Path(manifest).resolve()
    target = path(manifest)
    report = {"premap": str(target), "manifest": str(manifest)}
    if not target.is_file():
        return {**report, "state": "missing", "reason": "no pre-map beside the manifest"}
    try:
        record = json.loads(target.read_text(encoding="utf-8"))
        if record.get("schema") != SCHEMA:
            raise ValueError(f"schema {record.get('schema')!r}")
    except (OSError, ValueError) as error:
        return {**report, "state": "corrupt", "reason": str(error)}
    with open_snapshot(manifest) as store:
        current = _inputs(store, tuple(SOURCES if sources is None else sources))
    if record.get("inputs_digest") != current:
        return {**report, "state": "stale", "reason": "snapshot or sources changed since the pre-map"}
    if runner is not None and any(s.get("state") == "not_run" for s in record.get("sources", [])):
        return {**report, "state": "stale", "reason": "model commands not run yet"}
    return {**report, "state": "fresh"}


def ensure(manifest: Path, sources=None, runner=None, report=None) -> dict:
    """The pre-map of `manifest`, derived again when it is not fresh; with a runner, also when model commands were
    left `not_run` (the whole pre-map again: the join needs every source's part)."""
    if state(manifest, sources, runner)["state"] == "fresh":
        return json.loads(path(manifest).read_text(encoding="utf-8"))
    return write(manifest, sources, runner, report)
