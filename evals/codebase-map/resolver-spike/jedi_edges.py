# /// script
# requires-python = ">=3.11"
# dependencies = ["jedi>=0.19"]
# ///
"""Spike stage 2: turn Jedi inference into real call edges, honestly.

Stage 1 measured "can the engine resolve something at this position". That
over-counts, because inferring at the start of `broker.place_order` returns the
receiver's type, and a method call on a local variable resolves to the variable
declaration, which is not a call edge.

This stage maps (receiver type, method name) onto the snapshot's own symbol
table, so an edge is counted only when the project actually declares that
method. Everything else is reported as its own category, never as an edge.

Fix 1 (measurement campaign, 2026-10-22): inference now runs against each
project's own virtual environments instead of a bare project. `--environment`
is repeatable; for every sampled file the nearest enclosing environment wins,
and a file under none of them uses the default environment. Each environment is
obtained with `jedi.api.environment.create_environment(path, safe=False)`; when
that raises (broken venv, missing base interpreter) the run falls back to
`jedi.Project(added_sys_path=[root, <every venv site-packages>])`. The mode
actually used is recorded per file, so a number is never reported without the
environment that produced it.

Known Jedi pitfall, deliberately not triggered: `jedi.settings.fast_parser =
False` raises `KeyError` inside Jedi 0.20.1 (`jedi/inference/syntax_tree.py`).
The default `True` is left alone.

Known defect in the gap buckets, found after Fix 1 and kept so the published
numbers stay reproducible: `in_project` tests `relative_to(project_root)`, and a
project's virtual environments live inside its root. Once Jedi has those
environments, every third-party target (`rich`, `_pytest`, `pydantic`) passes the
test and lands in `receiver-project-not-a-class` or
`direct-project-not-a-symbol`. The edge buckets are unaffected, because a
third-party name never matches the snapshot's symbol table. The correct test is
membership of the target file in the snapshot inventory, which is what the
Codebase Map's perimeter decides. `../python-parser/gap_diagnosis.py` replays the
same sample with that test: Jupiter's gap goes from 374 to 140, Phazly's from
181 to 67, and the edge counts are identical.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"))
from snapshot_store import _unpack, open_snapshot  # noqa: E402

import jedi  # noqa: E402
from jedi.api.environment import create_environment  # noqa: E402

# Bytecode of a project's interpreter must never land inside the read-only
# project tree. Both variables are honoured by CPython 3.8+.
_SITE_SUFFIXES = ("dist-info", "egg-info", "egg-link")


def venv_root_of(candidate: Path) -> Path:
    """A venv directory or its python executable, normalised to the venv root."""
    candidate = candidate.resolve()
    if candidate.is_dir() and (candidate / "pyvenv.cfg").is_file():
        return candidate
    if candidate.name.lower().startswith("python") and candidate.is_file():
        root = candidate.parent.parent
        if (root / "pyvenv.cfg").is_file():
            return root
    raise SystemExit(f"--environment {candidate} is neither a venv directory nor its python.exe")


def site_packages_of(root: Path) -> Path | None:
    candidate = root / "Lib" / "site-packages"
    if candidate.is_dir():
        return candidate
    for child in (root / "lib").glob("python*/site-packages"):
        if child.is_dir():
            return child
    return None


def top_level_names(site_packages: Path | None) -> list[str]:
    """Importable top-level names visible in a site-packages directory."""
    if site_packages is None or not site_packages.is_dir():
        return []
    names: set[str] = set()
    for child in site_packages.iterdir():
        name = child.name
        if name.startswith("__") or name.startswith(".") or name.startswith("_virtualenv"):
            continue
        if any(name.endswith(suffix) for suffix in _SITE_SUFFIXES):
            continue
        if child.is_dir():
            names.add(name)
        elif name.endswith(".py"):
            names.add(name[:-3])
        elif name.endswith(".pth"):
            continue
        else:
            names.add(name)
    return sorted(names)


def interpreter_version(root: Path) -> str:
    exe = root / "Scripts" / "python.exe"
    if not exe.is_file():
        exe = root / "bin" / "python"
    if not exe.is_file():
        return "interpreter-missing"
    try:
        out = subprocess.run([str(exe), "-c",
                              "import sys;print('.'.join(map(str,sys.version_info[:3])))"],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        return f"interpreter-error:{type(error).__name__}"
    version = out.stdout.strip()
    return version or f"interpreter-failed:{out.stderr.strip()[:120]}"


def load_symbol_table(manifest: Path):
    """file -> set of method symbol names, and class short name -> defining files."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--files", type=int, default=40)
    parser.add_argument("--per-file", type=int, default=40)
    parser.add_argument("--environment", action="append", default=[], type=Path,
                        help="venv directory or its python.exe; repeatable, nearest enclosing wins")
    parser.add_argument("--default-environment", type=Path, default=None,
                        help="override which environment a file under no venv subtree uses")
    parser.add_argument("--label", default=None, help="free-text variant label recorded in the output")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    project_root = args.project.resolve()
    with open_snapshot(args.manifest) as store:
        manifest_root = Path(store.metadata["root"])
    methods_by_file, classes_by_name, functions_by_file = load_symbol_table(args.manifest)

    db = sqlite3.connect(args.manifest)
    by_file = collections.Counter()
    positions: dict[str, list[tuple[int, int, list[str], str]]] = collections.defaultdict(list)
    for file, line, column, blob in db.execute(
            "SELECT r.file, r.l0, r.c0, r.payload FROM sem_references r "
            "JOIN sem_coverage c ON c.file=r.file "
            "WHERE r.kind='call' AND r.resolution!='resolved' AND c.language='python'"):
        record = _unpack(blob)
        if record.get("reason") == "unbound-name":
            continue
        by_file[file] += 1
        positions[file].append((line, column, record.get("parts") or [],
                                record.get("reason") or "none"))
    sample = [file for file, _ in by_file.most_common(args.files)]
    selected = [(file, item) for file in sample for item in positions[file][:args.per_file]]

    # --- Fix 1: environment inventory and nearest-enclosing assignment -------
    candidates = [venv_root_of(path) for path in args.environment]

    def scope_of(root: Path) -> Path:
        """The source subtree an environment serves.

        A conventional venv (`.venv`, `venv`, `env`) lives *inside* the package
        directory it serves, and no source file is ever inside the venv itself,
        so nearest-enclosing must match the parent. Anything else scopes to its
        own directory.
        """
        parent = root.parent
        if root.name in (".venv", "venv", "env") and parent != root:
            try:
                parent.relative_to(project_root)
            except ValueError:
                return root
            return parent
        return root

    env_info: dict[Path, dict] = {}
    for root in candidates:
        sp = site_packages_of(root)
        env_info[root] = {
            "path": root.as_posix(),
            "scope": scope_of(root).as_posix(),
            "python_version": interpreter_version(root),
            "site_packages": sp.as_posix() if sp else None,
            "top_level_name_count": len(top_level_names(sp)),
            "top_level_names": top_level_names(sp),
            "create_environment": None,
        }

    def depth(root: Path) -> int:
        try:
            return len(scope_of(root).relative_to(project_root).parts)
        except ValueError:
            return 10 ** 6

    ordered = sorted(candidates, key=lambda r: (depth(r), 0 if r.name == ".venv" else 1, str(r)))
    if args.default_environment is not None:
        default_root = venv_root_of(args.default_environment)
        if default_root not in env_info:
            sp = site_packages_of(default_root)
            env_info[default_root] = {
                "path": default_root.as_posix(),
                "scope": scope_of(default_root).as_posix(),
                "python_version": interpreter_version(default_root),
                "site_packages": sp.as_posix() if sp else None,
                "top_level_name_count": len(top_level_names(sp)),
                "top_level_names": top_level_names(sp),
                "create_environment": None,
            }
            candidates.append(default_root)
    else:
        default_root = ordered[0] if ordered else None

    jedi_envs: dict[Path, object | None] = {}
    env_modes: dict[Path, str] = {}
    for root in candidates:
        try:
            jedi_envs[root] = create_environment(str(root), safe=False)
            env_modes[root] = "create_environment"
            env_info[root]["create_environment"] = "ok"
        except Exception as error:  # noqa: BLE001
            jedi_envs[root] = None
            env_modes[root] = "added_sys_path"
            env_info[root]["create_environment"] = f"failed:{type(error).__name__}: {error}"[:400]

    fallback_sys_path = [str(project_root)] + [
        str(site_packages_of(root)) for root in candidates if site_packages_of(root)]
    fallback_project = jedi.Project(path=str(project_root), added_sys_path=fallback_sys_path)
    plain_project = jedi.Project(path=str(project_root), added_sys_path=[str(project_root)])

    def environment_for(absolute: Path):
        """(project, environment, mode, root) for one source file.

        Nearest-enclosing-wins over each environment's *scope*, the source
        subtree it serves, not the venv directory itself.
        """
        best_root = None
        best_scope: Path | None = None
        for candidate in candidates:
            scope = Path(env_info[candidate]["scope"])
            try:
                absolute.relative_to(scope)
            except ValueError:
                continue
            if best_scope is None or len(scope.parts) > len(best_scope.parts):
                best_root, best_scope = candidate, scope
        root = best_root if best_root is not None else default_root
        if root is None:
            return plain_project, None, "project-only", None
        env = jedi_envs.get(root)
        if env is not None:
            return plain_project, env, "create_environment", root
        return fallback_project, None, "added_sys_path", root

    verdicts = collections.Counter()
    by_reason = collections.defaultdict(collections.Counter)
    by_environment = collections.defaultdict(collections.Counter)
    edges = collections.Counter()
    examples = collections.defaultdict(list)
    latencies: list[float] = []
    per_file_environment: dict[str, dict] = {}
    started_all = time.perf_counter()

    def in_project(path) -> Path | None:
        if path is None:
            return None
        try:
            return Path(path).resolve().relative_to(project_root)
        except ValueError:
            return None

    for file, (line, column, parts, reason) in selected:
        absolute = manifest_root / file
        if not absolute.is_file() or not parts:
            verdicts["skipped"] += 1
            continue
        project, environment, mode, env_root = environment_for(absolute)
        if file not in per_file_environment:
            per_file_environment[file] = {
                "environment": env_root.as_posix() if env_root else None,
                "environment_scope": env_info[env_root]["scope"] if env_root else None,
                "environment_mode": mode,
                "unresolved_call_refs": by_file[file],
            }
        env_key = env_root.as_posix() if env_root else "<project-only>"
        started = time.perf_counter()
        try:
            script = jedi.Script(path=str(absolute), project=project, environment=environment)
            if len(parts) == 1:
                inferred = script.infer(line=line, column=column)
                infer_mode = "direct"
            else:
                # Column of the last receiver segment: `a.b.c()` infers `a.b`.
                offset = sum(len(part) + 1 for part in parts[:-2])
                inferred = script.infer(line=line, column=column + offset)
                infer_mode = "method"
        except Exception as error:  # noqa: BLE001
            verdicts[f"infer-error:{type(error).__name__}"] += 1
            by_reason[reason][f"infer-error:{type(error).__name__}"] += 1
            by_environment[env_key][f"infer-error:{type(error).__name__}"] += 1
            continue
        latencies.append(time.perf_counter() - started)

        if not inferred:
            key = "unresolved"
        else:
            definition = inferred[0]
            relative = in_project(getattr(definition, "module_path", None))
            name = definition.name or ""
            if infer_mode == "direct":
                if relative is None:
                    key = "direct-external"
                elif name in functions_by_file.get(relative.as_posix(), ()) or \
                        name in {m for _, m in methods_by_file.get(relative.as_posix(), ())}:
                    key = "edge-direct-call"
                    edges[f"{relative.as_posix()}::{name}"] += 1
                elif name in classes_by_name:
                    key = "edge-instantiation"
                    edges[f"{relative.as_posix()}::{name}"] += 1
                else:
                    key = "direct-project-not-a-symbol"
            else:
                method = parts[-1]
                if relative is None:
                    key = "receiver-external"
                else:
                    owner_file = relative.as_posix()
                    if (name, method) in methods_by_file.get(owner_file, ()):
                        key = "edge-method-call"
                        edges[f"{owner_file}::{name}.{method}"] += 1
                    elif name in classes_by_name:
                        key = "receiver-project-method-not-a-symbol"
                    else:
                        key = "receiver-project-not-a-class"
        verdicts[key] += 1
        by_reason[reason][key] += 1
        by_environment[env_key][key] += 1
        if len(examples[key]) < 8:
            examples[key].append(f"{file}:{line}:{column} {'.'.join(parts)}")

    total = sum(verdicts.values())
    latencies.sort()
    edge_total = sum(value for key, value in verdicts.items() if key.startswith("edge-"))
    result = {
        "stage": 2,
        "fix": "fix-1-jedi-project-environments",
        "label": args.label,
        "engine": {"name": "jedi", "version": jedi.__version__, "python": sys.version.split()[0]},
        "project": str(project_root),
        "environments": {info["path"]: {k: v for k, v in info.items() if k != "top_level_names"}
                         for info in env_info.values()},
        "environment_top_level_names": {info["path"]: info["top_level_names"]
                                        for info in env_info.values()},
        "default_environment": default_root.as_posix() if default_root else None,
        "fallback_sys_path": fallback_sys_path,
        "sample": {"files": len(sample), "positions": len(selected),
                   "unresolved_call_refs_total": sum(by_file.values())},
        "per_file_environment": per_file_environment,
        "verdicts": dict(verdicts),
        "verdicts_by_environment": {k: dict(v) for k, v in sorted(by_environment.items())},
        "real_edges": edge_total,
        "real_edge_share": (edge_total / total) if total else None,
        "verdicts_by_unresolved_reason": {k: dict(v) for k, v in sorted(by_reason.items())},
        "elapsed_seconds": time.perf_counter() - started_all,
        "latency_ms": {"mean": (sum(latencies) / len(latencies) * 1000) if latencies else None,
                       "p95": (latencies[int(len(latencies) * 0.95) - 1] * 1000) if latencies else None},
        "top_edges": edges.most_common(20),
        "examples": {k: v for k, v in examples.items() if v},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("label", "sample", "environments", "verdicts",
                                             "verdicts_by_environment", "real_edges",
                                             "real_edge_share", "elapsed_seconds", "latency_ms")},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
