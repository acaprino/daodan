"""Jedi in batch for Python: one process, every name of every file of the project inferred.

`analyze` reads the whole project once: `jedi.Project`, then per file `Script.get_names(all_scopes=True,
definitions=False, references=True)` and, for each name, `infer()` at its position; when every inferred value is
neither a function nor a class, `goto(follow_imports=True)` restricted to those two, as `JediEngine.definitions`
(resolve_edges.py) does for decorated functions, and also when none of them is a function, class or property of the
project (`classmethod.__get__` is a function; a property read infers its value). An edge has `via` (`infer` or `goto`) and `product`: true on the `goto`
edges that replace the inferred values under the product's rule alone. No file of the product is modified or imported.

Edge: `caller` the innermost function or class holding the name (`file::A.m`, the file when none), `callee` the
target (`file::dotted.name` of a project definition, `package::dotted.name` of an external one), `site`
`file:line:column` of the name (line from 1, column from 0, in characters, as Jedi counts), `kind` `call` when
the next token is `(`, else `read`, `external` null for the project or `{manager, package, version}`. Also `at`
(`file:line:column` of the target's name, `null` without a file) and `type` (Jedi's type of the target).
`silent` and `failed` list the names Jedi left unanswered or failed on, `file:line:column` each.

    python -I adapters/python_jedi.py PROJECT WORK_DIR ENVIRONMENT|- OUT.json
"""
from __future__ import annotations

import collections
import importlib.metadata
import json
import sys
import sysconfig
import time
from pathlib import Path

SKIP_DIRS = {"__pycache__", "node_modules", "site-packages", "venv", ".venv", "env"}


def _files(project: Path) -> list[Path]:
    out = []
    for path in sorted(project.rglob("*.py")):
        parts = path.relative_to(project).parts[:-1]
        if any(part in SKIP_DIRS or part.startswith(".") for part in parts):
            continue
        out.append(path)
    return out


def _site_packages(environment: Path | None) -> Path | None:
    if environment is None:
        return None
    found = sorted(environment.glob("lib/python*/site-packages")) + [environment / "Lib/site-packages"]
    return next((path for path in found if path.is_dir()), None)


def _distributions(site: Path | None) -> dict:
    """Top-level import name -> (distribution, version) of what lies in `site`."""
    out = {}
    if site is None:
        return out
    for dist in importlib.metadata.distributions(path=[str(site)]):
        name = dist.metadata["Name"]
        for item in dist.files or ():
            top = item.parts[0]
            if top.endswith((".dist-info", ".egg-info", ".pth", ".data")) or top in ("..", "__pycache__", "bin"):
                continue
            out.setdefault(top[:-3] if top.endswith(".py") else top, (name, dist.version))
    return out


class Origin:
    """Where a definition lives: the project, a package of the environment, or the standard library."""

    def __init__(self, project: Path, site: Path | None, version: str):
        self.project, self.site, self.version = project.resolve(), site, version
        self.packages = _distributions(site)
        self.stdlib = [Path(sysconfig.get_paths()[key]).resolve() for key in ("stdlib", "platstdlib")]

    def of(self, path: Path | None, dotted: str | None = None) -> tuple[str | None, dict | None]:
        """`(path relative to the project, None)` or `(None, external)`; `dotted` names a compiled module's top."""
        stdlib = {"manager": "python", "package": "python-stdlib", "version": self.version}
        if path is None:  # a compiled module has no file: the package that owns its top-level name, else the library
            top = (dotted or "").split(".")[0]
            if top in self.packages:
                name, version = self.packages[top]
                return None, {"manager": "python", "package": name, "version": version}
            return None, stdlib
        path = Path(path).resolve()
        if path.is_relative_to(self.project):
            return path.relative_to(self.project).as_posix(), None
        if self.site is not None and path.is_relative_to(self.site.resolve()):
            top = path.relative_to(self.site.resolve()).parts[0]
            name, version = self.packages.get(top[:-3] if top.endswith((".py", ".pyi")) else top, (top, None))
            return None, {"manager": "python", "package": name, "version": version}
        if "typeshed" in path.parts:
            tail = path.parts[path.parts.index("typeshed") + 1:]
            if tail[:1] == ("stdlib",):
                return None, stdlib
            return None, {"manager": "python", "package": "typeshed-stubs", "version": None}
        if any(path.is_relative_to(root) for root in self.stdlib):
            return None, stdlib
        return None, {"manager": "python", "package": path.parts[-1], "version": None}


