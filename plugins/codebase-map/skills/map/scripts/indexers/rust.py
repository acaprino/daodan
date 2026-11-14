"""rust-analyzer's SCIP output: how it runs, and the aliases its index states its own way.

`index` runs `rust-analyzer scip` with the engine pass's binary, toolchain and options (`RustEngine`: all
features, no build script, no procedural macro, so no project code runs) in a mirror of the project where every
directory holding a `Cargo.toml` is real: at the root, then in each crate directory holding files the root run
left out. What a macro generates is not seen.

`hops` reads `let x = y` (the symbol the index references at the value) and a closure value (the function the
snapshot declares there). A module several crates include (`mod util;` in each test crate) is written once,
with one crate's symbols, and the other crates name its items with symbols defined nowhere; `mod name;` loads
`name.rs` or `name/mod.rs`, and the document of that file defines the module under another crate's symbol:
those names lead there, tagged `rust:module-file`.
"""
from __future__ import annotations

import collections
import json
import os
import shutil
import subprocess
from pathlib import Path, PurePosixPath

import code_graph

MIN_FREE = 1280 * 2**20  # 1,180 MB peak on semver (benchmarks/inference-audit, 13 November 2026)
# The engine pass's own rust-analyzer options: all features, no build script, no procedural macro.
CONFIG = {"cargo": {"buildScripts": {"enable": False}, "features": "all"}, "procMacro": {"enable": False}}

PATTERNS = {"tuple_pattern", "struct_pattern", "tuple_struct_pattern", "field_pattern", "ref_pattern",
            "mut_pattern", "slice_pattern", "or_pattern"}
ROOT_DIRECTORIES = ("tests", "benches", "examples", "bin")


def _defining_value(node) -> tuple[str, object]:
    child, parent, destructured = node, node.parent, False
    while parent is not None and parent.type in PATTERNS:
        child, parent, destructured = parent, parent.parent, True
    if parent is None:
        return "none", None
    if parent.type == "let_declaration" and parent.child_by_field_name("pattern") == child:
        return ("destructured" if destructured else "value"), parent.child_by_field_name("value")
    if parent.type in ("parameter", "closure_parameters", "self_parameter"):
        return "parameter", None
    return "none", None


def _value(index, rel: str, value) -> list:
    while value is not None and value.type == "parenthesized_expression":
        value = value.named_children[0] if value.named_children else None
    if value is None:
        return []
    if value.type == "closure_expression":
        return [((rel, value.start_point[0] + 1, value.start_point[1]), "value")]
    field = {"identifier": None, "scoped_identifier": "name", "field_expression": "field"}
    if value.type not in field:
        return []
    name = value.child_by_field_name(field[value.type]) if field[value.type] else value
    return [(key, "initializer") for key in index.stated(rel, name)] if name is not None else []


def _module_files(rel: str, name: str) -> list[str]:
    """Where `mod name;` in a file loads its module from."""
    path = PurePosixPath(rel)
    beside = path.name in ("mod.rs", "lib.rs", "main.rs", "build.rs") or path.parent.name in ROOT_DIRECTORIES
    base = path.parent if beside else path.parent / path.stem
    return [(base / f"{name}.rs").as_posix(), (base / name / "mod.rs").as_posix()]


def _mod_items(index):
    """`(file, name node)` of every `mod name;` without a body."""
    for rel in index.documents:
        if not rel.endswith(".rs"):
            continue
        tree = index.tree(rel, "rust")
        stack = [tree.root_node] if tree is not None else []
        while stack:
            node = stack.pop()
            if node.type == "mod_item" and node.child_by_field_name("body") is None:
                name = node.child_by_field_name("name")
                if name is not None:
                    yield rel, name
            stack.extend(node.named_children)


def _modules(index) -> dict:
    """The module symbol each document defines at its start."""
    out = {}
    for rel, occurrences in index.documents.items():
        for occurrence in occurrences:
            if occurrence.definition and occurrence.key.endswith("/") and (occurrence.line, occurrence.start) == (1, 0):
                out[rel] = occurrence.key
                break
    return out


