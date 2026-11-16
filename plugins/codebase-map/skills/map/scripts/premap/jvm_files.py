"""Source: what the files of a Gradle build or a Maven project declare about the tools it asks for, never run.

The wrapper (`gradle/wrapper/gradle-wrapper.properties`, `.mvn/wrapper/maven-wrapper.properties`): the unit's
`config.wrapper` and the build tool's version in the distribution's file name. A pom: the Java release it asks
for (`maven.compiler.release`, `source` and `target` properties, `java.version`, the `maven-compiler-plugin`'s
`release`, `source` and `target`) and the version of the `kotlin-maven-plugin`, each a property of the same pom
or a literal, its field the path in the pom with the plugin by its artifactId (`properties.java.version`,
`maven-compiler-plugin.configuration.source`). A value naming a property the pom does not define, and a Gradle
build's Java version, which lives in build scripts only Gradle runs, are `toolchain_undeclared` gaps.
"""
from __future__ import annotations

from pathlib import PurePosixPath
import re
import xml.etree.ElementTree as ET

import confinement

NAME, VERSION, RANK = "jvm-files", "daodan/premap/v1", "reader"
WRAPPERS = {"gradle": ("gradle/wrapper/gradle-wrapper.properties", r"gradle-([0-9][^-/]*)-(?:bin|all)\.zip$"),
            "maven": (".mvn/wrapper/maven-wrapper.properties", r"apache-maven-([0-9][^-/]*)-bin\.zip$")}
JAVA_PROPERTIES = ("maven.compiler.release", "maven.compiler.source", "maven.compiler.target", "java.version")
COMPILER_FIELDS = ("release", "source", "target")
PLACEHOLDER = re.compile(r"^\$\{([^}]+)\}$")


def _properties(text: str) -> dict:
    """A Java `.properties` file's keys and values, escapes undone."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in "#!":
            continue
        key, _, value = re.split(r"(?<!\\)[=:]", line, maxsplit=1)[0], None, None
        parts = re.split(r"(?<!\\)\s*[=:]\s*", line, maxsplit=1)
        if len(parts) == 2:
            out[parts[0].strip()] = re.sub(r"\\(.)", r"\1", parts[1].strip())
    return out


def _line(text: str, needle: str) -> int | None:
    at = text.find(needle)
    return text.count("\n", 0, at) + 1 if at >= 0 else None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _pom(rel: str, text: str, toolchains: list, gaps: list) -> None:
    try:
        project = ET.fromstring(text)
    except ET.ParseError:
        return  # an unreadable manifest is the module graph's gap
    defined = {}
    for node in project:
        if _local(node.tag) == "properties":
            defined = {_local(child.tag): (child.text or "").strip() for child in node}
    wanted = [(f"properties.{key}", key, defined[key]) for key in JAVA_PROPERTIES if key in defined]
    for plugin in project.iter():
        if _local(plugin.tag) != "plugin":
            continue
        fields = {_local(child.tag): child for child in plugin}
        artifact = (fields["artifactId"].text or "").strip() if "artifactId" in fields else ""
        if artifact == "maven-compiler-plugin" and "configuration" in fields:
            for child in fields["configuration"]:
                if _local(child.tag) in COMPILER_FIELDS and child.text:
                    wanted.append((f"maven-compiler-plugin.configuration.{_local(child.tag)}", f"<{_local(child.tag)}>",
                                   child.text.strip()))
        if artifact == "kotlin-maven-plugin" and "version" in fields and fields["version"].text:
            value = fields["version"].text.strip()
            wanted.append(("kotlin-maven-plugin.version", "kotlin-maven-plugin", value))
    for field, needle, value in wanted:
        tool = "kotlin" if field.startswith("kotlin") else "java"
        named = PLACEHOLDER.match(value)
        if named:
            if named.group(1) not in defined or PLACEHOLDER.match(defined[named.group(1)]):
                gaps.append({"kind": "toolchain_undeclared", "path": rel,
                             "detail": f"{field} is {value}, a property this pom does not define"})
                continue
            value = defined[named.group(1)]
        toolchains.append({"tool": tool, "version": value, "declared_in": f"{rel}#{field}", "line": _line(text, needle)})


def run(context):
    graph = context.graph
    builds = {}
    for module in graph["modules"]:
        if module["provenance"] != "build":
            continue
        for ecosystem in module["ecosystems"]:
            if ecosystem in ("gradle", "maven"):
                builds.setdefault(module["members"][0]["path"], set()).add(ecosystem)
    if not builds:
        return None
    units, toolchains, gaps = [], [], []
    for folder, tools in sorted(builds.items()):
        for tool in sorted(tools):
            kind = "gradle-project" if tool == "gradle" else "maven-module"
            wrapper_rel, pattern = WRAPPERS[tool]
            rel = wrapper_rel if folder == "." else f"{folder}/{wrapper_rel}"
            path = context.root / rel
            confinement.reject_link_chain(path)
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                values = _properties(text)
                url = values.get("distributionUrl")
                units.append({"root": folder, "kind": kind, "config": {"wrapper": {
                    "file": rel, "distribution_url": url, "distribution_sha256": values.get("distributionSha256Sum")}}})
                version = re.search(pattern, url or "")
                if version:
                    toolchains.append({"tool": tool, "version": version.group(1), "declared_in": f"{rel}#distributionUrl",
                                       "line": _line(text, "distributionUrl")})
            if tool == "gradle" and any(PurePosixPath(m).name.startswith("settings.gradle")
                                        for module in graph["modules"] if module["members"][0]["path"] == folder
                                        for m in module["manifests"]):
                gaps.append({"kind": "toolchain_undeclared", "path": folder,
                             "detail": "the Java version of a Gradle build is declared in its build scripts, which "
                                       "only Gradle runs: no source states it before the build"})
    for rel in context.inventory.files:
        if PurePosixPath(rel).name == "pom.xml":
            _pom(rel, context.inventory.text(rel), toolchains, gaps)
    return {"facts": {"units": units, "toolchains": toolchains}, "gaps": gaps}
