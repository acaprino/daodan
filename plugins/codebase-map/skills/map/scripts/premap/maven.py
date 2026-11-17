"""Source: Maven's own reactor, `help:effective-pom`, at each top folder holding a pom.xml.

`commands` describes, for Daodan's container, `mvn help:effective-pom` with the Maven Daodan carries: Maven builds
the reactor of the pom in that folder as a plain `mvn` would, profiles activated as their `activation` says,
parents and properties resolved, and prints every project of it after inheritance and interpolation. It reaches
the registries (the help plugin, parent poms, the build's extensions) and loads the build's extensions. `read`
turns each project into a `maven-module` unit named `groupId:artifactId`, rooted at the folder of its build
directory's parent, with its pom.xml as manifest, the reactor projects it depends on as edges, and its source
folders (the build's own and the ones a plugin's configuration names, `PLUGIN_SOURCES`), and as registries the
origins of the repositories and plugin repositories it resolves from (Central from the super POM, those the pom or a
parent declares), and what maven-compiler-plugin leaves out of each source folder it compiles (`compile_excludes`,
its `excludes` and `testExcludes`, each pattern relative to that folder); the reactor is a `maven` workspace with the folders of the projects its root's modules list, profiles
included, as members. A pom.xml no reactor holds states nothing: Maven does not build it.
"""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
import xml.etree.ElementTree as ET

from premap.origins import origin

NAME, VERSION, RANK = "maven", "3.10.0", "model"  # `indexers/jvm.py` MAVEN
DOWNLOAD = (("https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.10.0/apache-maven-3.10.0-bin.zip",
             "1f6d9909266510f039f59aa0e13dcd2c66da85f043e56276e41f2918f8bddaff"),)  # what the runner carries
FILE = "pom.xml"
HELP = "org.apache.maven.plugins:maven-help-plugin:3.5.1:effective-pom"
SCRIPT = f'o=$(mktemp) && mvn -B -ntp -q {HELP} -Doutput="$o" >&2 && cat "$o"'
NS = "{http://maven.apache.org/POM/4.0.0}"
# Where a plugin's configuration names the folders it compiles: kotlin-maven-plugin, build-helper-maven-plugin.
PLUGIN_SOURCES = (("sourceDirs", "sourceDir"), ("sources", "source"))
REPOSITORIES = (("repositories", "repository"), ("pluginRepositories", "pluginRepository"))
# What maven-compiler-plugin leaves out of the folder it compiles, its patterns relative to that folder.
EXCLUDES = (("excludes", "exclude", "sourceDirectory"), ("testExcludes", "testExclude", "testSourceDirectory"))


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def commands(context):
    folders = sorted({_folder(rel) for rel in context.inventory.files if PurePosixPath(rel).name == FILE},
                     key=lambda f: (f.count("/"), f))
    tops = [f for f in folders if not any(o != f and _inside(f, o) for o in folders)]
    return [{"tool": "maven", "argv": ["sh", "-c", SCRIPT], "cwd": top, "env": {"MAVEN_OPTS": "-Xmx512m"},
             "network": "registries"} for top in tops] or None


def _text(node, path: str) -> str | None:
    found = node.find(path)
    return found.text.strip() if found is not None and found.text else None


def read(context, commands, results):
    units, workspaces, packages, gaps, seen_pkgs = [], [], [], [], set()
    for command, result in zip(commands, results):
        root = result.get("root") or "/"
        text = result["stdout"] or ""
        if result["returncode"] != 0 or "<project" not in text:
            gaps.append({"kind": "model_failed", "path": command["cwd"],
                         "detail": f"mvn help:effective-pom: {(result['stderr'] or text).strip()[-300:]}"})
            continue
        tree = ET.fromstring(text[text.index("<"):])
        projects = [tree] if tree.tag == f"{NS}project" else tree.findall(f"{NS}project")

        def rel(path: str | None) -> str | None:
            if not path:
                return None
            value = posixpath.relpath(posixpath.normpath(path), root)
            return None if value.startswith("..") else value

        found = {}
        for project in projects:
            key = f"{_text(project, f'{NS}groupId')}:{_text(project, f'{NS}artifactId')}"
            folder = rel(posixpath.dirname(_text(project, f"{NS}build/{NS}directory") or ""))
            if folder is not None:
                found[key] = (project, folder)
        for key, (project, folder) in found.items():
            manifest = posixpath.join(folder, FILE).removeprefix("./")
            sources = [rel(_text(project, f"{NS}build/{NS}{tag}"))
                       for tag in ("sourceDirectory", "testSourceDirectory")]
            for plugin in project.findall(f"{NS}build/{NS}plugins/{NS}plugin"):  # the folders a plugin compiles
                sources += [rel((node.text or "").strip()) for held, tag in PLUGIN_SOURCES
                            for node in plugin.iterfind(f".//{NS}{held}/{NS}{tag}")]
            excludes = {}
            for plugin in project.findall(f"{NS}build/{NS}plugins/{NS}plugin"):
                if _text(plugin, f"{NS}artifactId") != "maven-compiler-plugin":
                    continue
                for held, tag, where in EXCLUDES:  # the plugin's configuration and its executions'
                    compiled = rel(_text(project, f"{NS}build/{NS}{where}"))
                    patterns = {(node.text or "").strip() for node in plugin.iterfind(f".//{NS}{held}/{NS}{tag}")}
                    if compiled and patterns - {""}:
                        excludes.setdefault(compiled, set()).update(patterns - {""})
            registries = {origin(_text(repository, f"{NS}url")) for held, tag in REPOSITORIES
                          for repository in project.findall(f"{NS}{held}/{NS}{tag}")} - {None}
            all_deps = {f"{_text(d, f'{NS}groupId')}:{_text(d, f'{NS}artifactId')}"
                        for d in project.findall(f"{NS}dependencies/{NS}dependency")
                        if _text(d, f"{NS}groupId") and _text(d, f"{NS}artifactId")}
            for coord in sorted(all_deps - set(found)):
                if (coord.casefold(), manifest) not in seen_pkgs:
                    seen_pkgs.add((coord.casefold(), manifest))
                    packages.append({"ecosystem": "maven", "name": coord, "declared_in": manifest})
            units.append({"name": key, "kind": "maven-module", "root": folder,
                          "manifest": manifest,
                          "source_roots": sorted({s for s in sources if s and s in context.inventory.directories}),
                          "depends_on": sorted(all_deps & set(found) - {key}),
                          **({"registries": sorted(registries)} if registries else {}),
                          **({"compile_excludes": {compiled: sorted(patterns) for compiled, patterns in sorted(
                              excludes.items())}} if excludes else {})})
        top = projects[0] if projects else None
        if top is not None and len(found) > 1:
            first = rel(posixpath.dirname(_text(top, f"{NS}build/{NS}directory") or "")) or command["cwd"]
            workspaces.append({"tool": "maven", "root": first,
                               "members": sorted(f for _, f in found.values() if f != first)})
    facts = {key: value for key, value in (("units", units), ("workspace", workspaces),
                                           ("packages", packages)) if value}
    return {"facts": facts, "gaps": gaps}
