"""Source: the language version a project file declares as data, read and never run.

`Package.swift`: the `// swift-tools-version:` line, which SwiftPM reads before it compiles the manifest and only as
the file's first line. An MSBuild project (`.csproj`) or `Directory.Build.props`: `TargetFramework`, each of
`TargetFrameworks`, and C#'s `LangVersion`, with `line`. A value naming an MSBuild property is a
`toolchain_undeclared` gap: only MSBuild's evaluation states it.
"""
from __future__ import annotations

from pathlib import PurePosixPath
import re
import xml.etree.ElementTree as ET

NAME, VERSION, RANK = "project-files", "daodan/premap/v1", "reader"
TOOLS_VERSION = re.compile(r"//\s*swift-tools-version\s*:\s*([0-9]+(?:\.[0-9]+)*)")
MSBUILD = {"TargetFramework": "dotnet", "TargetFrameworks": "dotnet", "LangVersion": "c#"}


def _line(text: str, needle: str) -> int | None:
    at = text.find(needle)
    return text.count("\n", 0, at) + 1 if at >= 0 else None


def _msbuild(rel: str, text: str, toolchains: list, gaps: list) -> None:
    try:
        project = ET.fromstring(text)
    except ET.ParseError:
        return  # an unreadable project file is the module graph's gap
    for node in project.iter():
        field = node.tag.rsplit("}", 1)[-1]
        if field not in MSBUILD or not (node.text or "").strip():
            continue
        value = node.text.strip()
        if "$(" in value:
            gaps.append({"kind": "toolchain_undeclared", "path": rel,
                         "detail": f"{field} is {value}: only MSBuild's evaluation states it"})
            continue
        for version in filter(None, (v.strip() for v in value.split(";"))):
            toolchains.append({"tool": MSBUILD[field], "version": version, "declared_in": f"{rel}#{field}",
                               "line": _line(text, f"<{field}")})


def run(context):
    toolchains, gaps = [], []
    for rel in context.inventory.files:
        name = PurePosixPath(rel).name
        if name == "Package.swift":
            first = context.inventory.text(rel).split("\n", 1)[0]
            declared = TOOLS_VERSION.match(first.strip())
            if declared:
                toolchains.append({"tool": "swift", "version": declared.group(1), "declared_in": rel, "line": 1})
        elif name.endswith(".csproj") or name == "Directory.Build.props":
            _msbuild(rel, context.inventory.text(rel), toolchains, gaps)
    if not toolchains and not gaps:
        return None
    return {"facts": {"toolchains": toolchains} if toolchains else {}, "gaps": gaps}
