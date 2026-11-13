"""scip-typescript, for JavaScript and TypeScript: how the indexer runs and the aliases its index states its own way.

`index` runs scip-typescript over a copy of the checkout with a generated tsconfig that holds every JS/TS
file of the snapshot (`allowJs`) and extends the project's own, after the engine pass's package install
(`npm ci --ignore-scripts`, `npm_modules`). `hops` reads the statement that defines a name: `a = b`,
`k: b.c`, `exports.f = g` and `{ k: name } = …` lead to the symbol the index references at the value or the
key (CommonJS `module.exports = { f }` needs none: the index states it as a shared range); a function value
leads to the function the snapshot declares there. A library function whose documented contract returns its
argument is a declared hop, tagged `declared:<package>.<function>`.
"""
from __future__ import annotations

import collections
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scip_graph  # noqa: E402

VERSION = "0.5.2"  # @sourcegraph/scip-typescript; needs Node >= 22.13
NODE = Path(os.environ.get("DAODAN_NODE_BIN", "/opt/node/bin"))
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


def _tsconfig(mirror: Path, files: list[str]) -> str | None:
    """Every JS/TS file of the snapshot in one program with `allowJs`; the project's own options kept."""
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    config = {"compilerOptions": options, "include": files, "exclude": []}
    own = mirror / "tsconfig.json"
    if own.is_file():
        own.rename(mirror / "tsconfig.project.json")
        config["extends"] = "./tsconfig.project.json"
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    own.write_text(json.dumps(config, indent=1), encoding="utf-8")
    return config.get("extends")


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    import resolve_edges as rx
    mirror = work_dir / "mirror-scip-typescript"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True, ignore=shutil.ignore_patterns("node_modules"))
    modules = rx.npm_modules(project_dir)  # the engine pass's own install: npm ci --ignore-scripts
    if modules is not None:
        for found in sorted(modules.parent.rglob("node_modules")):
            relative = found.relative_to(modules.parent)
            if "node_modules" in relative.parts[:-1]:
                continue
            link = mirror / relative
            if not link.exists():
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(found, target_is_directory=True)
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*")
                       if path.suffix in SUFFIXES and "node_modules" not in path.parts)
    extends = _tsconfig(mirror, [rel for rel in files if rel.endswith(SUFFIXES)])
    env = dict(os.environ, NODE_OPTIONS="--max-old-space-size=12288")
    env["PATH"] = f"{NODE}{os.pathsep}{env.get('PATH', '')}"
    output = work_dir / "scip-typescript-0.scip"
    run = {"prefix": "", **scip_graph.measured(
        [str(NODE / "scip-typescript"), "index", "--cwd", str(mirror), "--output", str(output), "--no-progress-bar"],
        str(mirror), env, 3 * 3600)}
    run["index"] = str(output) if output.is_file() else None
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    return {"indexes": [[run["index"], ""]] if run["index"] else [], "runs": [run],
            "indexer": {"name": "scip-typescript", "version": VERSION, "seconds": run["seconds"],
                        "peak_mb": run["peak_mb"]},
            "node_modules": str(modules), "tsconfig_extends": extends}


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
        parts = scip_graph.split_symbol(key)
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
