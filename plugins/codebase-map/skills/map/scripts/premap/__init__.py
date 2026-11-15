"""The pre-map of a snapshot: what the project holds and how each unit is analysed, before any indexer.

`premap.json` (`daodan/premap/v1`) beside the manifest, in Daodan's store, never in the project; the shape is
in `references/premap.md`: the project's structure and the toolchains it declares, never the libraries its
units use (each analyzer's build tool resolves those in the container while it indexes; a source stating them
fails). A source is a thin adapter in this package (`NAME`, `VERSION`, `RANK`) that states
facts in that shape: Daodan detects nothing on its own. A reader reads files and runs nothing (`run(context)`).
A model source is a build system's own command: `commands(context)` describes it as data, a runner the caller
supplies executes it in Daodan's container, and `read(context, commands, results)` reads its output; without a
runner it is `not_run`. The join keeps one entry per fact with the sources that state it (`tool@version`).
Where two sources give a field different values, the value of the source with precedence stays (`RANKS`: a
model command, a file reader, a scanner; between equals, the earlier in `SOURCES`) and the other goes to the
entry's `conflicts` with its source. What no source establishes is a gap with its class. Deterministic for the
same snapshot, source versions and command outputs.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import time

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import confinement  # noqa: E402
import modules  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402

from premap import (bazel, cargo, cmake, enry, gitmodules, go, jvm_files, meson, module_graph, npm,  # noqa: E402
                    npm_lock, python_build, renovate, requirements, suffix_table, tsc, uv)

SCHEMA = "daodan/premap/v1"
FILE = "premap.json"
RULE = "premap@" + SCHEMA  # the source of what the pre-map derives itself: `run` and the coverage gaps
RANKS = ("model", "reader", "scanner")
SOURCES = (module_graph, python_build, requirements, npm_lock, jvm_files, gitmodules, enry, renovate, go, cargo, uv,
           tsc, npm, cmake, meson, bazel)
IDENTITY = {  # the fields that make two entries one fact, from the strictest to the loosest
    "languages": (("language",),),
    "excluded": (("path",),),
    "units": (("root", "kind", "name", "manifest"), ("root", "kind", "name"), ("root", "kind")),
    "workspace": (("root", "tool"),),  # two build systems in one folder are two workspaces
    "toolchains": (("tool", "declared_in", "version"), ("tool", "declared_in")),
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
    "bazel-target": "Bazel evaluates the BUILD files and runs the repository rules",
    "bazel-module": "Bazel evaluates the BUILD files and runs the repository rules",
    "swift-package": "SwiftPM compiles and runs Package.swift",
    "mix-project": "Mix evaluates mix.exs and expands the project's macros",
    "xcode-target": "the build settings come from xcodebuild",
}
_JS = frozenset({"npm-package", "deno-project", "angular-project", "nx-project"})
_JVM = frozenset({"maven-module", "gradle-project", "sbt-project"})
_NATIVE = frozenset({"cmake-target", "make-target", "meson-target", "bazel-target", "msbuild-project"})
INDEXED_BY = {"Python": frozenset({"python-project"}), "Go": frozenset({"go-module"}),
              "Rust": frozenset({"cargo-crate"}), "TypeScript": _JS, "JavaScript": _JS, "Vue": _JS, "Svelte": _JS,
              "Java": _JVM, "Kotlin": _JVM, "C": _NATIVE, "C++": _NATIVE,
              "C#": frozenset({"dotnet-project", "msbuild-project"})}


class Context:
    """What a source reads: the snapshot (`store`, `inventory`, hash-verified text) and the module graph."""

    def __init__(self, manifest: Path, store):
        self.manifest, self.store = Path(manifest), store
        self.root = Path(store["root"])
        self.inventory = modules._Inventory(store)
        self._graph = None

    @property
    def graph(self) -> dict:
        if self._graph is None:
            self._graph = modules.load_graph(Path(modules.ensure_graph(self.manifest)["graph"]))
        return self._graph


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def label(source) -> str:
    return f"{source.NAME}@{source.VERSION}"


# ---------------------------------------------------------------------- join

def _package(name) -> str:
    return re.sub(r"[-_.]+", "-", str(name)).casefold()


def _canonical(value) -> str:
    if isinstance(value, list):
        return json.dumps(sorted(_canonical(v) for v in value))
    return json.dumps(value, sort_keys=True)


def _same(facet: str, field: str, a, b) -> bool:
    # Names fold as PEP 503 does: uv prints `acme-cli` for `acme_cli`; a unit's name is compared only between
    # entries of the same root and kind.
    if (facet, field) == ("units", "name") and a and b:
        return _package(a) == _package(b)
    if (facet, field) == ("toolchains", "declared_in") and a and b:  # a file and a setting of it are one place
        return str(a).split("#", 1)[0] == str(b).split("#", 1)[0]
    return _canonical(a) == _canonical(b)


def _set(entry: dict, facet: str, field: str, key: str | None, value, source: str) -> None:
    holder = entry["config"] if key is not None else entry
    name, where = (key, f"config.{key}") if key is not None else (field, field)
    if name not in holder:
        holder[name] = value
        entry["_from"][where] = source
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


def _coverage(record: dict, context: Context) -> list[dict]:
    """Code of a language that no unit able to index it holds, per outermost folder."""
    excluded = [e["path"].rstrip("/") for e in record.get("excluded", [])]
    roots = {language: [u["root"] for u in record["units"] if u["kind"] in kinds]
             for language, kinds in INDEXED_BY.items()}
    loose: dict[str, list[str]] = {}
    for rel, header in context.inventory.headers.items():
        language = suffix_table.NAMES.get(header.get("language"))
        if language not in INDEXED_BY or any(_inside(rel, e) for e in excluded):
            continue
        if not any(_inside(rel, root) for root in roots[language]):
            loose.setdefault(language, []).append(rel)
    gaps = []
    for language, files in sorted(loose.items()):
        folders = sorted({PurePosixPath(rel).parent.as_posix() for rel in files})
        outer = [f for f in folders if not any(other != f and _inside(f, other) for other in folders)]
        kinds = ", ".join(sorted(INDEXED_BY[language]))
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
                     "source_roots": sorted({_relative(s, root) for u in held for s in u.get("source_roots", [])})})
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


def _run(source, context: Context, runner) -> tuple[dict, dict | None, list[dict]]:
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
                results = runner(commands)
                if len(results) != len(commands):
                    raise ValueError(f"the runner answered {len(results)} of {len(commands)} commands")
                result = source.read(context, commands, results)
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
    statuses, parts, gaps = [], [], []
    for number, source in enumerate(sources, 1):
        status, part, found = _run(source, context, runner)
        statuses.append(status)
        if report is not None:  # `report(status, done, total)`: each source as it ends
            report(status, number, len(sources))
        if part:
            parts.append(part)
        gaps.extend(found)
    record = {"schema": SCHEMA,
              "binding": {"manifest": str(Path(manifest).resolve()), "logical_digest": logical_digest(store),
                          "root": store["root"]},
              "inputs_digest": _inputs(store, sources), "sources": statuses, **join(parts)}
    gaps.extend(record.pop("superseded", []))
    record.setdefault("units", [])
    for unit in record["units"]:
        unit.setdefault("depends_on", [])
    record["units"].sort(key=lambda u: (u["root"], u["kind"], u.get("name") or ""))
    record["gaps"] = gaps + _run_facts(record, context) + _coverage(record, context)
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
    """The pre-map of `manifest`, derived again when it is not fresh."""
    if state(manifest, sources, runner)["state"] == "fresh":
        return json.loads(path(manifest).read_text(encoding="utf-8"))
    return write(manifest, sources, runner, report)
