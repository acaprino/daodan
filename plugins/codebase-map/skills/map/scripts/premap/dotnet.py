"""Source: MSBuild's own evaluation of each .NET project, `dotnet msbuild -getProperty -getItem`.

`commands` describes, for Daodan's container, with the network closed, one evaluation per project file
(`.csproj`, `.fsproj`, `.vbproj`) with the .NET SDK Daodan carries: MSBuild imports `Directory.Build.props`,
`Directory.Build.targets`, `Directory.Packages.props` and the SDK, expands every property, and prints as JSON the
properties and items asked, without a restore or a build. Evaluating runs the project's MSBuild logic (property
functions, imports). `read` turns each project into a `dotnet-project` unit named by its `AssemblyName`, rooted at
its folder, with the project file as manifest, the projects its `ProjectReference` items reach as edges (also
through a property only the evaluation expands), its `Compile` items' folders as source roots, and its
`OutputType` and target frameworks in `config`. An evaluation that failed is a `model_failed` gap.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "dotnet", "10.0.404", "model"  # the .NET SDK Daodan carries
DOWNLOAD = (("https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.404/dotnet-sdk-10.0.404-linux-x64.tar.gz",
             "577d0eb17fec33d029104c5c63a1ab0accc3e28776274abef2218dbac5af18d2109b5406d26b31d76f5c245215e3ba0926a94c20"
             "246c672c41847c9e1eb1dc50"),)  # sha512, as Microsoft publishes it
PROJECTS = (".csproj", ".fsproj", ".vbproj")
PROPERTIES = ("AssemblyName", "OutputType", "TargetFramework", "TargetFrameworks")
ITEMS = ("ProjectReference", "Compile")
ENV = {"DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
       "DOTNET_SYSTEM_GLOBALIZATION_INVARIANT": "1", "DOTNET_CLI_HOME": "/tmp/daodan-dotnet",
       "MSBUILDDISABLENODEREUSE": "1"}


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def commands(context):
    projects = sorted((rel for rel in context.inventory.files if PurePosixPath(rel).suffix.lower() in PROJECTS),
                      key=lambda r: (r.count("/"), r))
    return [{"tool": "dotnet", "argv": ["dotnet", "msbuild", PurePosixPath(rel).name, "-nologo",
                                        *(f"-getProperty:{p}" for p in PROPERTIES), *(f"-getItem:{i}" for i in ITEMS)],
             "cwd": _folder(rel), "env": ENV, "network": "none"} for rel in projects] or None


def read(context, commands, results):
    root = next((r["root"] for r in results if r.get("root")), "/")
    evaluated, gaps = {}, []

    def rel(path: str) -> str | None:
        value = posixpath.relpath(posixpath.normpath(path.replace("\\", "/")), root)
        return None if value.startswith("..") else value

    for command, result in zip(commands, results):
        manifest = posixpath.join(command["cwd"], command["argv"][2]).removeprefix("./")
        text = (result["stdout"] or "").strip()
        if result["returncode"] != 0 or not text.startswith("{"):
            gaps.append({"kind": "model_failed", "path": manifest,
                         "detail": f"dotnet msbuild: {(text or result['stderr'] or '').strip()[-300:]}"})
            continue
        evaluated[manifest] = json.loads(text)
    names = {m: (e["Properties"].get("AssemblyName") or PurePosixPath(m).stem) for m, e in evaluated.items()}
    units = []
    for manifest, data in evaluated.items():
        properties, items = data["Properties"], data.get("Items", {})
        sources = {p for item in items.get("Compile", []) for p in [rel(item["FullPath"])] if p}
        edges = {names[p] for item in items.get("ProjectReference", []) for p in [rel(item["FullPath"])]
                 if p in names}
        frameworks = [f for f in (properties.get("TargetFrameworks") or properties.get("TargetFramework") or
                                  "").split(";") if f]
        config = {key: value for key, value in (("type", properties.get("OutputType")),
                                                ("target_frameworks", frameworks)) if value}
        units.append({"name": names[manifest], "kind": "dotnet-project", "root": _folder(manifest),
                      "manifest": manifest, "source_roots": sorted({_folder(s) for s in sources}),
                      "depends_on": sorted(edges), "config": config})
    return {"facts": {"units": units} if units else {}, "gaps": gaps}
