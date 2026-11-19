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

from build_units import msbuild_version

NAME, VERSION, RANK = "project-files", "daodan/premap/v2", "reader"
TOOLS_VERSION = re.compile(r"//\s*swift-tools-version\s*:\s*([0-9]+(?:\.[0-9]+)*)")
# The framework a project targets is `dotnet-target`: `dotnet` is the SDK that builds it (`global.json`).
MSBUILD = {"TargetFramework": "dotnet-target", "TargetFrameworks": "dotnet-target", "LangVersion": "c#"}
SDK_PACKAGES = {
    "microsoft.net.sdk.web": "Microsoft.AspNetCore.App",
    "microsoft.net.sdk.blazorwebassembly": "Microsoft.AspNetCore.Components.WebAssembly",
    "aspire.apphost.sdk": "Aspire.Hosting",
}


def _line(text: str, needle: str) -> int | None:
    at = text.find(needle)
    return text.count("\n", 0, at) + 1 if at >= 0 else None


def _central(text: str) -> dict[str, str]:
    """A `Directory.Packages.props`' `PackageVersion`s: name (casefolded) -> version."""
    try:
        project = ET.fromstring(text)
    except ET.ParseError:
        return {}
    return {(node.attrib.get("Include") or node.attrib.get("Update") or "").strip().casefold(): version
            for node in project.iter() if node.tag.rsplit("}", 1)[-1] == "PackageVersion"
            for version in [msbuild_version(node)] if version}


def _nearest(rel: str, centrals: dict[str, dict]) -> dict[str, str]:
    """The versions of the `Directory.Packages.props` MSBuild imports for `rel`: the first in its folder or above."""
    folder = PurePosixPath(rel).parent
    while folder.as_posix() not in centrals and folder.as_posix() != ".":
        folder = folder.parent
    return centrals.get(folder.as_posix(), {})


def _msbuild(rel: str, text: str, toolchains: list, packages: list, seen: set, gaps: list,
             central: dict[str, str]) -> None:
    try:
        project = ET.fromstring(text)
    except ET.ParseError:
        return  # an unreadable project file is the module graph's gap

    def add_pkg(name: str, needle: str, version: str | None = None) -> None:
        if not name or "$(" in name or (name.casefold(), rel) in seen:
            return
        seen.add((name.casefold(), rel))
        line = _line(text, needle)
        packages.append({"ecosystem": "nuget", "name": name, "declared_in": f"{rel}#L{line}" if line else rel,
                         **({"version": version} if version else {})})

    for sdk in filter(None, (s.strip().split("/", 1)[0] for s in (project.attrib.get("Sdk") or "").split(";"))):
        if sdk.lower() in SDK_PACKAGES:
            add_pkg(SDK_PACKAGES[sdk.lower()], sdk)
    for node in project.iter():
        field = node.tag.rsplit("}", 1)[-1]
        if field == "Sdk" and node.attrib.get("Name", "").split("/", 1)[0].lower() in SDK_PACKAGES:
            sdk_name = node.attrib["Name"].split("/", 1)[0]
            add_pkg(SDK_PACKAGES[sdk_name.lower()], sdk_name)
        elif field in ("PackageReference", "PackageVersion", "FrameworkReference"):
            pkg = (node.attrib.get("Include") or node.attrib.get("Update") or "").strip()
            # a `PackageReference` without its own version takes the central one (central package management)
            add_pkg(pkg, pkg, msbuild_version(node) or (central.get(pkg.casefold()) if field == "PackageReference"
                                                        else None))
        elif field == "UseMaui" and (node.text or "").strip().lower() == "true":
            add_pkg("Microsoft.Maui.Controls", "<UseMaui")
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
    toolchains, packages, gaps, seen = [], [], [], set()
    centrals = {PurePosixPath(rel).parent.as_posix(): _central(context.inventory.text(rel))
                for rel in context.inventory.files if PurePosixPath(rel).name == "Directory.Packages.props"}
    for rel in context.inventory.files:
        name = PurePosixPath(rel).name
        if name == "Package.swift":
            first = context.inventory.text(rel).split("\n", 1)[0]
            declared = TOOLS_VERSION.match(first.strip())
            if declared:
                toolchains.append({"tool": "swift", "version": declared.group(1), "declared_in": rel, "line": 1})
        elif name.endswith((".csproj", ".fsproj", ".vbproj")) or name in ("Directory.Build.props", "Directory.Packages.props"):
            _msbuild(rel, context.inventory.text(rel), toolchains, packages, seen, gaps, _nearest(rel, centrals))
    if not toolchains and not packages and not gaps:
        return None
    facts = {**({"toolchains": toolchains} if toolchains else {}),
             **({"packages": packages} if packages else {})}
    return {"facts": facts, "gaps": gaps}
