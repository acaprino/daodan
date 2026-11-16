"""scip-go: how it runs, and the aliases its index states its own way.

`index` runs scip-go, built once with Daodan's Go (`go install` at `VERSION`, checked by Go's checksum
database), in a mirror of the project where every directory holding a Go file is real: at the root, then in
each nested module holding files the root run left out, after `go mod download` there, with Go's ignored
directories (`_x`, `.x`, `testdata`) named as explicit packages. No project code runs: `go list` and the type
checker only read it.

A file the indexer's build leaves out (its `//go:build` line or its name rules out the build's GOOS, GOARCH,
cgo or tags) is indexed by a further run under the configuration nearest that build which builds it
(`configuration`), once `go list` there lists it; a file only the `ignore` tag builds is a program `go run`
names, indexed as one. Such a run indexes the file's whole package: only the left-out files' documents are
kept. A cgo file has no document (scip-go indexes the copy cgo writes into the build cache), nor has a file no
configuration builds, nor one past `PASSES` further runs: `missing` says which.

Interface implementations need no hop: scip-go states them in `SymbolInformation` (`is_implementation`), which
the shared traversal follows for members. `hops` reads the statement that defines a name: `x := y.z`,
`var x = y` lead to the symbol the index references at the value, position by position; a function literal
leads to the function the snapshot declares there. `prepare` gives what Go's universe scope declares (`len`, a
conversion `string(b)`, `err.Error` of the predeclared `error`), which scip-go writes no occurrence of, the
symbol of Go's `builtin` package: an external end.
"""
from __future__ import annotations

import collections
import itertools
import json
import os
import platform
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

import code_graph

VERSION = "v0.2.9"  # github.com/scip-code/scip-go
# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-go", ("go",), frozenset({"go-module"}), False
MIN_FREE = 512 * 2**20  # 335 MB peak on chi (benchmarks/inference-audit, 13 November 2026)
PARAMETERS = {"parameter_declaration", "variadic_parameter_declaration"}
# The operating systems and architectures a file's name restricts it to (go/build's lists, Go 1.27).
GOOS = frozenset("aix android darwin dragonfly freebsd hurd illumos ios js linux nacl netbsd openbsd plan9 solaris "
                 "wasip1 windows zos".split())
GOARCH = frozenset("386 amd64 amd64p32 arm armbe arm64 arm64be loong64 mips mipsle mips64 mips64le mips64p32 "
                   "mips64p32le ppc ppc64 ppc64le riscv riscv64 s390 s390x sparc sparc64 wasm".split())
# Go's universe scope (go/types): its functions and types belong to no package, and scip-go writes no occurrence
# of them; `prepare` gives them the symbols of Go's `builtin` package, which documents them.
FUNCTIONS = frozenset("append cap clear close complex copy delete imag len make max min new panic print println "
                      "real recover".split())
TYPES = frozenset("any bool byte comparable complex64 complex128 error float32 float64 int int8 int16 int32 int64 "
                  "rune string uint uint8 uint16 uint32 uint64 uintptr".split())
STDLIB = "scip-go gomod github.com/golang/go/src "  # the scheme and package of the standard library's symbols
DIRECTIVE = re.compile(r"(?m)^go\s+(\S+)")
# The configurations a left-out file is tried under, nearest the indexer's build first: GOOS and GOARCH in this
# order (the go tool's first-class ports first), and what each tag of a build means (go/build's matchTag).
GOOS_ORDER = ("linux", "windows", "darwin", "freebsd", "openbsd", "netbsd", "dragonfly", "solaris", "illumos", "aix",
              "android", "ios", "plan9", "js", "wasip1")
GOARCH_ORDER = ("amd64", "arm64", "386", "arm", "riscv64", "ppc64le", "ppc64", "s390x", "mips64le", "mips64",
                "mipsle", "mips", "loong64", "wasm")
