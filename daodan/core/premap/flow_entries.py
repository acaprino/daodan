"""Flow starts declared to Cargo and Python packaging, joined to definitions already in the snapshot."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path, PurePosixPath
import posixpath

import confinement
from snapshot_store import open_snapshot


def workflow_triggers(file, document):
    """The YAML document Renovate already read. The path after # names the exact workflow property."""
    on = document.get("on") if isinstance(document, dict) else None
    if isinstance(on, str):
        events = [(on, f"{file}#on", None)]
    elif isinstance(on, list):
        events = [(name, f"{file}#on.{i}", None) for i, name in enumerate(on) if isinstance(name, str)]
    elif isinstance(on, dict):
        events = [(name, f"{file}#on.{name}", value) for name, value in on.items()]
    else:
        return []
    found = []
    for name, site, value in events:
        if name == "schedule" and isinstance(value, list):
            for i, record in enumerate(value):
                if isinstance(record, dict) and isinstance(record.get("cron"), str):
                    found.append({"event": name, "label": record["cron"], "declared_in": f"{site}.{i}.cron"})
        else:
            found.append({"event": name, "label": name, "declared_in": site})
    return found


def service_and_workflow_entries(report):
    """Recorded activation conditions identify the declaration even when no source handler is established."""
    rows = []
    def append(shape, label, declared_in, kind):
        file, _, anchor = declared_in.partition("#")
        site = f"{file}:{anchor[1:]}" if anchor.startswith("L") and anchor[1:].isdecimal() else file
        rows.append({"reader": "manifesto", "shape": shape, "label": label, "declared_in": declared_in,
                     "site": site, "symbol": f"{file}::<module>", **({"kind": kind} if kind else {}),
                     "gap": f"{declared_in}: the declaration does not identify a project handler"})

    for trigger in report.get("workflow_triggers", ()):
        name = trigger["event"]
        kind = {"schedule": "orario", "workflow_dispatch": "comando"}.get(name)
        if name in ("push", "pull_request", "pull_request_target", "create", "delete", "release"):
            kind = "evento del repository"
        append(f"github.on.{name}", trigger["label"], trigger["declared_in"], kind)
    for item in report.get("configured_services", ()):
        append("compose.services", item["name"], item["declared_in"], "avvio di un processo")
    return rows


def _python_paths(unit, parts):
    root = PurePosixPath(unit["root"])
    mapping = unit["config"].get("package_dir") or {}
    # setuptools.discovery.find_package_path uses host paths. Snapshot keys are POSIX even on Windows.
    for count in range(len(parts), -1, -1):
        package = ".".join(parts[:count])
        if package in mapping:
            stem = PurePosixPath(posixpath.normpath(str(root.joinpath(mapping[package], *parts[count:]))))
            if count == len(parts):
                return [str(stem / "__init__.py")]
            return [str(stem.with_suffix(".py")), str(stem / "__init__.py")]
    bases = [root] if mapping else unit.get("source_roots") or [root]
    stems = (PurePosixPath(base).joinpath(*parts) for base in bases)
    return [str(path) for stem in stems for path in (stem.with_suffix(".py"), stem / "__init__.py")]


