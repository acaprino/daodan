"""rust-analyzer's SCIP output: how it runs, and the aliases its index states its own way.

`rust-analyzer scip` runs the build scripts (`cargo check`) and builds and loads the procedural macros whatever
`buildScripts.enable` and `procMacro.enable` say: at the pinned release cli/scip.rs loads the workspace with
`load_out_dirs_from_check: true` and the sysroot's proc-macro server. A `rust-project.json` names the sysroot
whose server and rustc it starts and the macro libraries it loads, `.cargo/config.toml` the programs cargo starts
as rustc. So rust-analyzer runs only in Daodan's container (`NEEDS_CONTAINER`), never on the host: one run over a
copy of the project (`_boxed`), with Daodan's Rust or the one a rustup file names (`toolchains`) and the standard
library's sources, which rust-analyzer reads. The preparation, with the registries and the hosts the project
declares open, installs them and fetches each root's crates (`cargo fetch`); the execution, with no network, runs
in each Cargo workspace's root and each crate outside one (`boxes`) the check rust-analyzer starts, through its
own compiler wrapper, then `rust-analyzer scip` with its defaults (`BOXED`). A build script that fails, or a
procedural macro that does not build, is a gap naming the crate and its error (`built`), and rust-analyzer reads
that crate as with build scripts off; a root it writes no index of is a run without one, with its own words.
Beside each index, `<index>.cfg.json` says whether the build scripts ran and the cfgs each crate's set, which
`unanswered` and `missing` read to decide a `cfg`.

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
import posixpath
import re
import shlex
import shutil
from pathlib import Path, PurePosixPath

import code_graph
import preparation
from premap.container_runner import IMAGE  # Ubuntu 24.04: gcc and the linker the build scripts' builds need

# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-rust", ("rust",), frozenset({"cargo-crate"}), True
BOXED = {"cargo": {"features": "all"}}  # rust-analyzer's defaults, build scripts and proc macros, all features
OUT = "/daodan/out/rust-analyzer"
ANALYZER = f"{preparation.IN}/rust-analyzer"
RUST_SRC = ("https://static.rust-lang.org/dist/2026-10-15/rust-src-1.99.1.tar.xz",
            "e485a88c45db546b73571df7bebfcb4454ba4fb552c492e25fc5b00eeb5bf22d", "rust-src.tar.xz")  # its manifest's
SRC_SETUP = (f"{{ mkdir -p {preparation.T}/x && tar -xJf {preparation.IN}/rust-src.tar.xz -C {preparation.T}/x"
             f" && cp -R {preparation.T}/x/rust-src-*/rust-src/. {preparation.T}/rust/ && rm -rf {preparation.T}/x"
             f" ; }} >&2 || echo 'DAODAN-MISSING rust-src@{preparation.NEEDS['rust']['version']}' >&2")
# What rust-analyzer's check runs (project-model's build_command), its compiler wrapper building only the build
# scripts and procedural macros; `--keep-going` is stable from Cargo 1.74, an older toolchain runs without it.
CHECK = "cargo check --quiet --workspace --message-format=json --all-features --keep-going --all-targets"
MIN_FREE = MEMORY = 8 * 2**30  # the container's memory, for the check and the index
LIMIT = 3600  # the seconds one root's check, and its index, may take
BUILD = 600  # the seconds the execution's own lines may take beside them
FALLBACK = "rust-analyzer reads {} as with build scripts off: without the cfgs they set and the files they write"
UNEXPANDED = "its macros are not expanded, as with procedural macros off"
NO_SERVER = ("the sysroot holds no rust-analyzer-proc-macro-srv: rust-analyzer expands no procedural macro, as with "
             "procedural macros off")
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


def _mod_items(index, files=None):
    """`(file, name node)` of every `mod name;` without a body, in the index's documents or in `files`."""
    for rel in index.documents if files is None else files:
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