UNIX = frozenset("aix android darwin dragonfly freebsd hurd illumos ios linux netbsd openbsd solaris".split())
IMPLIES = {"android": "linux", "illumos": "solaris", "ios": "darwin"}  # a GOOS that builds another's files too
RESERVED = GOOS | GOARCH | {"cgo", "unix", "gc", "gccgo"}
TOKENS = re.compile(r"\(|\)|!|&&|\|\||[^\s()!&|]+")
CGO = re.compile(r'(?m)^import\s+"C"\s*$')
CGO_COPY = 'a cgo file (`import "C"`): scip-go indexes the copy cgo writes into the build cache, not the file'
PASSES = 8  # the further runs one index takes


def _positional(names: list, node, values) -> tuple[str, object]:
    """Go binds by position: the value at the name's index, or the one call that returns them all."""
    items = values.named_children if values is not None else []
    at = next((i for i, name in enumerate(names) if name == node), None)
    if at is not None and len(items) == len(names):
        return "value", items[at]
    return ("destructured", items[0]) if len(items) == 1 else ("none", None)


def _defining_value(node) -> tuple[str, object]:
    parent = node.parent
    if parent is None:
        return "none", None
    if parent.type == "expression_list" and parent.parent is not None \
            and parent.parent.type == "short_var_declaration" and parent.parent.child_by_field_name("left") == parent:
        return _positional(parent.named_children, node, parent.parent.child_by_field_name("right"))
    if parent.type in ("var_spec", "const_spec"):
        return _positional(parent.children_by_field_name("name"), node, parent.child_by_field_name("value"))
    if parent.type in PARAMETERS:
        return "parameter", None
    return "none", None


def _value(index, rel: str, value) -> list:
    while value is not None and value.type == "parenthesized_expression":
        value = value.named_children[0] if value.named_children else None
    if value is None:
        return []
    if value.type == "func_literal":
        return [((rel, value.start_point[0] + 1, value.start_point[1]), "value")]
    name = value if value.type == "identifier" else value.child_by_field_name("field") \
        if value.type == "selector_expression" else None
    return [(key, "initializer") for key in index.stated(rel, name)] if name is not None else []


