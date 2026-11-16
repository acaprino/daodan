"""rust-analyzer's SCIP output: how it runs, and the aliases its index states its own way.

`index` runs `rust-analyzer scip` with the release and the Rust toolchain Daodan pins (`engine_tools`) and its
options (`CONFIG`: all features, no build script, no procedural macro, so no project code runs) in a mirror of
the project where every directory holding a `Cargo.toml` is real: at the root, then in each crate directory
holding files the root run left out. What a macro generates is not seen.

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

# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-rust", ("rust",), frozenset({"cargo-crate"}), False
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


def tasks(configs) -> dict:
    """What the run brought back for `missing`: `{"roots": [folder], "failed": {folder: how its run ended}}`,
    empty without it."""
    return configs if isinstance(configs, dict) else {}


# The configuration rust-analyzer reads (`CONFIG`): every feature on, the host's target, no build script, so no
# cfg one sets (`cargo:rustc-cfg`, tauri's `desktop`). A site the index answers nothing at under a `cfg` false
# there is code rust-analyzer leaves out; one of the cfgs it may set (`UNDECIDED`) or of another target key decides
# nothing.
CONFIGURATION = "every feature on, the host's target, no build script"
CFG_OFF = "its `#![cfg({})]` is false in the configuration rust-analyzer reads (" + CONFIGURATION + ")"
MOD_OFF = "the `mod` item that loads it is under `#[cfg({})]`, false in the configuration rust-analyzer reads (" \
    + CONFIGURATION + ")"
INACTIVE = "under `#[cfg({})]`, false in the configuration rust-analyzer reads (" + CONFIGURATION + \
    "): nothing is written"
UNDECIDED = frozenset({"test", "debug_assertions", "miri", "doc", "doctest", "docsrs", "proc_macro",
                       "overflow_checks", "ub_checks", "fmt_debug", "panic", "relocation_model", "sanitize"})
TARGET = ("target_endian", "target_family", "target_os", "target_pointer_width")


def _host() -> dict[str, str]:
    """The host's target cfgs rust-analyzer reads with no target set: endian, family, os, pointer width."""
    import sys
    system = {"win32": "windows", "darwin": "macos"}.get(sys.platform, sys.platform.split("-")[0].rstrip("0123456789"))
    family = "windows" if system == "windows" else "unix"
    return {"target_endian": sys.byteorder, "target_family": family, "target_os": system,
            "target_pointer_width": "64" if sys.maxsize > 2**32 else "32", family: ""}


def _cfg(text: str):
    """The value of a `cfg` predicate in the configuration rust-analyzer reads; None where it decides nothing."""
    import re
    text = text.strip()
    if re.fullmatch(r'feature\s*=\s*"[^"]*"', text):
        return True
    named = re.fullmatch(r'(\w+)\s*=\s*"([^"]*)"', text)
    if named:
        return _host()[named.group(1)] == named.group(2) if named.group(1) in TARGET else None
    if re.fullmatch(r"\w+", text):
        return text in _host() if text in ("unix", "windows") else None if text in UNDECIDED else False
    found = re.fullmatch(r"(not|all|any)\s*\((.*)\)", text, re.S)
    if not found:
        return None
    depth, items, start = 0, [], 0
    for at, char in enumerate(found.group(2)):
        depth += char == "("
        depth -= char == ")"
        if char == "," and depth == 0:
            items.append(found.group(2)[start:at])
            start = at + 1
    values = [_cfg(item) for item in [*items, found.group(2)[start:]] if item.strip()]
    if found.group(1) == "not":
        return None if len(values) != 1 or values[0] is None else not values[0]
    if found.group(1) == "all":
        return False if False in values else None if None in values else True
    return True if True in values else None if None in values else False


def _cfgs(node, inner: bool = False) -> list[str]:
    """The predicates of the `#[cfg(...)]` attributes written before a node (`#![cfg]` inside it, with `inner`)."""
    out, sibling = [], node.prev_named_sibling if not inner else None
    attributes = [child for child in node.named_children if child.type == "inner_attribute_item"] if inner else []
    while sibling is not None and sibling.type in ("attribute_item", "line_comment", "block_comment"):
        attributes.append(sibling)
        sibling = sibling.prev_named_sibling
    for item in attributes:
        text = item.text.decode("utf-8", errors="replace")
        start = text.find("cfg(")
        if start != -1 and text[:start].strip("#![ ") == "":
            out.append(text[start + 4:text.rfind(")")].strip())
    return out


def _off(node) -> str | None:
    """The first `cfg` written before `node` or a node enclosing it that is false in the configuration."""
    while node is not None:
        for predicate in _cfgs(node):
            if _cfg(predicate) is False:
                return predicate
        node = node.parent
    return None