# The configuration rust-analyzer read a file in (`_configuration`): every feature on, the target of where it ran,
# and the cfgs the crate's build script set where it ran (`cargo:rustc-cfg`, tauri's `desktop`), none elsewhere. A
# site the index answers nothing at under a `cfg` false there is code rust-analyzer leaves out; one of the cfgs it
# may set (`UNDECIDED`), or of a key outside the target's with no build script run, decides nothing.
HOST, CONTAINER = "host", "container"
TARGETS = {HOST: "the host's target", CONTAINER: "Linux in Daodan's container"}
SCRIPTS = {False: "no build script", True: "the build scripts run", "failed": "its build script failed"}
LINUX = {"target_endian": "little", "target_family": "unix", "target_os": "linux", "target_pointer_width": "64",
         "unix": ""}  # the container's target, x86_64 or aarch64 Linux


def _described(where: str, scripts) -> str:
    return f"every feature on, {TARGETS[where]}, {SCRIPTS[scripts]}"


CONFIGURATION = _described(HOST, False)
CFG_OFF = "its `#![cfg({})]` is false in the configuration rust-analyzer reads ({})"
MOD_OFF = "the `mod` item that loads it is under `#[cfg({})]`, false in the configuration rust-analyzer reads ({})"
LOADER_OFF = "the file whose `mod` item loads it, {}, is left out: {}"
NO_CRATE = "no crate includes it: no `mod` item of an indexed file loads it"
INACTIVE = "under `#[cfg({})]`, false in the configuration rust-analyzer reads ({}): nothing is written"
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


def _cfg(text: str, where: str = HOST, scripts=False, cfgs=()):
    """The value of a `cfg` predicate in the configuration rust-analyzer read (`where`, `scripts`, the `cfgs` the
    crate's build script set); None where it decides nothing."""
    text = text.strip()
    if re.fullmatch(r'feature\s*=\s*"[^"]*"', text):
        return True
    target = _host() if where == HOST else LINUX
    named = re.fullmatch(r'(\w+)\s*=\s*"([^"]*)"', text)
    if named:
        if named.group(1) in TARGET:
            return target[named.group(1)] == named.group(2)
        return f'{named.group(1)}="{named.group(2)}"' in cfgs if scripts is True else None
    if re.fullmatch(r"\w+", text):
        if text in ("unix", "windows"):
            return text in target
        return None if text in UNDECIDED else text in cfgs if scripts is True else False
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
    values = [_cfg(item, where, scripts, cfgs) for item in [*items, found.group(2)[start:]] if item.strip()]
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


def _off(node, where: str = HOST, scripts=False, cfgs=()) -> str | None:
    """The first `cfg` written before `node` or a node enclosing it that is false in the configuration."""
    while node is not None:
        for predicate in _cfgs(node):
            if _cfg(predicate, where, scripts, cfgs) is False:
                return predicate
        node = node.parent
    return None


def _inside(rel: str, folder: str) -> bool:
    return folder in ("", ".") or rel == folder or rel.startswith(folder + "/")