def hops(index) -> dict:
    """Alias edges from the statements that define the names of Go documents."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        if not rel.endswith(".go"):
            continue
        for occurrence in occurrences:
            if not occurrence.definition or occurrence.key.endswith(("#", ").", "/", ")")):
                continue
            node = index.node(rel, occurrence, "go")
            if node is None:
                continue
            form, value = _defining_value(node)
            if form == "value" and value is not None:
                out[occurrence.key] += [item for item in _value(index, rel, value) if item[0] != occurrence.key]
    return {key: list(dict.fromkeys(items)) for key, items in out.items() if items}


def _builtin(parts: list) -> str | None:
    """The descriptor in Go's `builtin` package of what a reference names in the universe scope, None for any
    other name: `len` is `builtin/len().`, a conversion `string(b)` `builtin/string#`, and a method `Error` the
    index holds nothing at is that of the predeclared `error`, the one type of the scope with a method."""
    if len(parts) == 1:
        name = parts[0]
        return f"builtin/{name}()." if name in FUNCTIONS else f"builtin/{name}#" if name in TYPES else None
    return "builtin/error#Error()." if parts and parts[-1] == "Error" else None


def _stdlib(index, rel: str) -> str | None:
    """The version of Go's standard library the document `rel` links to: the one its own occurrences name, else
    the `go` directive of the go.mod above it, as scip-go names it (`go1.22`)."""
    for occurrence in index.documents.get(rel, ()):
        if occurrence.key.startswith(STDLIB):
            return occurrence.key[len(STDLIB):].split(" ", 1)[0]
    folder = PurePosixPath(rel).parent
    while True:
        manifest = index.root / folder / "go.mod"
        if manifest.is_file():
            found = DIRECTIVE.search(manifest.read_text(encoding="utf-8", errors="replace"))
            return f"go{found.group(1)}" if found else None
        if folder == folder.parent:
            return None
        folder = folder.parent


def prepare(index, snapshot) -> dict:
    """An occurrence where a reference of an indexed document names Go's universe scope and the index holds
    nothing (`_builtin`), with the symbol of Go's `builtin` package in the standard library the document links
    to: an external end, which scip-go leaves out. `{"builtins": how many}`."""
    added, versions = 0, {}
    for _identity, rel, _kind, _resolution, _target, span, parts, _reason in snapshot.references("go"):
        checkout = snapshot.checkout.get(rel, rel)
        descriptor = _builtin(parts) if checkout in index.documents else None
        site = snapshot.callee(rel, span, parts) if descriptor else None
        start = index.from_bytes(checkout, site[0], site[1]) if site else None
        if start is None or index.at.get((checkout, site[0], start)):
            continue
        if checkout not in versions:
            versions[checkout] = _stdlib(index, checkout)
        if versions[checkout] is None:
            continue
        occurrence = code_graph.Occurrence(site[0], start, site[0], start + len(parts[-1]),
                                           f"{STDLIB}{versions[checkout]} {descriptor}", False, None)
        index.documents[checkout].append(occurrence)
        index.at[(checkout, site[0], start)].append(occurrence)
        added += 1
    return {"builtins": added}


def tasks(configs) -> dict:
    """What the run brought back for `missing`: `{"roots": [folder], "failed": {folder: how its run ended},
    "constraints": {file: why no run indexed it}}`, empty without it."""
    return configs if isinstance(configs, dict) else {}


def _target() -> tuple[str, str]:
    """GOOS and GOARCH of the indexer's build: the environment's, else Go's defaults, the machine's."""
    system = {"win32": "windows", "darwin": "darwin"}.get(sys.platform, "linux")
    machine = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "amd64"
    return os.environ.get("GOOS") or system, os.environ.get("GOARCH") or machine


def _named(rel: str) -> list[str]:
    """The GOOS and GOARCH a file's name restricts it to, as go/build reads names: the last words after the
    first underscore, `_test` aside (`x_linux.go`, `x_windows_amd64_test.go`; `linux.go` names none)."""
    words = PurePosixPath(rel).stem.split("_")[1:]
    if words[-1:] == ["test"]:
        words.pop()
    if len(words) >= 2 and words[-2] in GOOS and words[-1] in GOARCH:
        return words[-2:]
    return words[-1:] if words and words[-1] in GOOS | GOARCH else []


NO_MODULE = ("no Go module holds it: no go.mod in its folder or above, and the go tool builds a package only in a"
             " module (a build that writes one, `go mod init` in a Dockerfile, is not the project's declaration)")


def missing(index, rels: list[str], configs: dict | None = None) -> dict:
    """Why a Go file has no document: no module holds it, the run of its module wrote no index, a build
    constraint, or a file name the indexer's build leaves out."""
    roots, failed = set((configs or {}).get("roots") or ()), (configs or {}).get("failed") or {}
    constraints, docker = (configs or {}).get("constraints") or {}, (configs or {}).get("docker") or {}
    read = {code_graph.owner(rel, roots) for rel in index.documents}
    reasons, target = {}, _target()
    for rel in rels:
        root, named = code_graph.owner(rel, roots), _named(rel)
        if root is None and "roots" in (configs or {}):
            if rel not in index.documents:  # a Dockerfile's build stage indexes it, or says why not (`_docker`)
                reasons[rel] = docker.get(rel, NO_MODULE)
            continue
        if root in failed and root not in read:
            reasons[rel] = f"the scip-go run of its module {root or '.'} wrote no index ({failed[root]})"
            continue
        if rel in constraints:
            reasons[rel] = constraints[rel]
            continue
        try:
            head = (index.root / rel).read_text(encoding="utf-8", errors="replace").split("\n")[:20]
        except OSError:
            head = []
        constraint = next((line.strip() for line in head if line.startswith("//go:build")), None)
        if constraint:
            reasons[rel] = f"build constraint `{constraint}`"
        elif any(word not in target for word in named):
            reasons[rel] = f"file name constraint `{'_'.join(named)}`: the indexer's build is {'/'.join(target)}"
    return reasons


def _constraint(text: str) -> str | None:
    """The `//go:build` line of a Go file's source, None without one: it stands before the package clause."""
    for line in text.split("\n"):
        if line.startswith("//go:build"):
            return line.strip()
        if line.startswith("package "):
            return None
    return None


