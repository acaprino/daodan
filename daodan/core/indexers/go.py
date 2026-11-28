"""scip-go: how it runs, and the aliases its index states its own way.

The go command starts what a project names: git for a module no proxy serves, the C compiler for a file that
imports "C", the Go a `toolchain` line asks for. So the go command and scip-go run only in Daodan's container
(`NEEDS_CONTAINER`), never on the host: one run over a copy of the project (`_boxed`). The preparation, with the
registries and the hosts the project declares open, builds scip-go with Daodan's Go (`go install` at `VERSION`,
checked by Go's checksum database) and runs `go mod download` in each module that holds a Go file. The
execution, with no network, runs scip-go in each of them under the indexer's own build (`OWN`), with Go's
ignored directories (`_x`, `.x`, `testdata`) named as explicit packages.

A file the indexer's build leaves out (its `//go:build` line or its name rules out the build's GOOS, GOARCH,
cgo or tags) is indexed by a further run of the same execution under the configuration nearest that build which
builds it (`configuration`), once `go list` there lists it; a file only the `ignore` tag builds is a program
`go run` names, indexed as one. Such a run indexes the file's whole package: only the left-out files' documents
are kept. A cgo file has no document (scip-go indexes the copy cgo writes into the build cache), nor has a file
no configuration builds, nor one past `PASSES` further runs: `missing` says which.

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
import os
import posixpath
import re
import shlex
import shutil
import time
from pathlib import Path, PurePosixPath

import code_graph
import preparation
from container_runner import IMAGE  # gcc for cgo, git, timeout

VERSION = "v0.2.9"  # github.com/scip-code/scip-go
# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
NAME, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-go", ("go",), frozenset({"go-module"}), True
# The container's memory, not measured yet: scip-go's build, then its runs (335 MB peak on chi on the host,
# benchmarks/inference-audit, 13 November 2026).
MIN_FREE = MEMORY = 4 * 2**30
OUT = "/daodan/out/scip-go"
SCIP_GO = f"{preparation.T}/bin/scip-go"
# The indexer's own build, in every command of the execution: Daodan's Go alone, whatever a `toolchain` line
# asks; cgo on (the image has gcc); no module fetched, no go.mod rewritten.
OWN = {"CGO_ENABLED": "1", "GOFLAGS": "-mod=readonly", "GOPROXY": "off", "GOTOOLCHAIN": "local"}
# What `go list -f` prints for a package: the Go files it builds, tests included and cgo files aside (scip-go reads
# their copies), one path a line.
BUILT = "".join('{{range .%s}}{{$.Dir}}/{{.}}{{"\\n"}}{{end}}' % key
                for key in ("GoFiles", "TestGoFiles", "XTestGoFiles"))
LIMIT = 3600  # the seconds one run of scip-go may take: the container's limit is their sum (13.9 s on chi)
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
    """GOOS and GOARCH of the indexer's build: those of the Go the container runs, as its release names them
    (`go1.27.3.linux-amd64.tar.gz`)."""
    goos, goarch = re.search(r"\.([a-z0-9]+)-([a-z0-9]+)\.tar\.gz$", preparation.GO[0]).groups()
    return goos, goarch


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


def _variables(config: dict) -> dict:
    """The go command's variables a configuration sets over the indexer's own build (`OWN`): none for a program."""
    if "program" in config:
        return {}
    tags = {"GOFLAGS": f"{OWN['GOFLAGS']} -tags={','.join(config['tags'])}"} if config["tags"] else {}
    return {"GOOS": config["GOOS"], "GOARCH": config["GOARCH"], "CGO_ENABLED": config["CGO_ENABLED"], **tags}


def _patterns(prefix: str, rels: list[str], config: dict) -> list[str]:
    """What a further run names, from its module's folder: a program's file, else the files' packages."""
    inner = [rel[len(prefix) + 1:] if prefix else rel for rel in rels]
    if "program" in config:
        return [f"./{inner[0]}"]
    return sorted({f"./{posixpath.dirname(rel)}" if posixpath.dirname(rel) else "." for rel in inner})


def _document_path(value: bytes) -> str:
    return next((part.decode("utf-8", "replace").replace("\\", "/") for field, kind, part in code_graph._fields(value)
                 if field == 1 and kind == 2), "")


