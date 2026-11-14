"""Gradle through the Build Server Protocol: microsoft/build-server-for-gradle 0.4.0 (built from its tag in the
image), asked by `bsp_client.py` for workspace/buildTargets, buildTarget/sources, dependencyModules and
javacOptions, with no compile request. The server runs Gradle through the Tooling API with an init script of its
own, so configuring the build runs the project's scripts. One target per source set; a unit is a Gradle
project (the targets sharing a baseDirectory). BSP gives no project path, so units carry no name and
`depends_on` names units by root; dependency modules are the whole classpath, transitive ones included.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import native_common as common

VERSION = "build-server-for-gradle 0.4.0 (Gradle of the wrapper, else 9.9.1) on Temurin 17"
VERSION_COMMAND = ["cat", "/opt/bsg/VERSION"]
TRIGGERS = ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts")
COMMAND = "build-server-for-gradle: build/initialize, workspace/buildTargets, buildTarget/sources, dependencyModules"
LAUNCH = ["/opt/bsg/launch.sh"]
CLIENT = Path(__file__).with_name("bsp_client.py")
TIMEOUT = 600


def _path(uri: str, root: Path) -> str:
    return common.rel(Path(unquote(urlparse(uri).path)), root)


def _source_set(target: dict) -> str:
    query = parse_qs(urlparse(target["id"]["uri"]).query)
    if query.get("sourceset"):
        return query["sourceset"][0]
    name = target.get("displayName") or ""
    return name[name.rfind("[") + 1:name.rfind("]")] if "[" in name else name


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir), Path(work_dir)
    scripts = common.find(root, set(TRIGGERS))
    pool = [s for s in scripts if Path(s).name.startswith("settings.")] or scripts
    tops = sorted({common.parent(s) for s in pool
                   if not any(common.parent(q) != common.parent(s) and
                              (common.parent(q) == "." or common.parent(s).startswith(common.parent(q) + "/"))
                              for q in pool)})
    units, dependencies, errors, raw = {}, [], [], {"steps": {}, "sample_target": None, "java": {}}
    for n, directory in enumerate(tops):
        out = work / f"bsp-{n}.json"
        done = common.run([sys.executable, "-I", str(CLIENT), str(root / directory), str(out), str(TIMEOUT), "--",
                           *LAUNCH], root / directory, name="bsp: gradle model", timeout=TIMEOUT + 60)
        data = common.json_or_none(out.read_text(encoding="utf-8")) if out.is_file() else None
        if not isinstance(data, dict):
            errors.append(f"{directory}: {common.error_of(done)}")
            continue
        errors += [f"{directory}: {e}" for e in data.get("errors") or []]
        raw["steps"][directory] = data.get("steps")
        raw.setdefault("server_stderr", data.get("server_stderr"))
        targets = data.get("targets") or []
        if targets and raw["sample_target"] is None:
            raw["sample_target"] = targets[0]
        by_id = {t["id"]["uri"]: t for t in targets}
        roots = {uri: _path(t.get("baseDirectory") or uri, root) for uri, t in by_id.items()}
        sources = {item["target"]["uri"]: item for item in (data.get("sources") or {}).get("items") or []}
        modules = {item["target"]["uri"]: item for item in (data.get("modules") or {}).get("items") or []}
        for uri, target in by_id.items():
            unit_root = roots[uri]
            unit = units.setdefault(unit_root, {"kind": "gradle-project", "root": unit_root, "source_roots": set(),
                                                "depends_on": set(), "config": {"source_sets": {}}})
            name = _source_set(target)
            item = sources.get(uri) or {}
            dirs = sorted({_path(r, root) for r in item.get("roots") or []} |
                          {_path(s["uri"], root) for s in item.get("sources") or [] if not s.get("generated")
                           and s.get("kind") == 2})
            unit["config"]["source_sets"][name] = dirs
            unit["source_roots"].update(d for d in dirs if (root / d).is_dir())
            for dep in target.get("dependencies") or []:
                other = roots.get(dep["uri"])
                if other and other != unit_root:
                    unit["depends_on"].add(other)
            jvm = target.get("data") or {}
            if isinstance(jvm, dict) and jvm.get("javaVersion"):
                unit["config"]["java_version"] = jvm["javaVersion"]
                raw["java"][f"{unit_root} [{name}]"] = {k: jvm.get(k) for k in ("javaVersion", "javaHome",
                                                                                 "sourceCompatibility",
                                                                                 "targetCompatibility",
                                                                                 "gradleVersion") if k in jvm}
            scope = "test" if "test" in name.lower() else "runtime"
            for module in (modules.get(uri) or {}).get("modules") or []:
                dependencies.append({"unit": unit_root, "name": module.get("name"), "resolved": module.get("version"),
                                     "scope": scope})
    out_units = []
    for unit in units.values():
        unit["source_roots"] = sorted(unit["source_roots"])
        unit["depends_on"] = sorted(unit["depends_on"])
        out_units.append(unit)
    seen, unique = set(), []
    for d in dependencies:
        key = (d["unit"], d["name"], d["scope"])
        if key not in seen:
            seen.add(key)
            unique.append(d)
    common.NOTES.update(errors=errors[:12], raw=raw)
    return {"units": out_units, "dependencies": unique}