def _parse(expression: str):
    """A `//go:build` expression as nested tuples (`("!", x)`, `("&&", a, b)`, `("||", a, b)`, a tag), None
    when it does not parse."""
    tokens, at = TOKENS.findall(expression), [0]

    def peek():
        return tokens[at[0]] if at[0] < len(tokens) else None

    def take():
        at[0] += 1
        return tokens[at[0] - 1]

    def either():
        tree = both()
        while peek() == "||":
            take()
            tree = ("||", tree, both())
        return tree

    def both():
        tree = unary()
        while peek() == "&&":
            take()
            tree = ("&&", tree, unary())
        return tree

    def unary():
        token = take()
        if token == "!":
            return "!", unary()
        if token == "(":
            tree = either()
            if take() != ")":
                raise ValueError(expression)
            return tree
        if token in (")", "&&", "||"):
            raise ValueError(expression)
        return token

    try:
        tree = either()
    except (IndexError, ValueError):
        return None
    return tree if at[0] == len(tokens) else None


def _holds(tree, holds) -> bool:
    if isinstance(tree, str):
        return holds(tree)
    if tree[0] == "!":
        return not _holds(tree[1], holds)
    left, right = _holds(tree[1], holds), _holds(tree[2], holds)
    return left and right if tree[0] == "&&" else left or right


def _tag(tag: str, goos: str, goarch: str, cgo: bool, tags, minor: int) -> bool:
    """Whether a build of that configuration satisfies `tag`, as go/build matches one."""
    if tag in tags or tag in (goos, goarch) or IMPLIES.get(goos) == tag:
        return True
    if tag in ("unix", "cgo", "gc"):
        return goos in UNIX if tag == "unix" else cgo if tag == "cgo" else True
    found = re.fullmatch(r"go1\.(\d+)", tag)
    return bool(found) and int(found.group(1)) <= minor


def configuration(rel: str, text: str, target: tuple[str, str], cgo: bool) -> dict | None:
    """The configuration nearest the indexer's build (`target`: its GOOS and GOARCH; `cgo`: whether it has cgo)
    that builds the Go file `rel` of source `text`, as its name and its `//go:build` line say: `{GOOS, GOARCH,
    CGO_ENABLED, tags}`, the build's own when it builds the file; `{"program": rel}` for a file only the `ignore`
    tag builds, a program `go run` names; None when none builds it. Nearest: the fewest of GOOS, GOARCH, cgo and
    the tags changed, then GOOS and GOARCH in the order of `GOOS_ORDER` and `GOARCH_ORDER`."""
    import resolve_edges as rx
    minor, line, named = int(rx.GO_VERSION.split(".")[1]), _constraint(text), _named(rel)
    expression = line[len("//go:build"):] if line else ""
    tree = _parse(expression) if line else None
    if line and tree is None:
        return None
    custom = sorted({tag for tag in TOKENS.findall(expression) if tag not in ("(", ")", "!", "&&", "||")
                     and tag not in RESERVED and not re.fullmatch(r"go1\.\d+", tag)
                     and not tag.startswith("goexperiment.")})
    sets = [combo for size in range(len(custom) + 1) for combo in itertools.combinations(custom, size)] \
        if len(custom) <= 6 else [(), tuple(custom)]
    systems = [target[0], *(goos for goos in GOOS_ORDER if goos != target[0])]
    machines = [target[1], *(goarch for goarch in GOARCH_ORDER if goarch != target[1])]
    best = None
    for tags in sets:
        for i, goos in enumerate(systems):
            if any(word in GOOS and word not in (goos, IMPLIES.get(goos)) for word in named):
                continue
            for j, goarch in enumerate(machines):
                if any(word in GOARCH and word != goarch for word in named):
                    continue
                for flip, on in enumerate((cgo, not cgo)):
                    if tree is not None and not _holds(tree, lambda tag: _tag(tag, goos, goarch, on, tags, minor)):
                        continue
                    rank = ((i > 0) + (j > 0) + flip + len(tags), i, j, flip, tags)
                    if best is None or rank < best[0]:
                        best = (rank, goos, goarch, on, tags)
    if best is None:
        return None
    _rank, goos, goarch, on, tags = best
    if "ignore" in tags:
        return {"program": rel}
    return {"GOOS": goos, "GOARCH": goarch, "CGO_ENABLED": "1" if on else "0", "tags": list(tags)}