def _covered(runs: list[dict], project: Path) -> set[str]:
    """The files the runs' indexes hold a document of, named as `code_graph.Index.load` names them."""
    out = set()
    for run in runs:
        if run.get("index"):
            for number, wire, value in code_graph._fields(Path(run["index"]).read_bytes()):
                if number == 2 and wire == 2:
                    rel, prefix = _document_path(value), run["prefix"]
                    out.add(f"{prefix}/{rel}" if prefix and not (Path(project) / rel).is_file() else rel)
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


def _planned(project: Path, files: list[str], roots: set[str]) -> tuple[dict, dict, dict]:
    """The further runs the Go files ask for, read from the files alone: `{(module's folder, label):
    (configuration, files)}` for those the indexer's own build leaves out and another configuration builds,
    `{file: why}` for a cgo file and for one no configuration builds, and each constrained file's constraint as a
    reason says it."""
    target, cgo = _target(), OWN["CGO_ENABLED"] == "1"
    groups, reasons, said = {}, {}, {}
    for rel in files:
        if "vendor" in rel.split("/")[:-1]:
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
        said[rel] = f"build constraint `{line}`" if line else f"file name constraint `{'_'.join(named)}`"
        config = configuration(rel, text, target, cgo)
        if config is None:
            reasons[rel] = f"{said[rel]}: no GOOS, GOARCH, cgo and tags build it"
            continue
        label = _label(config, target, cgo)
        if label:  # the indexer's own build builds it: it is left out for another reason
            groups.setdefault((prefix, label), (config, []))[1].append(rel)
    return groups, reasons, said


def scripts(runs: list[tuple], further: list[tuple]) -> tuple[str, str, dict]:
    """The preparation's script, the execution's, and what the preparation needs beside them (`{files, hosts}`).
    The preparation: Daodan's Go (`tools`, installed as root before it, `container.tool_phase`; the preparation
    runs as `container.NOBODY`), scip-go built with it by at most `go_jobs` compilers at once, then `go mod
    download` in the folder of each of `runs` (`(folder, patterns)`). The execution, with no network and under
    `OWN`: scip-go on each run's patterns, run `n` leaving `index-n.scip`, its log, its exit code and its seconds;
    then each of `further` (`(folder, variables, patterns, files)`), numbered after them: `go list` there under
    `variables`, its files as paths from the folder in `list-n.txt`, and scip-go when one of `files` is among
    them, for the first `PASSES` of them (`capped` after)."""
    import container
    import engine_tools
    needs = preparation.setup(["go"])
    build = (f"GOBIN={preparation.T}/bin GOPATH={preparation.STATE}/scip-go GOCACHE={preparation.STATE}/scip-go-cache"
             f" GOFLAGS= GOTOOLCHAIN=local {preparation.T}/go/bin/go install -p {engine_tools.go_jobs()}"
             f" github.com/scip-code/scip-go/cmd/scip-go@{VERSION}")  # no build of the project: Daodan's Go alone
    prepare = ["# scip-go prepare", "set -u", f"mkdir -p {preparation.T}/bin {preparation.ENV['HOME']}",
               f"{{ {build} ; }} >&2 || echo 'DAODAN-MISSING scip-go@{VERSION}' >&2",
               "export GOFLAGS=-mod=readonly GOTOOLCHAIN=local",  # as the execution: a `toolchain` line brings no Go
               preparation.restore("go", [folder for folder, _patterns in runs])]

    def at(folder: str) -> str:
        return shlex.quote(posixpath.normpath(f"{container.WORKDIR}/{folder}"))

    execute = ["# scip-go execute", "set -u", "export " + " ".join(f"{name}={value}" for name, value in OWN.items()),
               f"OUT={OUT}", "mkdir -p $OUT",
               f'run() {{ n=$1; d=$2; shift 2; s=$(date +%s); ( cd "$d" && exec timeout -k 30 {LIMIT} "$@" )'
               " > $OUT/scip-$n.log 2>&1; echo $? > $OUT/scip-$n.code;"
               " echo $(( $(date +%s) - s )) > $OUT/scip-$n.seconds; }", "passes=0"]
    # A listed path, from the folder the go command runs in.
    inner = """awk -v p="$PWD/" 'index($0, p) == 1 { print substr($0, length(p) + 1) }'"""

    def indexed(number: int, patterns: list[str]) -> str:
        return f"{SCIP_GO} --output=$OUT/index-{number}.scip {shlex.join(patterns)}"

    for number, (folder, patterns) in enumerate(runs):
        execute.append(f"run {number} {at(folder)} {indexed(number, patterns)}")
    for number, (folder, variables, patterns, files) in enumerate(further, len(runs)):
        under = shlex.join(["env", *(f"{name}={value}" for name, value in variables.items())])
        listed = " ".join(f"-e {shlex.quote(rel)}" for rel in files)
        execute += [
            f"if [ $passes -ge {PASSES} ]; then echo capped > $OUT/scip-{number}.code; else",
            f"  ( cd {at(folder)} && {under} go list -e -f {shlex.quote(BUILT)} {shlex.join(patterns)} | {inner} )"
            f" > $OUT/list-{number}.txt 2> $OUT/list-{number}.err",
            f"  if grep -qxF {listed} $OUT/list-{number}.txt; then passes=$((passes + 1));"
            f" run {number} {at(folder)} {under} {indexed(number, patterns)}; fi",
            "fi"]
    return ("\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "exit 0"]) + "\n",
            {"files": needs["files"], "hosts": needs["hosts"], "tools": {"lines": needs["lines"], "caps": needs["caps"]}})