def _caller(module, leaf, rel: str) -> str:
    chain, node = [], leaf.parent
    while node is not None:
        if node.type in ("funcdef", "classdef") and node.name is not leaf:
            chain.append(node.name.value)
        node = node.parent
    return f"{rel}::{'.'.join(reversed(chain))}" if chain else rel


def _peak_mb() -> int | None:
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    except ImportError:
        return None


def analyze(project_dir: Path, work_dir: Path, environment: Path | None) -> dict:
    import jedi
    import parso
    started = time.time()
    project_dir = Path(project_dir).resolve()
    environment = Path(environment).resolve() if environment else None
    roots = [str(project_dir)] + ([str(project_dir / "src")] if any((project_dir / "src").glob("*/__init__.py")) else [])
    project = jedi.Project(path=str(project_dir), added_sys_path=roots)
    env = jedi.create_environment(str(environment), safe=False) if environment else jedi.get_default_environment()
    version = ".".join(map(str, env.version_info[:2]))
    origin = Origin(project_dir, _site_packages(environment), version)
    grammar = parso.load_grammar()
    edges, seen, stats, errors = [], set(), collections.Counter(), collections.Counter()
    silent, failed = [], []
    examples = []
    for path in _files(project_dir):
        rel = path.relative_to(project_dir).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        module = grammar.parse(text)
        leaves = {leaf.start_pos: leaf for leaves in module.get_used_names().values() for leaf in leaves}
        script = jedi.Script(code=text, path=str(path), project=project, environment=env)
        stats["files"] += 1
        for name in script.get_names(all_scopes=True, definitions=False, references=True):
            line, column = name.line, name.column
            leaf = leaves.get((line, column))
            if leaf is None:
                continue
            following = leaf.get_next_leaf()
            if leaf.parent.type == "argument" and following is not None and following.value == "=":
                continue  # a keyword argument's name is no reference to a value
            stats["names"] += 1
            kind = "call" if following is not None and following.value == "(" else "read"
            try:
                found = [(item, "infer", False) for item in script.infer(line=line, column=column)]
                # The product's rule: goto only when no inferred value is a function or a class (a decorator's
                # object); then the named ones replace the inferred. Wider here: also when none of the inferred
                # functions or classes lies in the project (`classmethod.__get__` is a function).
                local = any(item.type in ("function", "class", "property") and
                            origin.of(item.module_path, item.full_name)[0] for item, _, _ in found)
                if not local:
                    named = [item for item in script.goto(line=line, column=column, follow_imports=True)
                             if item.type in ("function", "class", "property")]
                    replaced = bool(found) and all(item.type not in ("function", "class") for item, _, _ in found)
                    found += [(item, "goto", replaced and item.type != "property") for item in named]
            except Exception as error:  # an engine that cannot answer at a name leaves it unanswered
                errors[type(error).__name__] += 1
                failed.append(f"{rel}:{line}:{column}")
                if len(examples) < 5:
                    examples.append(f"{rel}:{line}:{column} {type(error).__name__}: {str(error)[:120]}")
                continue
            if not found:
                silent.append(f"{rel}:{line}:{column}")
                continue
            stats["answered"] += 1
            caller = _caller(module, leaf, rel)
            for item, via, product in found:
                target, external = origin.of(item.module_path, item.full_name)
                at = f"{target}:{item.line}:{item.column}" if target and item.line is not None else None
                label = item.full_name or item.name
                callee = f"{target}::{label}" if target else f"{external['package']}::{label}"
                key = (rel, line, column, callee, at, via)
                if key in seen:
                    continue
                seen.add(key)
                edges.append({"caller": caller, "callee": callee, "site": f"{rel}:{line}:{column}", "kind": kind,
                              "external": external, "at": at, "type": item.type, "via": via, "product": product})
    return {"edges": edges, "silent": silent, "failed": failed,
            "engine": {"name": "jedi", "version": jedi.__version__, "seconds": round(time.time() - started, 1),
                       "peak_mb": _peak_mb(), "python": version, "files": stats["files"], "names": stats["names"],
                       "answered": stats["answered"], "errors": dict(errors), "error_examples": examples,
                       "import_roots": roots, "environment": str(environment) if environment else None}}


if __name__ == "__main__":
    project, work, environment, output = sys.argv[1:5]
    result = analyze(Path(project), Path(work), None if environment == "-" else Path(environment))
    Path(output).write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["engine"]))