def _label(config: dict, target: tuple[str, str], cgo: bool) -> str:
    """What a configuration changes in the indexer's build, as the go tool's variables and flags say it; empty
    for that build's own."""
    if "program" in config:
        return f"go run {config['program']}"
    changed = [f"{name}={config[name]}" for name, own in (("GOOS", target[0]), ("GOARCH", target[1]),
                                                          ("CGO_ENABLED", "1" if cgo else "0")) if config[name] != own]
    return " ".join([*changed, *([f"-tags={','.join(config['tags'])}"] if config["tags"] else [])])


def _environment(env: dict, config: dict) -> dict:
    if "program" in config:
        return env
    flags = [env.get("GOFLAGS", ""), f"-tags={','.join(config['tags'])}" if config["tags"] else ""]
    return {**env, "GOOS": config["GOOS"], "GOARCH": config["GOARCH"], "CGO_ENABLED": config["CGO_ENABLED"],
            "GOFLAGS": " ".join(flag for flag in flags if flag)}


def _patterns(prefix: str, rels: list[str], config: dict) -> list[str]:
    """What a further run names, from its module's folder: a program's file, else the files' packages."""
    inner = [rel[len(prefix) + 1:] if prefix else rel for rel in rels]
    if "program" in config:
        return [f"./{inner[0]}"]
    return sorted({f"./{posixpath.dirname(rel)}" if posixpath.dirname(rel) else "." for rel in inner})


