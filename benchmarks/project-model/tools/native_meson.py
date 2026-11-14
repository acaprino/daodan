"""Meson: targets as `meson introspect` reports them, first from the source tree (no configure), then from a
build directory configured outside the project (`meson setup`), which runs meson.build and may fetch wraps.
"""
from __future__ import annotations

import re
from pathlib import Path

import native_common as common

VERSION = "Meson 1.6.1"
VERSION_COMMAND = ["meson", "--version"]
TRIGGERS = ("meson.build",)
COMMAND = "meson introspect --projectinfo --targets meson.build; meson setup <work>/b; meson introspect <work>/b"
SECTIONS = ["--projectinfo", "--targets", "--dependencies", "--tests"]


def _standard(parameters: list[str]) -> str | None:
    for item in parameters:
        match = re.match(r"^-std=(\S+)$", item)
        if match:
            return match.group(1)
    return None


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir), Path(work_dir)
    if not (root / "meson.build").is_file():
        return {}
    errors, raw = [], {}
    source = common.run(["meson", "introspect", *SECTIONS[:3], "--indent", "meson.build"], root,
                        name="meson introspect meson.build")
    raw["from source"] = (source.stdout[:400] if source.returncode == 0 else common.error_of(source))
    build = work / "meson-build"
    setup = common.run(["meson", "setup", str(build), str(root)], root, name="meson setup")
    if setup.returncode != 0:
        errors.append(f"meson setup: {common.error_of(setup)}")
    data = None
    if (build / "meson-info").is_dir():
        done = common.run(["meson", "introspect", *SECTIONS, str(build)], root, name="meson introspect <build>")
        data = common.json_or_none(done.stdout)
    if not isinstance(data, dict):
        data = common.json_or_none(source.stdout) if source.returncode == 0 else None
        raw["used"] = "source introspection"
    if not isinstance(data, dict):
        common.NOTES.update(errors=errors, raw=raw)
        return {}
    project = (data.get("projectinfo") or {}).get("descriptive_name")
    tests = {}
    for test in data.get("tests") or []:
        for exe in test.get("cmd") or []:
            tests.setdefault(Path(exe).name, []).append(test.get("name"))
    units = []
    for target in data.get("targets") or []:
        unit_root = common.rel(Path(target.get("defined_in", root / "meson.build")).parent, root)
        sources, includes, args, standard = [], [], [], None
        for group in target.get("target_sources") or []:
            sources += [common.rel(s, root) for s in group.get("sources") or []]
            parameters = group.get("parameters") or []
            standard = standard or _standard(parameters)
            for item in parameters:
                if item.startswith("-I"):
                    path = Path(item[2:])
                    absolute = path if path.is_absolute() else build / path
                    rel = common.rel(absolute, root)
                    if not rel.startswith("/") and not rel.startswith("..") and (root / rel).is_dir():
                        includes.append(rel)
                elif item.startswith("-D"):
                    args.append(item)
        config = {"project": project, "type": target.get("type", "").replace(" ", "_"),
                  "sources": sorted(set(sources))}
        if includes:
            config["include_directories"] = sorted(set(includes))
        if args:
            config["c_args"] = sorted(set(args))
        if standard:
            config["c_std"] = standard
        if "installed" in target:
            config["install"] = target["installed"]
        if tests.get(Path((target.get("filename") or [""])[0]).name):
            config["tests"] = tests[Path(target["filename"][0]).name]
        units.append({"name": target.get("name"), "kind": "meson-target", "root": unit_root,
                      "manifest": common.join(unit_root, "meson.build"),
                      "source_roots": sorted({common.parent(s) for s in sources}), "config": config})
    dependencies = [{"name": d.get("name"), "resolved": d.get("version") or None, "declared_in": "meson.build"}
                    for d in data.get("dependencies") or [] if d.get("name") and d.get("type") != "internal"]
    common.NOTES.update(errors=errors, raw=raw)
    return {"units": units, "dependencies": dependencies}
