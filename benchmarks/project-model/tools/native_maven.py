"""Maven: the reactor as Maven itself evaluates it (parents, BOMs, properties, profiles, extensions).

At each top-most pom.xml (a walk by file name): `help:effective-pom` (every reactor project after
inheritance and interpolation: coordinates, packaging, modules, source directories, the compiler release)
and `dependency:tree -DoutputType=json` (each project's direct dependencies with the version and scope Maven
resolved). Both evaluate the build, so they load the project's extensions and plugins.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import native_common as common

VERSION = "Maven 3.10.0 on Temurin 17"
VERSION_COMMAND = ["mvn", "-v"]
TRIGGERS = ("pom.xml",)
HELP = "org.apache.maven.plugins:maven-help-plugin:3.5.1:effective-pom"
TREE = "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree"
COMMAND = f"mvn {HELP}; mvn {TREE} -DoutputType=json"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}
SCOPE = {"compile": "runtime", "runtime": "runtime", "test": "test", "provided": "provided", "system": "build"}


def _text(node, path):
    found = node.find(path, NS)
    return found.text.strip() if found is not None and found.text else None


def _walk(tree: dict, out: dict) -> None:
    out[f"{tree.get('groupId')}:{tree.get('artifactId')}"] = tree.get("children") or []


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir), Path(work_dir)
    poms = common.find(root, {"pom.xml"})
    tops = [p for p in poms if not any(common.parent(p).startswith(common.parent(q) + "/") or common.parent(q) == "."
                                       for q in poms if q != p)]
    units, workspaces, toolchains, dependencies, errors = [], [], [], [], []
    for n, pom in enumerate(tops):
        here = root / common.parent(pom)
        effective, tree_file = work / f"effective-{n}.xml", work / f"tree-{n}.json"
        done = common.run(["mvn", "-B", "-ntp", "-q", HELP, f"-Doutput={effective}"], here, name="mvn help:effective-pom")
        if done.returncode != 0 or not effective.is_file():
            errors.append(f"{pom}: effective-pom: {common.error_of(done)}")
            continue
        tree_done = common.run(["mvn", "-B", "-ntp", "-q", TREE, "-DoutputType=json", f"-DoutputFile={tree_file}",
                                "-DappendOutput=true"], here, name="mvn dependency:tree -DoutputType=json")
        trees: dict = {}
        if tree_done.returncode == 0 and tree_file.is_file():
            for item in common.json_stream(tree_file.read_text(encoding="utf-8")):
                if isinstance(item, dict):
                    _walk(item, trees)
        else:
            errors.append(f"{pom}: dependency:tree: {common.error_of(tree_done)}")
        document = ET.parse(effective).getroot()
        projects = [document] if document.tag.endswith("}project") else document.findall("m:project", NS)
        coords = {}
        for project in projects:
            group = _text(project, "m:groupId") or _text(project, "m:parent/m:groupId")
            coords[f"{group}:{_text(project, 'm:artifactId')}"] = project
        for ga, project in coords.items():
            build_dir = _text(project, "m:build/m:directory")
            unit_root = common.rel(Path(build_dir).parent, root) if build_dir else common.parent(pom)
            sources = [common.rel(d, root) for d in (_text(project, "m:build/m:sourceDirectory"),
                                                     _text(project, "m:build/m:testSourceDirectory"))
                       if d and Path(d).is_dir()]
            depends = []
            for child in trees.get(ga, []):
                name = f"{child.get('groupId')}:{child.get('artifactId')}"
                if name in coords:
                    depends.append(name)
                    continue
                scope = "optional" if str(child.get("optional")).lower() == "true" else \
                    SCOPE.get(child.get("scope") or "compile", child.get("scope"))
                dependencies.append({"unit": ga, "name": name, "resolved": child.get("version"), "scope": scope,
                                     "declared_in": common.join(unit_root, "pom.xml")})
            modules = [m.text.strip() for m in project.findall("m:modules/m:module", NS) if m.text]
            config = {"packaging": _text(project, "m:packaging") or "jar"}
            if modules:
                config["nested_modules"] = modules
            main, test = _text(project, "m:build/m:sourceDirectory"), _text(project, "m:build/m:testSourceDirectory")
            if (_text(project, "m:packaging") or "jar") != "pom":
                config["source_sets"] = {k: [common.rel(v, root)] for k, v in (("main", main), ("test", test)) if v}
            tasks = []
            for plugin in project.findall("m:build/m:plugins/m:plugin", NS):
                if _text(plugin, "m:artifactId") != "maven-compiler-plugin":
                    continue
                for execution in plugin.findall("m:executions/m:execution", NS):
                    tasks += [f"maven-compiler-plugin:{g.text.strip()}@{_text(execution, 'm:id')}"
                              for g in execution.findall("m:goals/m:goal", NS) if g.text]
            if tasks:
                config["compile_tasks"] = tasks
            units.append({"name": ga, "kind": "maven-module", "root": unit_root,
                          "manifest": common.join(unit_root, "pom.xml"), "source_roots": sources,
                          "depends_on": sorted(set(depends)), "config": config})
        workspaces.append({"tool": "maven", "root": common.parent(pom), "members": [u["root"] for u in units[-len(coords):]]})
        top = projects[0]
        release = (_text(top, "m:properties/m:maven.compiler.release") or
                   next((_text(p, "m:configuration/m:release") for p in top.findall("m:build/m:plugins/m:plugin", NS)
                         if _text(p, "m:artifactId") == "maven-compiler-plugin" and _text(p, "m:configuration/m:release")),
                        None) or _text(top, "m:properties/m:maven.compiler.source"))
        if release:
            toolchains.append({"tool": "java", "version": release, "declared_in": pom})
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "toolchains": toolchains, "dependencies": dependencies}