def _configuration(index, rel: str) -> tuple[str, object, list[str]]:
    """Where rust-analyzer read `rel`, whether the build scripts ran there and the cfgs its crate's set: the run
    whose root holds `rel` nearest, as it wrote beside its index (`<index>.cfg.json`: `failed` its crates whose build
    script failed, `cfgs` each crate's); the host with no build script where nothing says otherwise."""
    owners = [(prefix, Path(path)) for path, prefix in getattr(index, "sources", ()) if _inside(rel, prefix)]
    if not owners:
        return HOST, False, []
    _prefix, path = max(owners, key=lambda item: len(item[0]))
    try:
        said = json.loads(path.with_suffix(".cfg.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return HOST, False, []
    where = said.get("target") or HOST
    if any(_inside(rel, folder) for folder in said.get("failed") or ()):
        return where, "failed", []
    crates = [folder for folder in said.get("cfgs") or {} if _inside(rel, folder)]
    return where, bool(said.get("scripts")), said["cfgs"][max(crates, key=len)] if crates else []


def unanswered(index):
    """Why the index has no occurrence at a site: a `cfg` written before an enclosing item, statement or
    expression is false in the configuration rust-analyzer read the file in (`INACTIVE`)."""
    def cause(position: tuple) -> str | None:
        rel, line, column = position
        tree = index.tree(rel, "rust") if rel.endswith(".rs") and column is not None else None
        if tree is None:
            return None
        where, scripts, cfgs = _configuration(index, rel)
        off = _off(tree.root_node.descendant_for_point_range((line - 1, column), (line - 1, column + 1)), where,
                   scripts, cfgs)
        return INACTIVE.format(off, _described(where, scripts)) if off else None
    return cause


def missing(index, rels: list[str], configs: dict | None = None) -> dict:
    """Why a Rust file has no document: the run of its crate wrote no index and no other run read the crate;
    else no `mod` item of an indexed file loads it, so no crate includes it; else each `mod` item that loads it is
    under a `cfg` false in the configuration rust-analyzer read it in (`MOD_OFF`), or the file's own `#![cfg]` is
    (`CFG_OFF`). A file only files left out load names the one that loads it (`LOADER_OFF`)."""
    roots, failed = set((configs or {}).get("roots") or ()), (configs or {}).get("failed") or {}
    read = {code_graph.owner(rel, roots) for rel in index.documents}
    loaded = collections.defaultdict(list)  # a file a `mod` item loads: the false cfg of each such item, and where
    for rel, name in _mod_items(index):
        where, scripts, cfgs = _configuration(index, rel)
        for candidate in _module_files(rel, name.text.decode("utf-8")):
            loaded[candidate].append((_off(name.parent, where, scripts, cfgs), _described(where, scripts)))
    reasons = {}
    for rel in rels:
        root = code_graph.owner(rel, roots)
        where, scripts, cfgs = _configuration(index, rel)
        tree = index.tree(rel, "rust")
        own = [predicate for predicate in (_cfgs(tree.root_node, inner=True) if tree is not None else ())
               if _cfg(predicate, where, scripts, cfgs) is False]
        if root in failed and root not in read:
            reasons[rel] = f"the rust-analyzer run of its crate {root or '.'} wrote no index ({failed[root]})"
        elif rel not in loaded and PurePosixPath(rel).name not in ("lib.rs", "main.rs", "build.rs") \
                and PurePosixPath(rel).parent.name not in ROOT_DIRECTORIES:
            reasons[rel] = NO_CRATE
        elif rel in loaded and all(off for off, _said in loaded[rel]):
            reasons[rel] = MOD_OFF.format(*loaded[rel][0])
        elif own:
            reasons[rel] = CFG_OFF.format(own[0], _described(where, scripts))
    # A file loaded only by files left out (`#[cfg(target_os = "macos")] mod macos;`, then macos/mod.rs's
    # `mod posit;`): the one that loads it, and the cause that leaves the chain out.
    causes, changed = {rel: reason for rel, reason in reasons.items()}, True
    while changed:
        changed = False
        for rel, name in _mod_items(index, [rel for rel in rels if rel in reasons and rel.endswith(".rs")]):
            for candidate in _module_files(rel, name.text.decode("utf-8")):
                if reasons.get(candidate) == NO_CRATE:
                    causes[candidate] = causes[rel]
                    reasons[candidate], changed = LOADER_OFF.format(rel, causes[rel]), True
    return reasons


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folders of the crates and workspaces (`roots`, for `missing`); the
    container's runs, each Cargo workspace's root and each crate outside one, as Cargo builds them (`boxes`), with
    the Rust a rustup file names (`toolchains`: a `rust-version` is a minimum, never installed)."""
    import premap
    from dynamic import rust as observer
    crates = sorted({observer._folder(unit["root"]) for unit in record.get("units", []) if unit["kind"] in UNIT_KINDS})
    homes = {observer._folder(member): observer._folder(item["root"]) for item in record.get("workspace") or []
             if item.get("tool") == "cargo" for member in item.get("members") or ()}
    boxes = sorted({homes.get(crate, crate) for crate in crates})
    chains = []
    for root in boxes:
        chains += [item for item in observer._toolchain(record.get("toolchains") or [], root) if item not in chains]
    return {"roots": premap.roots(record, UNIT_KINDS, {"cargo"}), "boxes": boxes, "toolchains": chains}


def scripts(boxes: list[str], toolchains: list[dict]) -> tuple[str, str, dict]:
    """The preparation's script, the execution's, and what the preparation needs beside them (`{files, hosts,
    gaps}`): Daodan's Rust with its standard library and sources, else the one a rustup file names with its
    sources; each root's crates fetched; then, with no network, each root's check and index."""
    import container
    from dynamic import rust as observer
    chains = preparation.toolchains(toolchains)
    needs = preparation.setup(["rust"])
    versions = [item["version"] for item in toolchains if item.get("tool") == "rust"][:1]
    sources = [f"{{ rustup component add rust-src --toolchain {version} >&2 ; }} || "
               f"echo 'DAODAN-MISSING rust-src@{version}' >&2" for version in versions if chains["lines"]]
    prepare = ["# rust-analyzer prepare", "set -u", f"mkdir -p {preparation.T}/bin {preparation.ENV['HOME']}",
               f"chmod 755 {ANALYZER}",  # the copy carries a file's bytes, not its mode
               *needs["lines"], observer.STD_SETUP, SRC_SETUP, *chains["lines"], *sources,
               preparation.restore("cargo", boxes)]
    check = f"env RUSTC_WRAPPER={ANALYZER} RA_RUSTC_WRAPPER=1 timeout -k 30 {LIMIT} {CHECK}"
    older = check.replace(" --keep-going", "")
    execute = ["# rust-analyzer execute", "set -u",
               "export CARGO_NET_OFFLINE=true CARGO_TERM_COLOR=never CARGO_TARGET_DIR=/tmp/daodan-rust-target",
               f"OUT={OUT}", "mkdir -p $OUT", f"printf '%s' {shlex.quote(json.dumps(BOXED))} > $OUT/config.json",
               f"{ANALYZER} --version > $OUT/version.txt 2>&1",
               'ls "$(rustc --print sysroot)/libexec" > $OUT/libexec.txt 2>&1']
    for number, root in enumerate(boxes):
        folder, n = shlex.quote(posixpath.normpath(f"{container.WORKDIR}/{root}")), number
        execute += [
            f"( cd {folder} && {check} > $OUT/check-{n}.json 2> $OUT/check-{n}.err; c=$?;"
            f" if [ $c -ne 0 ] && grep -q -- --keep-going $OUT/check-{n}.err; then"
            f" {older} > $OUT/check-{n}.json 2> $OUT/check-{n}.err; c=$?; fi; exit $c ); echo $? > $OUT/check-{n}.code",
            f"s=$(date +%s); ( cd {folder} && timeout -k 30 {LIMIT} {ANALYZER} scip . --output $OUT/index-{n}.scip"
            f" --config-path $OUT/config.json > $OUT/scip-{n}.log 2>&1 ); echo $? > $OUT/scip-{n}.code;"
            f" echo $(( $(date +%s) - s )) > $OUT/scip-{n}.seconds"]
    return ("\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "exit 0"]) + "\n",
            {"files": [*needs["files"], observer.RUST_STD, RUST_SRC, *chains["files"]],
             "hosts": (*needs["hosts"], *chains["hosts"]), "gaps": chains["gaps"]})


FAILED_SCRIPT = re.compile(r"^error: failed to run custom build command for `(\S+) v(\S+)(?: \((.+)\))?`", re.M)
SAID = re.compile(r"(?i)\b(error|not found|failed|missing|could not|cannot|panicked)\b")


def _folder(source: str | None) -> str | None:
    """A source of the copy (`path+file:///work/x`, `/work/x`) as the project's folder, `.` for its root."""
    import container
    path = (source or "").removeprefix("path+file://").split("#")[0]
    if path != container.WORKDIR and not path.startswith(container.WORKDIR + "/"):
        return None
    return posixpath.relpath(path, container.WORKDIR)


def _package(identity: str) -> tuple[str, str, str | None]:
    """`(name, version, folder)` of a Cargo package id: `source#name@version`, `source#version` (the name is the
    folder's), or the older `name version (source)`."""
    if "#" in identity:
        source, _, tail = identity.partition("#")
        name, _, version = tail.rpartition("@")
        return name or source.rstrip("/").rsplit("/", 1)[-1], version, _folder(source)
    name, version, source = (identity.split(" ", 2) + ["", ""])[:3]
    return name, version, _folder(source.strip("()"))


def _cause(block: str) -> str:
    """The words of a failed build script: the first line of its stderr that names an error (with the next one,
    when it ends in a colon), else its first line; else the first of its stdout that names one (system-deps prints
    there), else how the process ended."""
    lines = [line.strip() for line in block.splitlines()]
    said = [line for line in lines[lines.index("--- stderr") + 1:] if line] if "--- stderr" in lines else []
    at = next((i for i, line in enumerate(said) if SAID.search(line)), 0 if said else None)
    if at is None:
        printed = [line.removeprefix("cargo:warning=") for line in lines[lines.index("--- stdout") + 1:]
                   if line and (not line.startswith("cargo:") or line.startswith("cargo:warning="))] \
            if "--- stdout" in lines else []
        said, at = printed, next((i for i, line in enumerate(printed) if SAID.search(line)), None)
    if at is None:
        ended = next((line for line in lines if line.startswith("process didn't exit")), "no output")
        return re.sub(r"`[^`]*/build-script-build`", "its build script", ended)
    line = said[at] + (f" {said[at + 1]}" if said[at].endswith(":") and at + 1 < len(said) else "")
    return line.rstrip(".")[:300]


def built(root: str, stdout: str, stderr: str, code: int | None) -> tuple[list[dict], list[str], dict]:
    """The gaps of one root's check, the folders of its crates read as with build scripts off, and the cfgs each
    of its crates' build scripts set (`{folder: [cfg]}`): a gap for each build script that failed (cargo's words on
    stderr) or did not build, each procedural macro that did not build (its compiler message), and the root itself
    when the check ran nothing at all."""
    messages = []
    for line in stdout.splitlines():
        try:
            messages.append(json.loads(line))
        except ValueError:
            continue
    gaps, failed, seen, cfgs = [], [], set(), {}
    for message in messages:
        if message.get("reason") == "build-script-executed":
            folder = _package(message.get("package_id") or "")[2]
            if folder:
                cfgs[folder] = sorted(set(message.get("cfgs") or ()))
    for found in FAILED_SCRIPT.finditer(stderr):
        name, version, source = found.groups()
        block = stderr[found.end():]
        following = re.search(r"^(error|warning): ", block, re.M)
        folder = _folder(source)
        if folder and folder not in failed:
            failed.append(folder)
        seen.add((name, version))
        gaps.append({"kind": "build_script_failed", "path": folder or root, "detail": (
            f"the build script of {name} {version} failed: "
            f"{_cause(block[:following.start()] if following else block)}: {FALLBACK.format(name)}")})
    for message in messages:
        said, kinds = message.get("message") or {}, (message.get("target") or {}).get("kind") or []
        if message.get("reason") != "compiler-message" or said.get("level") != "error" or not (
                {"proc-macro", "custom-build"} & set(kinds)):
            continue
        name, version, folder = _package(message.get("package_id") or "")
        if (name, version) in seen:
            continue
        seen.add((name, version))
        if "proc-macro" in kinds:
            gaps.append({"kind": "proc_macro_not_built", "path": folder or root, "detail": (
                f"the procedural macro {name} {version} did not build: {said.get('message')}: {UNEXPANDED}")})
        else:
            if folder and folder not in failed:
                failed.append(folder)
            gaps.append({"kind": "build_script_failed", "path": folder or root, "detail": (
                f"the build script of {name} {version} did not build: {said.get('message')}: {FALLBACK.format(name)}")})
    if code and not messages and not gaps:
        words = [line.strip() for line in stderr.splitlines() if line.strip()]
        first = next((line for line in words if line.startswith("error")), words[-1] if words else "no output")
        failed.append(root)
        gaps.append({"kind": "build_scripts_not_run", "path": root, "detail": (
            f"cargo check in {root} ran no build script (exit code {code}): {first[:300]}: {FALLBACK.format(root)}")})
    return gaps, failed, cfgs


def _analyzer() -> Path:
    """The pinned rust-analyzer for Linux on the container's architecture, downloaded once into the shared
    directory and checked by its release's sha256."""
    import gzip
    import container
    import engine_tools
    architecture = container.architecture()
    asset, digest = engine_tools.RUST_ANALYZER_ASSETS[f"linux-{architecture}"]
    home = engine_tools.shared_engine_dir("rust-analyzer-linux") / engine_tools.RUST_ANALYZER_RELEASE
    binary = home / f"rust-analyzer-{architecture}"
    if binary.is_file():
        return binary
    home.mkdir(parents=True, exist_ok=True)
    try:
        archive = engine_tools.download("https://github.com/rust-lang/rust-analyzer/releases/download/"
                                        f"{engine_tools.RUST_ANALYZER_RELEASE}/rust-analyzer-{asset}", home / asset,
                                        sha256=digest)
        partial = binary.with_suffix(".partial")
        with gzip.open(archive) as source, partial.open("wb") as target:
            shutil.copyfileobj(source, target)
        archive.unlink()
        os.replace(partial, binary)
    except (OSError, ValueError) as error:
        raise container.Gap(f"rust-analyzer {engine_tools.RUST_ANALYZER_RELEASE} for Linux could not be downloaded "
                            f"and verified: {error}", "check the connection to github.com") from error
    return binary


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _code(path: Path) -> int | None:
    text = _text(path).strip()
    return int(text) if text.lstrip("-").isdigit() else None


def _boxed(project_dir: Path, work_dir: Path, boxes: list[str], toolchains: list[dict], declared: dict,
           engine) -> dict:
    """One container run: each root's check and index (`scripts`), read back. `{runs, gaps, build}`, a run per root,
    with no index where rust-analyzer wrote none; without the container run, `{state, reason, gaps}`."""
    import container
    out = work_dir / "container"
    shutil.rmtree(out, ignore_errors=True)
    prepare, execute, needs = scripts(boxes, toolchains)

    def inputs() -> dict:
        return {ANALYZER: _analyzer(), **{f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                                          for url, digest, name in needs["files"]}}

    result = container.run_in_container(
        project_dir, ["sh", "-c", execute], image=IMAGE, out_dir=out, prepare=["sh", "-c", prepare], outputs=[OUT],
        env=preparation.ENV, timeout=BUILD + len(boxes) * 2 * LIMIT, memory=MEMORY, engine=engine, inputs=inputs,
        registries=container.REGISTRIES + tuple(dict.fromkeys([*needs["hosts"], *declared.get("hosts", ())])))
    if result["state"] == "gap":
        return {"state": "unavailable", "reason": f"rust-analyzer runs only in Daodan's container: {result['cause']}",
                "install": result["remedy"], "gaps": []}
    prepared = _text(out / "prepare.log")
    gaps = [*needs["gaps"], *preparation.missing(prepared), *preparation.restore_gaps(prepared),
            *(result.get("gaps") or ())]  # and what the copy left out (`container.copy_perimeter`)
    if result["state"] != "done":
        return {"state": "failed", "gaps": gaps, "reason": f"the container run of rust-analyzer ended {result['state']}"
                + (f": {result['cause']}" if result.get("cause") else "") + f" (see the logs in {out})"}
    back = out / Path(OUT).name
    if "rust-analyzer-proc-macro-srv" not in _text(back / "libexec.txt"):
        gaps.append({"kind": "proc_macros_not_expanded", "detail": NO_SERVER})
    runs = []
    for number, root in enumerate(boxes):
        failures, failed, cfgs = built(root, _text(back / f"check-{number}.json"),
                                       _text(back / f"check-{number}.err"), _code(back / f"check-{number}.code"))
        gaps += failures
        written, code, log = back / f"index-{number}.scip", _code(back / f"scip-{number}.code"), \
            _text(back / f"scip-{number}.log")
        target = work_dir / f"rust-analyzer-box-{number}.scip"
        indexed = code == 0 and written.is_file()
        if indexed:
            os.replace(written, target)
            said = {"target": CONTAINER, "scripts": True, "failed": failed, "cfgs": cfgs}
            target.with_suffix(".cfg.json").write_text(json.dumps(said), encoding="utf-8")
        errors = [line[line.find(" ERROR ") + 7:][:200] for line in log.splitlines() if " ERROR " in line]
        runs.append({"prefix": "" if root == "." else root, "returncode": code,
                     "command": [ANALYZER, "scip", ".", "--config-path", "config.json"],
                     "seconds": float(_code(back / f"scip-{number}.seconds") or 0), "peak_mb": None,
                     "stdout_tail": "", "stderr_tail": log[-2500:], "stderr_errors": len(errors),
                     "stderr_error_examples": list(dict.fromkeys(errors))[:5], "image": IMAGE,
                     "index": str(target) if indexed else None,
                     "index_bytes": target.stat().st_size if indexed else 0})
    return {"runs": runs, "gaps": gaps, "build": _text(back / "version.txt").strip() or None}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, roots: set[str], boxes=(),
          toolchains=(), declared: dict | None = None, engine=None) -> dict:
    """The rust-analyzer index of each of `boxes` in Daodan's container, with the engine the pass found
    (`NEEDS_CONTAINER`) and the hosts the project declares (`declared`); `roots` the folders of the crates and
    workspaces as the pre-map names them (`structure`). Nothing of it runs on the host."""
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    if not boxes:
        return runtime.refused("rust-analyzer", rx.RUST_ANALYZER_RELEASE, runtime.Unavailable(
            "the pre-map names no Cargo package: no crate to index", "none: the Rust files keep their static facts"))
    boxed = _boxed(project_dir, work_dir, list(boxes), list(toolchains), declared or {}, engine)
    if "state" in boxed:
        return {"indexes": [], "runs": [], "indexer": code_graph.indexer("rust-analyzer", rx.RUST_ANALYZER_RELEASE,
                                                                           []), **boxed}
    runs = boxed["runs"]
    rust = next((item["version"] for item in toolchains if item.get("tool") == "rust"),
                preparation.NEEDS["rust"]["version"])
    # Named by its pinned release, like every indexer; `build` is what the binary states; `configs` is for `tasks`.
    return {**runtime.outcome("rust-analyzer", rx.RUST_ANALYZER_RELEASE, runs), "build": boxed["build"],
            "toolchain": rust, "config": BOXED, "image": IMAGE,
            "configs": {"roots": sorted(roots), "failed": {run["prefix"]: f"exit code {run['returncode']}"
                                                           for run in runs if not run["index"]}},
            **({"gaps": boxed["gaps"]} if boxed["gaps"] else {})}