def _cgo(go: str, env: dict, cwd: Path) -> bool:
    """Whether the indexer's build has cgo (`go env CGO_ENABLED`: 0 where no C compiler is found)."""
    try:
        done = subprocess.run([go, "env", "CGO_ENABLED"], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return False
    return (done.stdout or "").strip() == "1"


def _listed(go: str, env: dict, cwd: Path, patterns: list[str], bases) -> dict[str, set]:
    """The Go files `go list` puts in each package of `patterns` under `env`, tests included and cgo files aside
    (scip-go reads their copies), by the package's folder from the first of `bases` that holds it."""
    try:
        done = subprocess.run([go, "list", "-e", "-json", *patterns], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError):
        return {}
    out, text, at, decoder = collections.defaultdict(set), done.stdout or "", 0, json.JSONDecoder()
    bases = [Path(base).resolve() for base in bases]
    while True:
        while at < len(text) and text[at].isspace():
            at += 1
        if at >= len(text):
            return out
        try:
            item, at = decoder.raw_decode(text, at)
        except ValueError:
            return out
        folder = None
        for base in bases:
            try:
                folder = Path(item["Dir"]).resolve().relative_to(base).as_posix()
                break
            except (KeyError, TypeError, ValueError):
                continue
        if folder is not None:
            for key in ("GoFiles", "TestGoFiles", "XTestGoFiles"):
                out[folder] |= set(item.get(key) or ())


def _document_path(value: bytes) -> str:
    return next((part.decode("utf-8", "replace").replace("\\", "/") for field, kind, part in code_graph._fields(value)
                 if field == 1 and kind == 2), "")


def _covered(runs: list[dict], mirror: Path) -> set[str]:
    """The files the runs' indexes hold a document of, named as `code_graph.Index.load` names them."""
    out = set()
    for run in runs:
        if run.get("index"):
            for number, wire, value in code_graph._fields(Path(run["index"]).read_bytes()):
                if number == 2 and wire == 2:
                    rel, prefix = _document_path(value), run["prefix"]
                    out.add(f"{prefix}/{rel}" if prefix and not (Path(mirror) / rel).is_file() else rel)
    return out


def _encoded(number: int, value: bytes) -> bytes:
    """A length-delimited protobuf field."""
    out = bytearray()
    for item in (number << 3 | 2, len(value)):
        while True:
            byte, item = item & 0x7F, item >> 7
            out.append(byte | 0x80 if item else byte)
            if not item:
                break
    return bytes(out) + value


def _keep(path: Path, names: set[str]) -> int:
    """Rewrite the SCIP index at `path` with only the documents named in `names`, its other fields as they are;
    the number of documents kept."""
    out, kept = bytearray(), 0
    for number, wire, value in code_graph._fields(path.read_bytes()):
        if wire != 2:  # an index holds length-delimited fields only
            continue
        if number == 2:
            if _document_path(value) not in names:
                continue
            kept += 1
        out += _encoded(number, value)
    path.write_bytes(bytes(out))
    return kept


def _configured(go: str, scip_go: str, env: dict, project: Path, mirror: Path, work_dir: Path, files: list[str],
                roots: set[str], runs: list[dict]) -> tuple[list[dict], dict]:
    """The further runs for the Go files `runs` left out because the indexer's build does, and `{file: why}` for
    the files no run indexed: see the module's docstring."""
    covered, target, cgo = _covered(runs, mirror), _target(), None
    groups, reasons, said = {}, {}, {}
    for rel in files:
        if rel in covered or "vendor" in rel.split("/")[:-1]:
            continue
        try:
            text = (Path(project) / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        line, named, prefix = _constraint(text), _named(rel), code_graph.owner(rel, roots)
        if CGO.search(text):
            reasons[rel] = CGO_COPY
            continue
        if prefix is None or not (line or named):
            continue  # left out for another reason: `missing` says which
        if cgo is None:
            cgo = _cgo(go, env, mirror)
        said[rel] = f"build constraint `{line}`" if line else f"file name constraint `{'_'.join(named)}`"
        config = configuration(rel, text, target, cgo)
        if config is None:
            reasons[rel] = f"{said[rel]}: no GOOS, GOARCH, cgo and tags build it"
            continue
        label = _label(config, target, cgo)
        if label:  # the indexer's own build builds it: it is left out for another reason
            groups.setdefault((prefix, label), (config, []))[1].append(rel)
    out = []
    for (prefix, label), (config, rels) in groups.items():
        if len(out) >= PASSES:
            reasons.update({rel: f"{said[rel]}: not indexed, the further runs of one index stop at {PASSES}"
                            for rel in rels})
            continue
        here, patterns = _environment(env, config), _patterns(prefix, rels, config)
        listed = _listed(go, here, Path(mirror) / prefix, patterns, (mirror, project))
        wanted = [rel for rel in rels if PurePosixPath(rel).name in listed.get(posixpath.dirname(rel) or ".", ())]
        reasons.update({rel: f"{said[rel]}: `go list` under {label} does not list it" for rel in rels
                        if rel not in wanted})
        if not wanted:
            continue
        output = Path(work_dir) / f"scip-go-{len(runs) + len(out)}.scip"
        run = {"prefix": prefix, "configuration": label, **code_graph.measured(
            [scip_go, f"--output={output}", *patterns], str(Path(mirror) / prefix), here, 3 * 3600)}
        names = {name for rel in wanted for name in (rel, rel[len(prefix) + 1:] if prefix else rel)}
        kept = _keep(output, names) if output.is_file() else 0
        run["index"], run["index_bytes"] = (str(output), output.stat().st_size) if kept else (None, 0)
        out.append(run)
        got = _covered([run], mirror)
        reasons.update({rel: f"{said[rel]}: the scip-go run under {label} wrote no document of it (exit code "
                             f"{run['returncode']})" for rel in wanted if rel not in got})
    return out, reasons


def _build(go: str, env: dict, partial: Path, work_dir: Path) -> None:
    """scip-go into `partial`, its sources and build cache in a scratch directory removed after, with at most
    `go_jobs` compilers at once."""
    import resolve_edges as rx
    scratch = Path(tempfile.mkdtemp(prefix="scip-go-build-", dir=work_dir))
    try:
        build = {**env, "GOBIN": str(partial), "GOPATH": str(scratch / "path"), "GOCACHE": str(scratch / "cache"),
                 "GOFLAGS": ""}
        subprocess.run([go, "install", "-p", rx.go_jobs(), f"github.com/scip-code/scip-go/cmd/scip-go@{VERSION}"],
                       check=True, env=build, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1800)
    finally:
        # Go makes its module cache read-only.
        shutil.rmtree(scratch, onexc=lambda function, path, _error: (os.chmod(path, 0o700), function(path)))


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folders it runs in, and the Dockerfiles as BuildKit reads them."""
    import premap
    builds = record.get("docker_builds") or []
    return {"roots": premap.roots(record, UNIT_KINDS, {"go"}), **({"docker": builds} if builds else {})}


GO_BUILD = r"\bgo\s+(build|install)\b"  # the RUN of a Dockerfile's stage that builds its Go module
SCIP_GO_OUT = "/daodan/out"


PROGRESS = re.compile(r"go: (downloading|creating|finding|added|upgraded|found|to add|extracting) |"
                      r"go: module \S+ is deprecated|^\s*go mod tidy$|\simports$")  # what the go command says on the way


def _first_error(log: str, marker: int) -> str:
    """The go command's first error line before `marker` in a preparation's log (`dispatch imports` /
    `<package> imports` / the error: the error), else its last line."""
    lines = [line for line in log[:marker].splitlines() if line.strip()]
    found = next((line for line in lines if not PROGRESS.search(line)), None)
    return (found or (lines[-1] if lines else "")).rstrip()[:400]


def _docker(project: Path, work_dir: Path, files: list[str], roots: set[str], builds) -> tuple[list[dict], dict, list]:
    """The runs for the Go files no module holds that a Dockerfile's build stage copies in: its steps up to its
    `go build` or `go install` in the preparation (`docker_build.plan`), with scip-go built there with Daodan's
    Go; scip-go then runs offline where the build would, on the module and the module cache the steps left, and
    its documents name the checkout's files. Each run carries the Dockerfile, the stage and the `go.mod` and
    `go.sum` the steps resolved (`go get` resolves at run time). Also `{file: why}` for the files whose stage is
    not reproduced or did not run, and the gaps of a step that failed."""
    import docker_build
    import preparation
    outside = [rel for rel in files if code_graph.owner(rel, roots) is None]
    runs, reasons, gaps = [], {}, []
    for build in builds if outside else ():
        plan = docker_build.plan(build, project, outside, GO_BUILD)
        if plan is None:
            continue
        covered = sorted(set(plan["copies"].values()) & set(outside))
        if plan["gaps"]:
            first = plan["gaps"][0]
            reasons.update({rel: f"no Go module holds it, and its Dockerfile's build stage is not reproduced: "
                                 f"{first['path']}: {first['detail']}" for rel in covered})
            gaps += plan["gaps"]
            continue
        setup = [f"mkdir -p {preparation.T}/bin", *preparation.NEEDS["go"]["setup"],
                 f"GOBIN={preparation.T}/bin GOPATH={preparation.STATE}/scip-go"
                 f" GOCACHE={preparation.STATE}/scip-go-cache GOFLAGS= GOTOOLCHAIN=local {preparation.T}/go/bin/go"
                 f" install github.com/scip-code/scip-go/cmd/scip-go@{VERSION}",
                 f"( cd {shlex.quote(plan['workdir'])} && mkdir -p {SCIP_GO_OUT}/resolved"
                 f" && cp go.mod go.sum {SCIP_GO_OUT}/resolved/ ) || true"]
        out_dir = Path(work_dir) / f"docker-{len(runs)}"
        started = time.monotonic()
        result = docker_build.run(project, out_dir, plan, ["env", "GOPROXY=off", f"{preparation.T}/bin/scip-go",
                                                           f"--output={SCIP_GO_OUT}/index.scip", "./..."],
                                  setup=setup, files=preparation.NEEDS["go"]["files"], outputs=[SCIP_GO_OUT],
                                  timeout=1800)
        log = out_dir / "prepare.log"
        said = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        step = docker_build.failed_step(plan, build, said, _first_error)
        if step:
            reasons.update({rel: f"no Go module holds it: {step['path']} `{step['original']}` failed: "
                                 f"{step['error']}" for rel in covered})
            gaps += step["gaps"]
            continue
        if result["state"] != "done":
            last = docker_build.last_line(said).strip()
            reasons.update({rel: f"no Go module holds it, and its Dockerfile's build stage did not run: "
                                 f"{result.get('cause')}" + (f": {last}" if last else "") for rel in covered})
            continue
        written, index = out_dir / "out" / "index.scip", Path(work_dir) / f"scip-go-docker-{len(runs)}.scip"
        kept = docker_build.rewritten(written, plan, index) if written.is_file() else 0
        resolved = {name: (out_dir / "out" / "resolved" / name).read_text(encoding="utf-8", errors="replace")
                    for name in ("go.mod", "go.sum") if (out_dir / "out" / "resolved" / name).is_file()}
        execute = out_dir / "execute.log"
        runs.append({"prefix": "", "docker": docker_build.provenance(plan), "resolved": resolved,
                     "returncode": result.get("exit_code"), "seconds": round(time.monotonic() - started, 1),
                     "peak_mb": None, "index": str(index) if kept else None, "index_bytes": index.stat().st_size
                     if kept else 0, "stderr_tail": (execute.read_text(encoding="utf-8", errors="replace")[-2500:]
                                                     if execute.is_file() else "")})
        if not kept:
            reasons.update({rel: f"no Go module holds it, and scip-go in its Dockerfile's build stage wrote no "
                                 f"document of it (exit code {result.get('exit_code')})" for rel in covered})
    return runs, reasons, gaps


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, roots: set[str],
          docker=()) -> dict:
    """The scip-go index of `project_dir` for `files` (default: every `.go` file), `roots` the folders of its
    modules as the pre-map names them, `docker` its Dockerfiles as BuildKit reads them (`_docker`); see the
    module's docstring."""
    import engine_tools
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tool = runtime.Tool(project_dir, "scip-go", VERSION)
    try:
        runtime.memory("scip-go", MIN_FREE)
        goroot = rx.shared_engine_dir("go") / rx.GO_VERSION / "go"
        if not tool.installed() or not (goroot / "bin" / rx.executable_name("go")).is_file():
            runtime.room()
        with runtime.fetching(f"Go {rx.GO_VERSION} and scip-go {VERSION}", "go.dev and proxy.golang.org"):
            env = {**os.environ, **engine_tools.go_environment()}
            go = str(Path(env["GOROOT"]) / "bin" / rx.executable_name("go"))
            tool._install(tool.home(), lambda partial: _build(go, env, partial, work_dir))
    except runtime.Unavailable as error:
        return runtime.refused("scip-go", VERSION, error)
    scip_go = str(tool.home() / rx.executable_name("scip-go"))
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*.go"))
    roots = set(roots)
    packages = {rel.rsplit("/", 1)[0] for rel in files if "/" in rel}

    def command(prefix, output):
        subprocess.run([go, "mod", "download"], cwd=mirror / prefix, env=env, stdin=subprocess.DEVNULL,
                       capture_output=True, timeout=1800)
        skip = len(prefix) + 1 if prefix else 0
        ignored = sorted({rel.rsplit("/", 1)[0][skip:] for rel in files
                          if "/" in rel and code_graph.owner(rel, roots) == prefix and any(
                              part.startswith(("_", ".")) or part == "testdata" for part in rel.split("/")[:-1])})
        return [scip_go, f"--output={output}", "./...", *[f"./{directory}" for directory in ignored]]

    runtime.clear(work_dir, "scip-go")
    with runtime.mirrored(tool, runtime.real(packages | roots, work_dir)) as mirror:
        runs = code_graph.module_runs("scip-go", roots, command, files, mirror, work_dir, env)
        more, constraints = _configured(go, scip_go, env, project_dir, mirror, work_dir, files, roots, runs)
    runs += more
    built, docker_reasons, gaps = _docker(project_dir, work_dir, files, roots, docker)
    runs += built
    return {**runtime.outcome("scip-go", VERSION, runs),  # `configs` is for `tasks`
            "configs": {"roots": sorted(roots), "failed": {run["prefix"]: f"exit code {run['returncode']}"
                                                           for run in runs if not run["index"]
                                                           and "configuration" not in run and "docker" not in run},
                        **({"constraints": constraints} if constraints else {}),
                        **({"docker": docker_reasons} if docker_reasons else {})},
            **({"gaps": gaps} if gaps else {})}
