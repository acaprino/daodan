# /// script
# requires-python = ">=3.11"
# dependencies = ["jedi==0.20.1"]
# ///
"""Re-classify the Python resolver measurement with the Codebase Map's perimeter.

resolver-spike/jedi_edges.py decides that a Jedi target is "in the project" with
`Path(target).relative_to(project_root)`. A project's virtual environments live
inside its root (`<root>/.venv`, `<root>/jupiter-tools/devops/.venv`), so once
Fix 1 gave Jedi those environments, every third-party definition it reached
(`rich`, `_pytest`, `InquirerPy`, `aiohttp`, `pydantic`) passed that test and was
graded as a project target. The snapshot never contains those files, because
its perimeter excludes dot-directories and what Git ignores.

This script replays the same inference on the same sample with the same
environment per file, computes the verdict EXACTLY as jedi_edges.py does, and
then the corrected verdict, where a target counts as project only if its file
is in the snapshot inventory. It reports four things:

  1. replication: the replayed original verdicts against the published run, so
     a difference caused by the projects having changed since is visible
  2. correction: how many published edges and gap positions move to external
  3. strictness: how many `edge-instantiation` verdicts hold only because the
     original rule accepts a class name declared ANYWHERE in the project, not in
     the target file
  4. cause of the corrected gap, per position: parser, convention, inherited,
     not-a-symbol, harness
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import sqlite3
import sys
from pathlib import Path

PLUGIN_SCRIPTS = Path(__file__).resolve().parents[3] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))
from snapshot_store import _unpack, open_snapshot  # noqa: E402

import jedi  # noqa: E402
from jedi.api.environment import create_environment  # noqa: E402

GAP = ("receiver-project-not-a-class", "receiver-project-method-not-a-symbol", "direct-project-not-a-symbol")


def load_symbol_table(manifest: Path):
    """Identical to resolver-spike/jedi_edges.py:load_symbol_table."""
    methods_by_file = collections.defaultdict(set)
    classes_by_name = collections.defaultdict(set)
    functions_by_file = collections.defaultdict(set)
    db = sqlite3.connect(manifest)
    for file, name, kind in db.execute("SELECT file, name, kind FROM meta_symbols"):
        if kind == "method" and "." in name:
            owner, method = name.rsplit(".", 1)
            methods_by_file[file].add((owner.split(".")[-1], method))
            classes_by_name[owner.split(".")[-1]].add(file)
        elif kind == "class":
            classes_by_name[name.split(".")[-1]].add(file)
        elif kind == "function":
            functions_by_file[file].add(name.split(".")[-1])
    return methods_by_file, classes_by_name, functions_by_file


def original_verdict(mode, relative, name, method, tables):
    """Identical to the classification block of jedi_edges.py."""
    methods_by_file, classes_by_name, functions_by_file = tables
    if mode == "direct":
        if relative is None:
            return "direct-external"
        if name in functions_by_file.get(relative, ()) or \
                name in {m for _, m in methods_by_file.get(relative, ())}:
            return "edge-direct-call"
        if name in classes_by_name:
            return "edge-instantiation"
        return "direct-project-not-a-symbol"
    if relative is None:
        return "receiver-external"
    if (name, method) in methods_by_file.get(relative, ()):
        return "edge-method-call"
    if name in classes_by_name:
        return "receiver-project-method-not-a-symbol"
    return "receiver-project-not-a-class"


def ast_definitions(path: Path):
    try:
        tree = ast.parse(path.read_bytes())
    except (SyntaxError, ValueError, OSError) as error:
        return None, f"{type(error).__name__}: {error}"[:120]
    out = []
    stack = [(child, [], "", False) for child in reversed(list(ast.iter_child_nodes(tree)))]
    while stack:
        node, chain, kinds, in_block = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            tag = "c" if isinstance(node, ast.ClassDef) else "d"
            names = chain + [node.name]
            out.append({"q": ".".join(names), "name": node.name, "l": node.lineno,
                        "deco_l": min([d.lineno for d in node.decorator_list] + [node.lineno]),
                        "kind": "class" if tag == "c" else "def", "a": kinds, "b": in_block,
                        "bases": [ast.unparse(b) for b in node.bases] if tag == "c" else []})
            children = [(c, names, kinds + tag, False) for c in ast.iter_child_nodes(node)]
        elif isinstance(node, ast.stmt):
            children = [(c, chain, kinds, True) for c in ast.iter_child_nodes(node)]
        else:
            children = [(c, chain, kinds, in_block) for c in ast.iter_child_nodes(node)]
        stack.extend(reversed(children))
    return out, None


def method_cause(row, script, line, column, parts, d, project_root, inventory, tables, meta_by_file):
    """For `receiver.method()`, ask Jedi where `method` itself is declared.

    The resolver measurement inferred the receiver and looked `(receiver class,
    method)` up on that class alone. `goto` on the method name follows the MRO,
    module attributes and assignments, so it says where the callee really is.
    """
    methods_by_file, _, functions_by_file = tables
    method = parts[-1]
    method_col = column + sum(len(part) + 1 for part in parts[:-1])
    try:
        source_line = Path(script.path).read_text(encoding="utf-8", errors="replace").splitlines()[line - 1]
    except (OSError, IndexError):
        source_line = ""
    if source_line[method_col:method_col + len(method)] != method:
        row["probe"] = source_line.strip()[:100]
        return "harness:method-not-at-computed-column"
    if d.type == "function":
        # `obj.func.assert_called()`: an attribute of a function object, the
        # unittest.mock idiom. Not a call into project code.
        return "harness:attribute-of-a-function"
    try:
        found = script.goto(line=line, column=method_col, follow_imports=True)
    except Exception as error:  # noqa: BLE001
        return f"goto-error:{type(error).__name__}"
    if not found:
        return "goto-unresolved"
    g = found[0]
    g_path = getattr(g, "module_path", None)
    try:
        g_rel = Path(g_path).resolve().relative_to(project_root).as_posix() if g_path else None
    except ValueError:
        g_rel = None
    row["goto"] = {"type": g.type, "name": g.name, "file": g_rel or (str(g_path) if g_path else None),
                   "line": g.line, "full_name": g.full_name}
    if g_rel is None or g_rel not in inventory:
        return "callee-external:inherited-or-module-attribute"
    if g.type in ("function", "class"):
        owner = (g.full_name or "").rsplit(".", 2)
        owner_short = owner[-2] if len(owner) >= 2 else ""
        if (owner_short, method) in methods_by_file.get(g_rel, ()) or method in functions_by_file.get(g_rel, ()) \
                or any(n.rsplit(".", 1)[-1] == method for n in meta_by_file.get(g_rel, ())):
            if d.type == "module":
                return "edge-missed-by-rule:module-function"
            return "edge-missed-by-rule:inherited-project-method"
        defs, error = ast_definitions(project_root / g_rel)
        if error is not None:
            row["parse_error"] = error
            return "parser"
        hit = next((x for x in defs if x["l"] == g.line or x["deco_l"] == g.line), None)
        if hit is not None and (hit["b"] or "d" in hit["a"]):
            row["ast_def"] = hit
            return "convention"
        return "unexplained-project-callable"
    if g.type in ("statement", "instance", "param", "property"):
        return f"dynamic-attribute:{g.type}"
    return f"goto-{g.type}"


def cause_of(row, d, mode, method, relative, project_root, meta_names):
    """Why the snapshot does not recognise an in-snapshot target (direct calls)."""
    if d.type == "module":
        return "not-a-symbol:module"
    if d.type in ("instance", "statement", "param", "property"):
        return f"not-a-symbol:{d.type}"
    defs, error = ast_definitions(project_root / relative)
    if error is not None:
        row["parse_error"] = error
        return "parser"
    at_line = [x for x in defs if d.line in (x["l"], x["deco_l"])]
    if mode == "method" and d.type == "class":
        cls = next((x for x in at_line if x["kind"] == "class"), None)
        if cls is None:
            return "harness:class-not-at-line"
        owned = [x for x in defs if x["q"] == f"{cls['q']}.{method}"]
        if owned:
            row["ast_def"] = owned[0]
            if owned[0]["q"] in meta_names:
                return "harness:method-is-in-table"
            return "convention" if owned[0]["b"] or "d" in owned[0]["a"] else "unexplained"
        if cls["bases"]:
            row["bases"] = cls["bases"]
            return "inherited"
        return "method-absent-from-class"
    hit = next((x for x in at_line if x["name"] == d.name), None)
    if hit is None:
        return "harness:no-definition-at-line"
    row["ast_def"] = hit
    if hit["q"] in meta_names:
        return "harness:name-is-in-table"
    if hit["b"] or "d" in hit["a"] or hit["a"].count("c") > 1:
        return "convention"
    return "unexplained"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix1", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--files", type=int, default=40)
    ap.add_argument("--per-file", type=int, default=40)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    fix1 = json.loads(args.fix1.read_text(encoding="utf-8"))
    project_root = args.project.resolve()
    with open_snapshot(args.manifest) as store:
        manifest_root = Path(store.metadata["root"])
    tables = load_symbol_table(args.manifest)
    db = sqlite3.connect(args.manifest)
    inventory = {row[0] for row in db.execute("SELECT file FROM sem_coverage")}
    meta_by_file = collections.defaultdict(set)
    meta_class_files = collections.defaultdict(set)
    for file, name, kind in db.execute("SELECT file, name, kind FROM meta_symbols"):
        meta_by_file[file].add(name)
        if kind == "class":
            meta_class_files[name.rsplit(".", 1)[-1]].add(file)

    by_file = collections.Counter()
    positions = collections.defaultdict(list)
    for file, line, column, blob in db.execute(
            "SELECT r.file, r.l0, r.c0, r.payload FROM sem_references r JOIN sem_coverage c ON c.file=r.file "
            "WHERE r.kind='call' AND r.resolution!='resolved' AND c.language='python'"):
        record = _unpack(blob)
        if record.get("reason") == "unbound-name":
            continue
        by_file[file] += 1
        positions[file].append((line, column, record.get("parts") or [], record.get("reason") or "none"))
    sample = [file for file, _ in by_file.most_common(args.files)]
    selected = [(file, item) for file in sample for item in positions[file][:args.per_file]]

    env_cache = {}

    def environment(path):
        if path is None:
            return None
        if path not in env_cache:
            try:
                env_cache[path] = create_environment(path, safe=False)
            except Exception:  # noqa: BLE001
                env_cache[path] = None
        return env_cache[path]

    project = jedi.Project(path=str(project_root), added_sys_path=[str(project_root)])
    per_file_env = fix1.get("per_file_environment", {})

    original = collections.Counter()
    corrected = collections.Counter()
    moved = collections.Counter()
    loose_instantiation = []
    gap_cause = collections.Counter()
    gap_cause_by_verdict = collections.defaultdict(collections.Counter)
    external_targets = collections.Counter()
    rows = []

    for file, (line, column, parts, reason) in selected:
        absolute = manifest_root / file
        if not absolute.is_file() or not parts:
            original["skipped"] += 1
            corrected["skipped"] += 1
            continue
        env = environment((per_file_env.get(file) or {}).get("environment"))
        try:
            script = jedi.Script(path=str(absolute), project=project, environment=env)
            if len(parts) == 1:
                inferred = script.infer(line=line, column=column)
                mode = "direct"
            else:
                offset = sum(len(part) + 1 for part in parts[:-2])
                inferred = script.infer(line=line, column=column + offset)
                mode = "method"
        except Exception as error:  # noqa: BLE001
            key = f"infer-error:{type(error).__name__}"
            original[key] += 1
            corrected[key] += 1
            continue
        if not inferred:
            original["unresolved"] += 1
            corrected["unresolved"] += 1
            continue
        d = inferred[0]
        module_path = getattr(d, "module_path", None)
        try:
            relative = Path(module_path).resolve().relative_to(project_root).as_posix() if module_path else None
        except ValueError:
            relative = None
        name = d.name or ""
        method = parts[-1]
        before = original_verdict(mode, relative, name, method, tables)
        original[before] += 1

        in_snapshot = relative is not None and relative in inventory
        after = original_verdict(mode, relative if in_snapshot else None, name, method, tables)
        if before != after:
            moved[f"{before} -> {after}"] += 1
            top = "/".join(relative.split("/")[:4]) if relative else "?"
            external_targets[top] += 1
        if after == "edge-instantiation" and relative not in meta_class_files.get(name, set()):
            loose_instantiation.append({"call": f"{file}:{line}:{column}", "callee": ".".join(parts),
                                        "target": f"{relative}:{d.line}", "class_declared_in":
                                        sorted(meta_class_files.get(name, set()))[:4]})
        corrected[after] += 1

        if after in GAP:
            row = {"call": f"{file}:{line}:{column}", "callee": ".".join(parts), "verdict": after,
                   "jedi": {"type": d.type, "name": name, "file": relative, "line": d.line,
                            "full_name": d.full_name}}
            if mode == "method":
                why = method_cause(row, script, line, column, parts, d, project_root, inventory,
                                   tables, meta_by_file)
            else:
                why = cause_of(row, d, mode, method, relative, project_root, meta_by_file.get(relative, set()))
            row["cause"] = why
            gap_cause[why] += 1
            gap_cause_by_verdict[after][why] += 1
            rows.append(row)

    published = fix1.get("verdicts", {})
    edges = lambda c: sum(v for k, v in c.items() if k.startswith("edge-"))  # noqa: E731
    gap = lambda c: sum(c.get(k, 0) for k in GAP)  # noqa: E731
    total = sum(v for k, v in corrected.items())
    result = {
        "project": str(project_root),
        "positions": len(selected),
        "replication": {"published": published, "replayed": dict(original),
                        "identical": dict(original) == published},
        "original": {"edges": edges(original), "gap": gap(original)},
        "corrected": {"verdicts": dict(corrected), "edges": edges(corrected), "gap": gap(corrected),
                      "edge_share": edges(corrected) / total if total else None},
        "moved_to_external": dict(moved.most_common()),
        "moved_targets_by_directory": dict(external_targets.most_common(12)),
        "loose_instantiation": {"count": len(loose_instantiation), "examples": loose_instantiation[:25]},
        "gap_cause": dict(gap_cause.most_common()),
        "gap_cause_by_verdict": {k: dict(v.most_common()) for k, v in gap_cause_by_verdict.items()},
        "gap_rows": rows,
    }
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("positions", "original", "corrected", "moved_to_external",
                                             "moved_targets_by_directory", "gap_cause",
                                             "gap_cause_by_verdict")}, indent=2))
    print("replication identical to the published run:", result["replication"]["identical"])
    print("loose edge-instantiation (class not declared in the target file):", len(loose_instantiation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