def unanswered(index):
    """Why the index has no occurrence at a site: a `cfg` written before an enclosing item, statement or
    expression is false in the configuration rust-analyzer reads (`INACTIVE`)."""
    def cause(position: tuple) -> str | None:
        rel, line, column = position
        tree = index.tree(rel, "rust") if rel.endswith(".rs") and column is not None else None
        point = (line - 1, column)
        off = _off(tree.root_node.descendant_for_point_range(point, (line - 1, column + 1))) if tree else None
        return INACTIVE.format(off) if off else None
    return cause


def missing(index, rels: list[str], configs: dict | None = None) -> dict:
    """Why a Rust file has no document: the run of its crate wrote no index and no other run read the crate;
    else no `mod` item of an indexed file loads it, so no crate includes it; else each `mod` item that loads it is
    under a `cfg` false in the configuration rust-analyzer reads (`MOD_OFF`), or the file's own `#![cfg]` is
    (`CFG_OFF`)."""
    roots, failed = set((configs or {}).get("roots") or ()), (configs or {}).get("failed") or {}
    read = {code_graph.owner(rel, roots) for rel in index.documents}
    loaded = collections.defaultdict(list)  # a file a `mod` item loads: the false cfg of each such item
    for rel, name in _mod_items(index):
        for candidate in _module_files(rel, name.text.decode("utf-8")):
            loaded[candidate].append(_off(name.parent))
    reasons = {}
    for rel in rels:
        root = code_graph.owner(rel, roots)
        tree = index.tree(rel, "rust")
        own = [predicate for predicate in (_cfgs(tree.root_node, inner=True) if tree is not None else ())
               if _cfg(predicate) is False]
        if root in failed and root not in read:
            reasons[rel] = f"the rust-analyzer run of its crate {root or '.'} wrote no index ({failed[root]})"
        elif rel not in loaded and PurePosixPath(rel).name not in ("lib.rs", "main.rs", "build.rs") \
                and PurePosixPath(rel).parent.name not in ROOT_DIRECTORIES:
            reasons[rel] = "no crate includes it: no `mod` item of an indexed file loads it"
        elif rel in loaded and all(loaded[rel]):
            reasons[rel] = MOD_OFF.format(loaded[rel][0])
        elif own:
            reasons[rel] = CFG_OFF.format(own[0])
    return reasons


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folders it runs in."""
    import premap
    return {"roots": premap.roots(record, UNIT_KINDS, {"cargo"})}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, roots: set[str]) -> dict:
    """The rust-analyzer index of `project_dir` for `files` (default: every `.rs` file outside `target`),
    `roots` the folders of its crates and workspaces as the pre-map names them."""
    import engine_tools
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tool = runtime.Tool(project_dir, "rust-analyzer", rx.RUST_ANALYZER_RELEASE)
    home = tool.home()
    try:
        runtime.memory("rust-analyzer", MIN_FREE)
        if not tool.installed():
            runtime.room()
        with runtime.fetching(f"rust-analyzer {rx.RUST_ANALYZER_RELEASE} and Rust {rx.RUST_VERSION}",
                              "github.com and static.rust-lang.org"):
            toolchain = engine_tools.rust_toolchain()
            if toolchain is None:
                raise runtime.Unavailable("no Rust toolchain could be installed", "check the network: Daodan "
                                          "downloads cargo, rustc and rust-src from static.rust-lang.org")
            tool._install(home, engine_tools.fetch_rust_analyzer)
    except runtime.Unavailable as error:
        return runtime.refused("rust-analyzer", rx.RUST_ANALYZER_RELEASE, error)
    # Crates the project depends on land in the shared directory, not in the user's cargo home.
    launch = [str(home / rx.executable_name("rust-analyzer"))]
    overrides = {"PATH": str(toolchain / "bin") + os.pathsep + os.environ.get("PATH", ""),
                 "CARGO_HOME": str(engine_tools.shared_cache_dir() / "cargo"),
                 "CARGO_TARGET_DIR": str(work_dir / "rust-target")}
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
    roots = set(roots)

    def command(prefix, output):
        return [launch[0], "scip", ".", "--output", str(output), "--config-path", str(config)]

    runtime.clear(work_dir, "rust-analyzer")
    try:
        with runtime.mirrored(tool, runtime.real(roots, work_dir)) as mirror:
            runs = code_graph.module_runs("rust-analyzer", roots, command, files, mirror, work_dir, env,
                                          fallback=lambda prefix, output: command(prefix, output)[:-2])
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    # Named by its pinned release, like every indexer; `build` is what the binary states; `configs` is for `tasks`.
    return {**runtime.outcome("rust-analyzer", rx.RUST_ANALYZER_RELEASE, runs), "build": build,
            "toolchain": rx.RUST_VERSION, "config": CONFIG,
            "configs": {"roots": sorted(roots), "failed": {run["prefix"]: f"exit code {run['returncode']}"
                                                           for run in runs if not run["index"]}}}
