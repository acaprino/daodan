"""scip-go: how it runs, and the aliases its index states its own way.

`index` runs scip-go, built once with Daodan's Go (`go install` at `VERSION`, checked by Go's checksum
database), in a mirror of the project where every directory holding a Go file is real: at the root, then in
each nested module holding files the root run left out, after `go mod download` there, with Go's ignored
directories (`_x`, `.x`, `testdata`) named as explicit packages. No project code runs: `go list` and the type
checker only read it.

Interface implementations need no hop: scip-go states them in `SymbolInformation` (`is_implementation`), which
the shared traversal follows for members. `hops` reads the statement that defines a name: `x := y.z`,
`var x = y` lead to the symbol the index references at the value, position by position; a function literal
leads to the function the snapshot declares there.
"""
from __future__ import annotations

import collections
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import code_graph

VERSION = "v0.2.9"  # github.com/scip-code/scip-go
MIN_FREE = 512 * 2**20  # 335 MB peak on chi (benchmarks/inference-audit, 13 November 2026)
PARAMETERS = {"parameter_declaration", "variadic_parameter_declaration"}


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


def missing(index, rels: list[str]) -> dict:
    """Why a Go file has no document: a build constraint the indexer's default build leaves out."""
    reasons = {}
    for rel in rels:
        try:
            head = (index.root / rel).read_text(encoding="utf-8", errors="replace").split("\n")[:20]
        except OSError:
            continue
        constraint = next((line.strip() for line in head if line.startswith("//go:build")), None)
        if constraint:
            reasons[rel] = f"build constraint `{constraint}`"
    return reasons


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


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """The scip-go index of `project_dir` for `files` (default: every `.go` file); see the module's docstring."""
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
            env = {**os.environ, **rx.GoEngine(project_dir).go_environment()}
            go = str(Path(env["GOROOT"]) / "bin" / rx.executable_name("go"))
            tool._install(tool.home(), lambda partial: _build(go, env, partial, work_dir))
    except runtime.Unavailable as error:
        return runtime.refused("scip-go", VERSION, error)
    scip_go = str(tool.home() / rx.executable_name("scip-go"))
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*.go"))
    roots = code_graph.manifest_dirs(project_dir, "go.mod")
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
    return runtime.outcome("scip-go", VERSION, runs)
