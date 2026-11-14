""".NET: the solution and projects as the dotnet CLI reports them.

At each solution (*.sln, *.slnx), or at each project file when there is none: `dotnet sln list` (member
projects), `dotnet list <project> reference` (project references), `dotnet list <solution> package --format
json` (top-level packages per project and framework, requested and resolved; it restores first, which
evaluates MSBuild and may run targets), and `dotnet --version` in the solution directory (the SDK that
global.json selects).
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = ".NET SDK 8.0.404"
VERSION_COMMAND = ["dotnet", "--version"]
TRIGGERS = ("*.sln", "*.slnx", "*.csproj", "*.fsproj", "*.vbproj")
COMMAND = ("dotnet sln list; dotnet list <project> reference; dotnet restore; "
           "dotnet list <solution> package --format json")
ENV = {"DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1"}


def _dotnet(args, cwd, name):
    return common.run(["dotnet", *args], cwd, name=name, env=ENV)


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    found = common.find(root, set(TRIGGERS))
    solutions = [f for f in found if f.endswith((".sln", ".slnx"))]
    projects_all = [f for f in found if not f.endswith((".sln", ".slnx"))]
    units, workspaces, dependencies, errors, raw = [], [], [], [], {}
    groups = []  # (directory, entry file, [project rel paths])
    for solution in solutions:
        here = root / common.parent(solution)
        done = _dotnet(["sln", Path(solution).name, "list"], here, "dotnet sln list")
        members = [common.rel(here / line.strip().replace("\\", "/"), root) for line in done.stdout.splitlines()
                   if line.strip().endswith(("proj",))]
        if done.returncode != 0:
            errors.append(f"{solution}: dotnet sln list: {common.error_of(done)}")
        groups.append((common.parent(solution), solution, members))
        workspaces.append({"tool": "dotnet", "root": common.parent(solution),
                           "members": [common.parent(m) for m in members]})
    listed = {m for _, _, members in groups for m in members}
    groups += [(common.parent(p), p, [p]) for p in projects_all if p not in listed and not solutions]
    for directory, entry, members in groups:
        here = root / directory
        version = _dotnet(["--version"], here, "dotnet --version")
        raw.setdefault("sdk selected", {})[directory] = version.stdout.strip() or common.error_of(version)
        restore = _dotnet(["restore", Path(entry).name], here, "dotnet restore")  # SDK 8 lists nothing without it
        if restore.returncode != 0:
            errors.append(f"{entry}: dotnet restore: {common.error_of(restore)}")
        packages = _dotnet(["list", Path(entry).name, "package", "--format", "json"], here,
                           "dotnet list package --format json")
        data = common.json_or_none(packages.stdout)
        if packages.returncode != 0 or not isinstance(data, dict):
            errors.append(f"{entry}: dotnet list package: {common.error_of(packages)}")
            data = {}
        by_path = {common.rel(p["path"], root): p for p in data.get("projects") or [] if p.get("path")}
        names = {Path(m).stem for m in members}
        for member in members:
            name = Path(member).stem
            refs = _dotnet(["list", str(root / member), "reference"], here, "dotnet list reference")
            depends = sorted(Path(line.strip().replace("\\", "/")).stem for line in refs.stdout.splitlines()
                             if line.strip().endswith("proj"))
            if refs.returncode != 0:
                errors.append(f"{member}: dotnet list reference: {common.error_of(refs)}")
            project = by_path.get(member) or {}
            frameworks = [f.get("framework") for f in project.get("frameworks") or []]
            unit = {"name": name, "kind": "dotnet-project", "root": common.parent(member), "manifest": member,
                    "depends_on": [d for d in depends if d in names] or depends}
            if frameworks:
                unit["config"] = {"target_frameworks": frameworks}
            units.append(unit)
            seen = set()
            for framework in project.get("frameworks") or []:
                for package in framework.get("topLevelPackages") or []:
                    if package["id"] in seen:
                        continue
                    seen.add(package["id"])
                    dependencies.append({"unit": name, "name": package["id"],
                                         "declared": package.get("requestedVersion"),
                                         "resolved": package.get("resolvedVersion"), "scope": "runtime",
                                         "declared_in": member})
    common.NOTES.update(errors=errors, raw=raw)
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "dependencies": dependencies}