def hops(index) -> dict:
    """Alias edges from the statements that define the names of Rust documents, and module-file hops."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        if not rel.endswith(".rs"):
            continue
        for occurrence in occurrences:
            if not occurrence.definition or occurrence.key.endswith(("#", ").", "/", ")")):
                continue
            node = index.node(rel, occurrence, "rust")
            if node is None:
                continue
            form, value = _defining_value(node)
            if form == "value" and value is not None:
                out[occurrence.key] += [item for item in _value(index, rel, value) if item[0] != occurrence.key]
    modules, aliases = _modules(index), {}
    for rel, name in _mod_items(index):
        for key in index.stated(rel, name):
            if not key.endswith("/") or key in index.defs:
                continue
            for candidate in _module_files(rel, name.text.decode("utf-8")):
                if modules.get(candidate) and modules[candidate] != key:
                    aliases[key] = modules[candidate]
    if aliases:
        referenced = {occurrence.key for occurrences in index.documents.values() for occurrence in occurrences
                      if not occurrence.definition and occurrence.key not in index.defs}
        for key in referenced:
            prefix = next((prefix for prefix in aliases if key.startswith(prefix)), None)
            if prefix is not None and aliases[prefix] + key[len(prefix):] in index.defs:
                out[key].append((aliases[prefix] + key[len(prefix):], "rust:module-file"))
    return {key: list(dict.fromkeys(items)) for key, items in out.items() if items}


def missing(index, rels: list[str]) -> dict:
    """Why a Rust file has no document: no `mod` item of an indexed file loads it, so no crate includes it."""
    loaded = {candidate for rel, name in _mod_items(index) for candidate in _module_files(rel, name.text.decode("utf-8"))}
    return {rel: "no crate includes it: no `mod` item of an indexed file loads it" for rel in rels
            if rel not in loaded and PurePosixPath(rel).name not in ("lib.rs", "main.rs", "build.rs")
            and PurePosixPath(rel).parent.name not in ROOT_DIRECTORIES}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """The rust-analyzer index of `project_dir` for `files` (default: every `.rs` file outside `target`)."""
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    engine = rx.RustEngine(project_dir)
    engine.target_dir = work_dir / "rust-target"
    home = engine.home()
    try:
        runtime.memory("rust-analyzer", MIN_FREE)
        if not (home / ".installed").is_file():
            runtime.room()
        with runtime.fetching(f"rust-analyzer {rx.RUST_ANALYZER_RELEASE} and Rust {rx.RUST_VERSION}",
                              "github.com and static.rust-lang.org"):
            ready, reason = engine.prepare(home)
        if not ready:
            raise runtime.Unavailable(reason, engine.install)
    except runtime.Unavailable as error:
        return runtime.refused("rust-analyzer", rx.RUST_ANALYZER_RELEASE, error)
    launch, overrides = engine.command(home)
    # On Windows rust-analyzer leaves a `proc-macro-srv*` directory per load in the temporary folder.
    temp = work_dir / "rust-analyzer-temp"
    temp.mkdir(exist_ok=True)
    env = {**os.environ, **overrides, "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}
    build = subprocess.run([launch[0], "--version"], env=env, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=120).stdout.strip()
    config = work_dir / "rust-analyzer.json"
    config.write_text(json.dumps(CONFIG), encoding="utf-8")
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*.rs")
                       if "target" not in path.relative_to(project_dir).parts)
    roots = code_graph.manifest_dirs(project_dir, "Cargo.toml")

    def command(prefix, output):
        return [launch[0], "scip", ".", "--output", str(output), "--config-path", str(config)]

    runtime.clear(work_dir, "rust-analyzer")
    try:
        with runtime.mirrored(engine, runtime.real(roots, work_dir)) as mirror:
            runs = code_graph.module_runs("rust-analyzer", roots, command, files, mirror, work_dir, env,
                                          fallback=lambda prefix, output: command(prefix, output)[:-2])
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    # Named by its pinned release, like every indexer; `build` is what the binary states.
    return {**runtime.outcome("rust-analyzer", rx.RUST_ANALYZER_RELEASE, runs), "build": build,
            "toolchain": rx.RUST_VERSION, "config": CONFIG}
