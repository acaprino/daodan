"""Jelly, the static whole-program call graph for JavaScript and TypeScript: a second source beside the index.

`analyze` runs Jelly (`cs-au-dk/jelly`, `jelly -j cg.json`) over the snapshot's JS/TS files of a copy of the
checkout whose packages sit inside it, static analysis only: never `--approx`, `-d` or `--npm-test`, which
run project code. `dependencies=True` analyzes every module the entry files reach in `node_modules`;
`False` passes `--ignore-dependencies`. Heuristic edges from a call into a package to the callbacks it is
given (`--no-callgraph-external`) are left out: they name what the package may call, not what the site calls.

Jelly's JSON (`src/output/analysisstatereporter.ts`): `files`, `functions` and `calls` as
`file index:start line:start column:end line:end column` (1-based columns, the source's UTF-16 units),
`call2fun` pairs; a module is a function spanning its file. Each call is matched with tree-sitter to the call,
`new` or JSX element with the same range, and its site is its callee's last name, as the snapshot names it.
"""
from __future__ import annotations

import collections
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402
from adapters import ts_compiler  # noqa: E402

VERSION = "0.13.0"  # @cs-au-dk/jelly
WRAPPERS = {"parenthesized_expression", "non_null_expression", "as_expression", "satisfies_expression"}


def _trees():
    from indexers import typescript
    from languages._treesitter import get_parser
    cache = {}

    def tree(path: Path):
        if path not in cache:
            grammar = typescript.GRAMMARS.get(path.suffix.lower())
            loaded = get_parser(grammar) if grammar else None
            try:
                cache[path] = loaded[0].parse(path.read_bytes()) if loaded else None
            except OSError:
                cache[path] = None
        return cache[path]
    return tree


def _site(node) -> tuple[str, object]:
    """(kind, the node naming the callee) of a call, `new` or JSX element."""
    if node.type in ("call_expression", "new_expression"):
        callee = node.child_by_field_name("function" if node.type == "call_expression" else "constructor")
        while callee is not None and callee.type in WRAPPERS and callee.named_children:
            callee = callee.named_children[0]
        if callee is not None and callee.type == "member_expression":
            callee = callee.child_by_field_name("property") or callee
        elif callee is not None and callee.type == "subscript_expression":
            callee = callee.child_by_field_name("index") or callee
        return ("call" if node.type == "call_expression" else "new"), callee or node
    if node.type.startswith("jsx"):
        return "jsx", node.child_by_field_name("name") or node
    return "other", node


def _exact(tree, start: tuple, end: tuple):
    """The smallest node spanning exactly `start`..`end` (tree-sitter rows and byte columns), None without one."""
    node = tree.root_node.descendant_for_point_range(start, end)
    return node if node is not None and (tuple(node.start_point), tuple(node.end_point)) == (start, end) else None


def analyze(project_dir: Path, work_dir: Path, files: list[str] | None = None, dependencies: bool = True,
            timeout: int = 1200) -> dict:
    from adapters import typescript
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    here = ts_compiler.mirror(Path(project_dir), work_dir)
    root = here.resolve()
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in Path(project_dir).rglob("*")
                       if path.suffix in typescript.SUFFIXES and "node_modules" not in path.parts)
    entries = [rel for rel in files if rel.endswith(typescript.SUFFIXES) and not rel.endswith(".d.ts")]
    label = "deps" if dependencies else "own"
    output, diagnostics = work_dir / f"jelly-{label}.json", work_dir / f"jelly-{label}-diagnostics.json"
    options = ["-j", str(output), "--diagnostics-json", str(diagnostics), "-b", str(here), "-i", str(timeout),
               "--no-callgraph-external", "--no-tty", "--no-print-progress", "-l", "warn"]
    if not dependencies:
        options.append("--ignore-dependencies")
    env = dict(os.environ, NODE_OPTIONS="--max-old-space-size=20480")
    env["PATH"] = f"{ts_compiler.NODE}{os.pathsep}{env.get('PATH', '')}"
    node = shutil.which("node", path=env["PATH"]) or "node"
    main = ts_compiler.TOOLS / "node_modules/@cs-au-dk/jelly/lib/main.js"
    run = scip_graph.measured([node, str(main), *options, "--", *entries], str(here), env, timeout + 1800)
    run["command"] = run["command"][:len(options) + 3] + [f"... {len(entries)} entry files"]
    engine = {"name": "jelly", "version": VERSION, "seconds": run["seconds"], "peak_mb": run["peak_mb"],
              "dependencies": dependencies, "timeout": timeout}
    if not output.is_file():
        return {"edges": [], "run": run, "engine": engine}
    data = json.loads(output.read_text(encoding="utf-8"))
    names = [name.replace("\\", "/") for name in data["files"]]

    def parse(text: str):
        index, l0, c0, l1, c1 = text.split(":")
        return int(index), int(l0), int(c0) - 1, int(l1), int(c1) - 1
    functions = {key: parse(value) for key, value in data["functions"].items()}
    modules = {}  # file index -> the function spanning the whole file
    for key, (index, l0, c0, l1, c1) in functions.items():
        if (l0, c0) == (1, 0) and (index not in modules or (l1, c1) > functions[modules[index]][3:]):
            modules[index] = key
    module_keys = set(modules.values())
    per_file = collections.defaultdict(list)
    for key, value in functions.items():
        if key not in module_keys:
            per_file[value[0]].append((value[1:], key))
    lines, tree = ts_compiler.Lines(), _trees()

    def path_of(index: int) -> Path:
        return (here / names[index]).resolve()

    def located(index: int, line: int, column: int) -> tuple[str, dict | None]:
        return ts_compiler.where(path_of(index), root, line, column, lines)
    callees = collections.defaultdict(list)
    for call, function in data["call2fun"]:
        callees[str(call)].append(str(function))
    edges, counts = [], collections.Counter()
    for key, text in data["calls"].items():
        index, l0, c0, l1, c1 = parse(text)
        path = path_of(index)
        site, external = located(index, l0, c0)
        if external is not None:
            continue  # a call inside a package
        counts["calls"] += 1
        kind, found, parsed = "other", None, tree(path)
        if parsed is not None:
            node = _exact(parsed, (l0 - 1, lines.byte(path, l0, c0)), (l1 - 1, lines.byte(path, l1, c1)))
            if node is not None:
                kind, found = _site(node)
        if found is not None:
            site = f"{site.rsplit(':', 2)[0]}:{found.start_point[0] + 1}:{found.start_point[1]}"
        holders = [(span, name) for span, name in per_file[index] if span[:2] <= (l0, c0) and (l1, c1) <= span[2:]]
        caller = located(index, *max(holders)[0][:2])[0] if holders else site.rsplit(":", 2)[0]
        targets = callees.get(key, ())
        counts[f"{kind} with callee" if targets else f"{kind} without callee"] += 1
        for target in targets:
            t_index, t0, t_c0, _t1, _t_c1 = functions[target]
            callee, package = located(t_index, t0, t_c0)
            edges.append({"caller": caller, "callee": callee, "site": site,
                          "kind": "module" if target in module_keys else kind, "external": package})
    try:
        diagnostics_data = json.loads(diagnostics.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        diagnostics_data = {}
    small = {key: value for key, value in diagnostics_data.items() if not isinstance(value, (list, dict))}
    return {"edges": edges, "counts": dict(counts), "run": run, "files_in_graph": len(names),
            "diagnostics": small, "engine": engine}