def _said(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _run(back: Path, number: int, work_dir: Path, command: list[str]) -> dict:
    """Run `number` of the execution as it left it in `back`: how it ended, its seconds, its log's tail and its
    index, moved to `work_dir`."""
    code, seconds, log = (_said(back / f"scip-{number}.{name}").strip() for name in ("code", "seconds", "log"))
    written, index = back / f"index-{number}.scip", Path(work_dir) / f"scip-go-{number}.scip"
    if written.is_file():
        os.replace(written, index)
    errors = [line[line.find(" ERROR ") + 7:][:200] for line in log.splitlines() if " ERROR " in line]
    return {"command": command, "returncode": int(code) if code.lstrip("-").isdigit() else None,
            "seconds": float(seconds) if seconds.isdigit() else 0.0, "peak_mb": None, "stdout_tail": "",
            "stderr_tail": log[-2500:], "stderr_errors": len(errors),
            "stderr_error_examples": list(dict.fromkeys(errors))[:5], "image": IMAGE,
            "index": str(index) if index.is_file() else None,
            "index_bytes": index.stat().st_size if index.is_file() else 0}


def _boxed(project_dir: Path, work_dir: Path, files: list[str], roots: set[str], declared: dict, engine) -> dict:
    """One container run (`scripts`), read back: `{runs, constraints, gaps}`, a run per module of `roots` that
    holds a Go file, then the further runs made, each with no index where scip-go wrote none, and `{file: why}`
    for the files a build constraint, a file name or cgo left without a document; without the container run,
    `{state, reason, gaps}`."""
    import container
    out = work_dir / "container"
    shutil.rmtree(out, ignore_errors=True)
    held = collections.defaultdict(set)  # each module's folders that hold a Go file, from the module's
    for rel in files:
        home = code_graph.owner(rel, roots)
        if home is not None:
            held[home].add(posixpath.dirname(rel)[len(home) + 1 if home else 0:])
    # `./...` leaves out the directories Go ignores (`_x`, `.x`, `testdata`): each is named as a package.
    runs = [(root or ".", ["./...", *(f"./{folder}" for folder in sorted(held[root]) if any(
                part.startswith(("_", ".")) or part == "testdata" for part in folder.split("/")))])
            for root in sorted(roots) if held[root]]
    if not runs:
        return {"runs": [], "constraints": {}, "gaps": []}
    groups, reasons, said = _planned(project_dir, files, roots)
    further = [(prefix or ".", _variables(config), _patterns(prefix, rels, config),
                sorted(rel[len(prefix) + 1 if prefix else 0:] for rel in rels))
               for (prefix, _), (config, rels) in groups.items()]
    prepare, execute, needs = scripts(runs, further)

    def inputs() -> dict:
        return {f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                for url, digest, name in needs["files"]}

    result = container.run_in_container(
        project_dir, ["sh", "-c", execute], image=IMAGE, out_dir=out, prepare=["sh", "-c", prepare], outputs=[OUT],
        env=preparation.ENV, timeout=600 + (len(runs) + min(len(further), PASSES)) * (LIMIT + 60),
        prepare_timeout=3600, memory=MEMORY, engine=engine, inputs=inputs, tools=needs["tools"],
        registries=container.REGISTRIES + tuple(dict.fromkeys([*needs["hosts"], *declared.get("hosts", ())])))
    if result["state"] == "gap":
        return {"state": "unavailable", "reason": f"scip-go runs only in Daodan's container: {result['cause']}",
                "install": result["remedy"], "gaps": []}
    prepared = _said(out / "prepare.log")
    gaps = [*preparation.missing(prepared), *preparation.restore_gaps(prepared),
            *(result.get("gaps") or ())]  # and what the copy left out (`container.copy_perimeter`)
    if result["state"] != "done":
        return {"state": "failed", "gaps": gaps, "reason": f"the container run of scip-go ended {result['state']}"
                + (f": {result['cause']}" if result.get("cause") else "") + f" (see the logs in {out})"}
    back = out / Path(OUT).name
    done = [{"prefix": "" if folder == "." else folder, **_run(back, number, work_dir, [SCIP_GO, *patterns])}
            for number, (folder, patterns) in enumerate(runs)]
    covered = _covered(done, project_dir)
    reasons = {rel: why for rel, why in reasons.items() if rel not in covered}
    more = []
    for number, ((prefix, label), (_config, rels)) in enumerate(groups.items(), len(runs)):
        rels = [rel for rel in rels if rel not in covered]  # the files `done` left out because its build does
        if _said(back / f"scip-{number}.code").strip() == "capped":
            reasons.update({rel: f"{said[rel]}: not indexed, the further runs of one index stop at {PASSES}"
                            for rel in rels})
            continue
        listed = set(_said(back / f"list-{number}.txt").splitlines())
        wanted = [rel for rel in rels if rel[len(prefix) + 1 if prefix else 0:] in listed]
        reasons.update({rel: f"{said[rel]}: `go list` under {label} does not list it" for rel in rels
                        if rel not in wanted})
        if not wanted:
            continue
        run = {"prefix": prefix, "configuration": label,
               **_run(back, number, work_dir, [SCIP_GO, *further[number - len(runs)][2]])}
        names = {name for rel in wanted for name in (rel, rel[len(prefix) + 1:] if prefix else rel)}
        kept = _keep(Path(run["index"]), names) if run["index"] else 0
        run["index"], run["index_bytes"] = (run["index"], Path(run["index"]).stat().st_size) if kept else (None, 0)
        more.append(run)
        got = _covered([run], project_dir)
        reasons.update({rel: f"{said[rel]}: the scip-go run under {label} wrote no document of it (exit code "
                             f"{run['returncode']})" for rel in wanted if rel not in got})
    return {"runs": [*done, *more], "constraints": reasons, "gaps": gaps}


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folders of its modules, where scip-go runs (a `go.work`'s folder
    is none: `./...` there names no module's packages), and the Dockerfiles as BuildKit reads them."""
    import premap
    builds = record.get("docker_builds") or []
    return {"roots": premap.roots(record, UNIT_KINDS), **({"docker": builds} if builds else {})}


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
        plan = docker_build.sourced(plan, Path(work_dir) / f"sources-{len(runs)}")  # the base's package hosts
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
        gaps += result.get("gaps") or []  # what the copy left out (`container.copy_perimeter`)
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


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, roots: set[str], docker=(),
          declared: dict | None = None, engine=None) -> dict:
    """The scip-go index of `project_dir` for `files` (default: every `.go` file), in Daodan's container with the
    engine the pass found (`NEEDS_CONTAINER`) and the hosts the project declares (`declared`): `roots` the folders
    of its modules as the pre-map names them, `docker` its Dockerfiles as BuildKit reads them (`_docker`); see the
    module's docstring. Nothing of it runs on the host."""
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*.go"))
    roots = set(roots)
    runtime.clear(work_dir, "scip-go")
    boxed = _boxed(project_dir, work_dir, files, roots, declared or {}, engine)
    if "state" in boxed:
        return {"indexes": [], "runs": [], "indexer": code_graph.indexer("scip-go", VERSION, []), **boxed}
    built, docker_reasons, gaps = _docker(project_dir, work_dir, files, roots, docker)
    runs, constraints, gaps = [*boxed["runs"], *built], boxed["constraints"], [*boxed["gaps"], *gaps]
    found = runtime.outcome("scip-go", VERSION, runs) if runs else runtime.refused(
        "scip-go", VERSION, runtime.Unavailable("no Go module of the pre-map holds a Go file: no module to index",
                                                "none: the Go files keep their static facts"))
    return {**found,  # `configs` is for `tasks`
            "configs": {"roots": sorted(roots), "failed": {run["prefix"]: f"exit code {run['returncode']}"
                                                           for run in runs if not run["index"]
                                                           and "configuration" not in run and "docker" not in run},
                        **({"constraints": constraints} if constraints else {}),
                        **({"docker": docker_reasons} if docker_reasons else {})},
            **({"gaps": gaps} if gaps else {})}