def declarations(units, store):
    """Only the root function in the declared file can answer. Never import a Python package or build a crate."""
    @lru_cache(maxsize=64)
    def functions(path):
        if store.format == "sqlite":
            if not store.has_file(path):
                return None
            return store.connection.execute(
                "SELECT name,l0 FROM sem_declarations WHERE file=? AND scope='module' AND kind='function'", (path,)
            ).fetchall()
        entry = store.get_file(path)
        if entry is None:
            return None
        semantic = entry.get("semantic") or {}
        return [(d["name"], d["span"][0]) for d in semantic.get("declarations", ())
                if d.get("scope") == "module" and d["kind"] == "function"]

    def candidate(shape, label, declared_in, paths, function, target):
        row = {"reader": "manifesto", "shape": shape, "kind": "comando" if shape == "project.scripts" else
               "avvio di un processo", "declared_in": declared_in, "label": label, "handler_source": "manifesto"}
        files = [p for p in sorted(set(paths)) if functions(p) is not None]
        if len(files) == 1:
            matches = [line for name, line in functions(files[0]) if name == function]
            if len(matches) == 1:
                return {**row, "site": f"{files[0]}:{matches[0]}", "symbol": f"{files[0]}::{function}"}
        manifest = declared_in.split("#", 1)[0]
        return {**row, "site": manifest, "symbol": f"{manifest}::<module>",
                "gap": f"{declared_in}: no unique snapshot function for {target}"}

    rows = []
    for unit in units:
        root = PurePosixPath(unit["root"])
        config = unit.get("config") or {}
        if unit["kind"] == "cargo-crate":
            for item in config.get("targets", ()):
                if item["kind"] == "bin":
                    rows.append(candidate("cargo.bin", item["name"], unit["manifest"], [item["path"]], "main",
                                          f"{item['path']}::main"))
        if unit["kind"] != "python-project":
            continue
        for group, names in config.get("entry_points", {}).items():
            shape = f"project.{group}"
            for name, target in names.items():
                declared_in = f"{root / 'pyproject.toml'}#{shape}.{name}"
                module, _, function = target.partition(":") if isinstance(target, str) else ("", "", "")
                parts = module.split(".")
                paths = []
                if all(part.isidentifier() for part in parts) and function.isidentifier():
                    paths = _python_paths(unit, parts)
                rows.append(candidate(shape, name, declared_in, paths, function, target))
    return rows


def read_record(manifest):
    import premap
    path = premap.path(manifest)
    confinement.reject_link_chain(path)
    report = json.loads(path.read_text(encoding="utf-8"))
    if not premap.binding_matches(manifest, report["binding"]):
        raise ValueError("the pre-map belongs to a different snapshot")
    return report


def evidence(manifest):
    """Load and validate the pre-map once for all of its flow-entry readers."""
    from premap import FRAMEWORK_SOURCES, TEMPLATE_SOURCES, module_graph, noir, python_build, renovate
    manifest = Path(manifest)
    try:
        report = read_record(manifest)
    except (OSError, KeyError, TypeError, ValueError) as error:
        return [], [noir.unavailable(error), {"kind": "declared_entries_unavailable", "source": "manifesto",
                    "detail": str(error), "remedy": "refresh the pre-map for this snapshot"}]
    routes, gaps = noir.from_record(report)
    for source in FRAMEWORK_SOURCES:
        framework, framework_gaps = source.from_record(report)
        routes, gaps = routes + framework, gaps + framework_gaps
    # A template source's rows are not routes: they stand for, or join, the tree reader's at the same events (`entries.compiled`); their gaps are told here
    for source in TEMPLATE_SOURCES:
        gaps += source.from_record(report)[1]
    rows = report.get("declared_entries")
    if rows is None:
        # Cargo targets in older reports already identify the path. No need for another Cargo run.
        with open_snapshot(manifest) as store:
            rows = declarations(report.get("units", ()), store)
    sources = {s["source"]: s for s in report["sources"]}
    unavailable = {"source_unavailable", "source_failed", "model_not_run"}
    for gap in report.get("gaps", ()):
        source = gap.get("source", "").partition("@")[0]
        kind, path = gap.get("kind"), gap.get("path", "")
        if source in {"cargo", python_build.NAME} and kind in unavailable | {"model_failed"}:
            gaps.append(gap)
        elif source == module_graph.NAME and kind in unavailable | {"compose_not_read"}:
            gaps.append(gap)
        elif source == renovate.NAME:
            # Its dependency scan runs even without workflows. Only the second command reads CI YAML.
            workflow = path == renovate.WORKFLOWS or path.startswith(renovate.WORKFLOWS + "/")
            yaml_not_run = kind in unavailable and sources.get(gap["source"], {}).get("commands", 2) > 1
            if (kind == "model_failed" and workflow) or yaml_not_run:
                gaps.append(gap)
    if any(s.startswith("python-build@") and s != f"python-build@{python_build.VERSION}" for s in sources):
        detail = "the saved Python reader did not verify package-directory mappings"
        gaps.append({"kind": "declared_entries_unavailable", "source": "python-build",
                     "detail": detail, "remedy": "refresh the pre-map for this snapshot"})
        for row in rows:
            if row["shape"] in {"project.scripts", "project.gui-scripts"}:
                file = row["declared_in"].partition("#")[0]
                row.update(site=file, symbol=f"{file}::<module>", gap=detail)
    return routes + rows + service_and_workflow_entries(report), gaps
