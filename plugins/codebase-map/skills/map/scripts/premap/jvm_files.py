"""Source: what the files of a Gradle build or a Maven project declare about the tools it asks for, never run.

The wrapper (`gradle/wrapper/gradle-wrapper.properties`, `.mvn/wrapper/maven-wrapper.properties`): the unit's
`config.wrapper` and the build tool's version in the distribution's file name. A pom: the Java release it asks
for (`maven.compiler.release`, `source` and `target` properties, `java.version`, `kotlin.compiler.jvmTarget`, the
`maven-compiler-plugin`'s `release`, `source` and `target`) and the version of the `kotlin-maven-plugin`, each a
property of the same pom or a literal, its field the path in the pom with the plugin by its artifactId (`properties.java.version`,
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
JAVA_PROPERTIES = ("maven.compiler.release", "maven.compiler.source", "maven.compiler.target", "java.version",
                   "kotlin.compiler.jvmTarget")  # the last: the bytecode level kotlin-maven-plugin writes
COMPILER_FIELDS = ("release", "source", "target")
PLACEHOLDER = re.compile(r"^\$\{([^}]+)\}$")
GRADLE_PLUGIN = re.compile(r"""\bid\s*\(\s*['"]([^'"]+)['"]\s*\)|\bid\s+['"]([^'"]+)['"]""")
KOTLIN_PLUGIN = re.compile(r"""\bkotlin\s*\(\s*['"]([^'"]+)['"]\s*\)""")
GRADLE_COORD = re.compile(r"""['"]([A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+)(?::[^'"\s]+)?['"]""")
TOML_MODULE = re.compile(r"""module\s*=\s*['"]([^'"]+:[^'"]+)['"]""")
TOML_GROUP_NAME = re.compile(r"""group\s*=\s*['"]([^'"]+)['"].*?name\s*=\s*['"]([^'"]+)['"]""")
TOML_PLUGIN_ID = re.compile(r"""\bid\s*=\s*['"]([^'"]+)['"]""")


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


def _pom_packages(rel: str, text: str, own: set[str], packages: list[dict], seen: set) -> None:
    try:
        project = ET.fromstring(text)
    except ET.ParseError:
        return

    def add(group: str, artifact: str) -> None:
        if not artifact or "$" in artifact or "$" in group:
            return
        coord = f"{group}:{artifact}" if group else artifact
        if coord.casefold() in own or artifact.casefold() in own:
            return
        if (coord.casefold(), rel) not in seen:
            seen.add((coord.casefold(), rel))
            line = _line(text, f">{artifact}<")
            packages.append({"ecosystem": "maven", "name": coord, "declared_in": f"{rel}#L{line}" if line else rel})

    for node in project:
        if _local(node.tag) == "parent":
            fields = {_local(c.tag): (c.text or "").strip() for c in node}
            add(fields.get("groupId", ""), fields.get("artifactId", ""))
    for node in project.iter():
        tag = _local(node.tag)
        if tag in ("dependency", "plugin"):
            fields = {_local(c.tag): (c.text or "").strip() for c in node}
            group = fields.get("groupId", "org.apache.maven.plugins" if tag == "plugin" else "")
            add(group, fields.get("artifactId", ""))


def _gradle_packages(rel: str, text: str, packages: list[dict], seen: set) -> None:
    base = PurePosixPath(rel).name
    for number, line in enumerate(text.splitlines(), 1):
        code = line.split("//" if not base.endswith(".toml") else "#", 1)[0]
        if base.endswith(".toml"):
            for m in TOML_MODULE.finditer(code):
                coord = m.group(1)
                if (coord.casefold(), rel) not in seen:
                    seen.add((coord.casefold(), rel))
                    packages.append({"ecosystem": "maven", "name": coord, "declared_in": f"{rel}#L{number}"})
            for m in TOML_GROUP_NAME.finditer(code):
                coord = f"{m.group(1)}:{m.group(2)}"
                if (coord.casefold(), rel) not in seen:
                    seen.add((coord.casefold(), rel))
                    packages.append({"ecosystem": "maven", "name": coord, "declared_in": f"{rel}#L{number}"})
            for m in TOML_PLUGIN_ID.finditer(code):
                pid = m.group(1)
                if "." in pid and (pid.casefold(), rel) not in seen:
                    seen.add((pid.casefold(), rel))
                    packages.append({"ecosystem": "maven", "name": pid, "declared_in": f"{rel}#L{number}"})
            continue
        for m in GRADLE_PLUGIN.finditer(code):
            pid = m.group(1) or m.group(2)
            if pid and "." in pid and (pid.casefold(), rel) not in seen:
                seen.add((pid.casefold(), rel))
                packages.append({"ecosystem": "maven", "name": pid, "declared_in": f"{rel}#L{number}"})
        for m in KOTLIN_PLUGIN.finditer(code):
            kid = f"org.jetbrains.kotlin.{m.group(1)}"
            if (kid.casefold(), rel) not in seen:
                seen.add((kid.casefold(), rel))
                packages.append({"ecosystem": "maven", "name": kid, "declared_in": f"{rel}#L{number}"})
        for m in GRADLE_COORD.finditer(code):
            coord = m.group(1)
            if not coord.startswith(":") and "$" not in coord and (coord.casefold(), rel) not in seen:
                seen.add((coord.casefold(), rel))
                packages.append({"ecosystem": "maven", "name": coord, "declared_in": f"{rel}#L{number}"})


def run(context):
    graph = context.graph
    builds = {}
    own = set()
    for module in graph["modules"]:
        if module["provenance"] != "build":
            continue
        for ecosystem in module["ecosystems"]:
            if ecosystem in ("gradle", "maven"):
                builds.setdefault(module["members"][0]["path"], set()).add(ecosystem)
                own |= {a.casefold() for a in [module["name"], *module["aliases"]] if a}
    if not builds:
        return None
    units, toolchains, packages, gaps, seen_pkgs = [], [], [], [], set()
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
        base = PurePosixPath(rel).name
        if base == "pom.xml":
            text = context.inventory.text(rel)
            _pom(rel, text, toolchains, gaps)
            _pom_packages(rel, text, own, packages, seen_pkgs)
        elif base in ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts") or base.endswith(".versions.toml"):
            _gradle_packages(rel, context.inventory.text(rel), packages, seen_pkgs)
    facts = {"units": units, "toolchains": toolchains, **({"packages": packages} if packages else {})}
    return {"facts": facts, "gaps": gaps}
