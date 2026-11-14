"""scip-typescript, for JavaScript and TypeScript: how it runs, and the aliases its index states its own way.

`index` runs scip-typescript (npm, without install scripts, on Daodan's Node) in a mirror of the project with
the engine pass's package install linked as `node_modules` (`npm_modules`: `npm ci --ignore-scripts`; a
project without a root `package.json` gets it in each outermost directory holding one) and a generated
tsconfig that holds every JS/TS file of the snapshot (`allowJs`) and extends the project's own, or without a
root `tsconfig.json` the nested one the caller names (where an app keeps its options and path aliases). No
project code runs.

`hops` reads the statement that defines a name: `a = b`, `k: b.c`, `exports.f = g` and `{ k: name } = …` lead
to the symbol the index references at the value or the key (CommonJS `module.exports = { f }` needs none: the
index states it as a shared range); a function value leads to the function the snapshot declares there. A
library function whose documented contract returns its argument is a declared hop, tagged
`declared:<package>.<function>`.
"""
from __future__ import annotations

import collections
import json
import subprocess
from pathlib import Path, PurePosixPath

import code_graph

VERSION = "0.5.2"  # @sourcegraph/scip-typescript on npm
MIN_FREE = 2304 * 2**20  # 2,264 MB peak on tududi (benchmarks/inference-audit, 13 November 2026)
SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
GRAMMARS = {".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "tsx", ".js": "javascript",
            ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript"}
PATTERNS = {"object_pattern", "array_pattern", "pair_pattern", "shorthand_property_identifier_pattern",
            "assignment_pattern", "object_assignment_pattern", "rest_pattern"}
PARAMETERS = {"formal_parameters", "required_parameter", "optional_parameter", "catch_clause"}
WRAPPERS = {"parenthesized_expression", "as_expression", "satisfies_expression", "non_null_expression",
            "type_assertion"}
FUNCTIONS = {"arrow_function", "function_expression", "function", "generator_function", "class"}
# Library functions whose documented contract returns their argument (`argument`) or what their argument, a
# function without a block body, returns (`result`); matched by the package and descriptors of the index.
DECLARED = {("@types/react", "/React/useCallback()."): "argument",
            ("@types/react", "/React/useMemo()."): "result"}


def _unwrap(node):
    while node is not None and node.type in WRAPPERS:
        node = node.named_children[0] if node.named_children else None
    return node


def _defining_value(node) -> tuple[str, object]:
    """(form, node) of the statement that defines the name at `node`: `pattern-key` with the key, `value` or
    `field` with the value, `parameter`, `destructured` (another element of a pattern) or `none`."""
    child, parent = node, node.parent
    if parent is not None and parent.type == "assignment_pattern" and parent.child_by_field_name("left") == node:
        child, parent = parent, parent.parent
    if parent is not None and parent.type == "pair_pattern" and parent.child_by_field_name("value") == child:
        return "pattern-key", parent.child_by_field_name("key")
    child, parent, destructured = node, node.parent, False
    while parent is not None and parent.type in PATTERNS:
        child, parent, destructured = parent, parent.parent, True
    if parent is None:
        return "none", None
    kind, field = parent.type, parent.child_by_field_name
    if kind in PARAMETERS or (kind == "arrow_function" and field("parameter") == child):
        return "parameter", None
    if kind == "variable_declarator" and field("name") == child:
        return ("destructured" if destructured else "value"), field("value")
    if kind == "pair" and field("key") == child:
        return "value", field("value")
    if kind in ("public_field_definition", "field_definition"):
        return "field", field("value")
    if kind == "member_expression" and field("property") == child and parent.parent is not None \
            and parent.parent.type == "assignment_expression" and parent.parent.child_by_field_name("left") == parent:
        return "value", parent.parent.child_by_field_name("right")
    return "none", None


def _value(index, rel: str, value, tag: str, function_tag: str = "value") -> list:
    """Where a value leads: a function's start, or the symbols the index references at a name."""
    value = _unwrap(value)
    if value is None:
        return []
    if value.type in FUNCTIONS:
        return [((rel, value.start_point[0] + 1, value.start_point[1]), function_tag)]
    if value.type in ("identifier", "member_expression"):
        name = value if value.type == "identifier" else value.child_by_field_name("property")
        return [(key, tag) for key in index.stated(rel, name)] if name is not None else []
    if value.type == "call_expression":
        return _declared(index, rel, value)
    return []


def _declared(index, rel: str, call) -> list:
    callee = _unwrap(call.child_by_field_name("function"))
    if callee is None:
        return []
    name = callee if callee.type == "identifier" else callee.child_by_field_name("property") \
        if callee.type == "member_expression" else None
    arguments = call.child_by_field_name("arguments")
    first = arguments.named_children[0] if arguments is not None and arguments.named_children else None
    if name is None or first is None:
        return []
    for key in index.stated(rel, name):
        parts = code_graph.split_symbol(key)
        for (package, suffix), contract in DECLARED.items():
            if not parts or parts[2] != package or not parts[4].endswith(suffix):
                continue
            tag = f"declared:{package}.{suffix.rsplit('/', 1)[-1][:-3]}"
            if contract == "argument":
                return _value(index, rel, first, tag, tag)
            first = _unwrap(first)
            body = first.child_by_field_name("body") if first is not None and first.type == "arrow_function" else None
            return _value(index, rel, body, tag, tag) if body is not None and body.type != "statement_block" else []
    return []


def hops(index) -> dict:
    """Alias edges from the statements that define the names of JS/TS documents."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        grammar = GRAMMARS.get(Path(rel).suffix.lower())
        if grammar is None:
            continue
        for occurrence in occurrences:
            # Types, methods, modules and parameters are declarations, never aliases.
            if not occurrence.definition or occurrence.key.endswith(("#", ").", "/", ")")):
                continue
            node = index.node(rel, occurrence, grammar)
            if node is None:
                continue
            form, value = _defining_value(node)
            if form == "pattern-key" and value is not None:
                found = [(key, "pattern-key") for key in index.stated(rel, value)]
            elif form in ("value", "field") and value is not None:
                found = _value(index, rel, value, "initializer")
            else:
                found = []
            out[occurrence.key] += [item for item in found if item[0] != occurrence.key]
    return {key: list(dict.fromkeys(items)) for key, items in out.items() if items}


def _tsconfig(mirror: Path, files: list[str], base: str | None = None) -> str | None:
    """Every JS/TS file of the snapshot in one program with `allowJs`; the project's own options kept."""
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    config = {"compilerOptions": options, "include": files, "exclude": []}
    own = mirror / "tsconfig.json"
    if own.is_file():
        own.rename(mirror / "tsconfig.project.json")
        config["extends"] = "./tsconfig.project.json"
    elif base and (mirror / base).is_file():
        config["extends"] = f"./{base}"
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    own.write_text(json.dumps(config, indent=1), encoding="utf-8")
    return config.get("extends")


def _package_roots(project_dir: Path) -> list[str]:
    """'' when the project's root has a package.json, else each outermost directory that has one."""
    if (project_dir / "package.json").is_file():
        return [""]
    roots = sorted(code_graph.manifest_dirs(project_dir, "package.json"))
    return [root for root in roots if not any(root.startswith(f"{other}/") for other in roots)]


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, tsconfig: str | None = None) -> dict:
    """The scip-typescript index of `project_dir` for `files` (default: every JS/TS file outside
    `node_modules`), `tsconfig` the configuration a root without one extends; see the module's docstring."""
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tool = runtime.Tool(project_dir, "scip-typescript", VERSION, skip=(".git", "node_modules"))
    try:
        runtime.memory("scip-typescript", MIN_FREE)
        directory = runtime.node(project_dir)
        script = runtime.npm_package(project_dir, directory, "@sourcegraph/scip-typescript", VERSION)
        roots = _package_roots(project_dir)
        for root in roots:
            key = rx.npm_key(project_dir / root)
            if key and not (rx.shared_cache_dir() / "npm" / key / "daodan-modules.json").is_file():
                runtime.room()
    except runtime.Unavailable as error:
        return runtime.refused("scip-typescript", VERSION, error)
    installs, links = {}, {}
    for root in roots:
        try:
            with runtime.on_path(directory):
                modules = rx.npm_modules(project_dir / root)  # the engine pass's own: npm ci --ignore-scripts
        except (OSError, subprocess.SubprocessError) as error:
            print(f"the project's JavaScript packages were not installed: {error}", flush=True)
            modules = None
        installs[root] = str(modules) if modules else None
        for manifest in rx.npm_manifests(project_dir / root) if modules is not None else ():
            installed = modules.parent / manifest.parent.relative_to(project_dir / root) / "node_modules"
            if installed.is_dir():
                relative = manifest.parent.relative_to(project_dir).as_posix()
                links[(PurePosixPath(relative) / "node_modules").as_posix()] = installed
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*")
                       if path.suffix in SUFFIXES and "node_modules" not in path.relative_to(project_dir).parts)
    output = work_dir / "scip-typescript-0.scip"
    runtime.clear(work_dir, "scip-typescript")
    env = runtime.environment(directory, NODE_OPTIONS="--max-old-space-size=12288")
    with runtime.mirrored(tool, links) as mirror:
        extends = _tsconfig(mirror, [rel for rel in files if rel.endswith(SUFFIXES)], tsconfig)
        run = {"prefix": "", **code_graph.measured(
            [str(directory / rx.executable_name("node")), str(script), "index", "--cwd", str(mirror), "--output",
             str(output), "--no-progress-bar"], str(mirror), env, 3 * 3600)}
    run["index"] = str(output) if output.is_file() else None
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    return {**runtime.outcome("scip-typescript", VERSION, [run]), "node_modules": installs,
            "tsconfig_extends": extends}
