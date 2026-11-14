"""Go: the module model as the go command reports it.

Commands, in each directory that holds a go.work, then in each go.mod no workspace lists (GOWORK=off):
`go work edit -json`, `go list -m -json` (main modules), `go mod edit -json` (requirements as written),
`go list -m -json all` (the build list: resolved versions), `go list -e -json ./...` (packages).
Finding the go.mod and go.work files is a walk by file name; everything else is the go command's answer.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "go1.27.3"
VERSION_COMMAND = ["go", "version"]
TRIGGERS = ("go.mod", "go.work")
COMMAND = "go work edit -json; go list -m -json; go mod edit -json; go list -m -json all; go list -e -json ./..."


def _go(args, cwd, name, gowork_off=False):
    return common.run(["go", *args], cwd, name=name, env={"GOWORK": "off"} if gowork_off else None)


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    works = common.find(root, {"go.work"}, skip_underscore=True)
    mods = common.find(root, {"go.mod"}, skip_underscore=True)
    units, workspaces, toolchains, dependencies, errors, raw = [], [], [], [], [], {}
    covered: set[str] = set()  # module directories a go.work lists
    sessions = []  # (directory, gowork_off)
    for work in works:
        directory = common.parent(work)
        done = _go(["work", "edit", "-json"], root / directory, "go work edit -json")
        data = common.json_or_none(done.stdout) if done.returncode == 0 else None
        if data is None:
            errors.append(f"{work}: {common.error_of(done)}")
            continue
        members = [common.rel(root / directory / use["DiskPath"], root) for use in data.get("Use") or []]
        covered.update(members)
        workspaces.append({"tool": "go", "root": directory, "members": members})
        if data.get("Go"):
            toolchains.append({"tool": "go", "version": data["Go"], "declared_in": work})
        if data.get("Toolchain"):
            toolchains.append({"tool": "go", "version": data["Toolchain"], "declared_in": work})
        sessions.append((directory, False))
    for mod in mods:
        directory = common.parent(mod)
        if directory not in covered:
            sessions.append((directory, True))
    main_paths: dict[str, str] = {}  # module path -> directory
    per_module: list[tuple[str, dict, bool, str]] = []
    for directory, off in sessions:
        done = _go(["list", "-m", "-json"], root / directory, "go list -m -json", off)
        mains = [m for m in common.json_stream(done.stdout) if isinstance(m, dict)]
        if done.returncode != 0 or not mains:
            errors.append(f"{directory}: go list -m -json: {common.error_of(done)}")
            continue
        build = _go(["list", "-m", "-json", "all"], root / directory, "go list -m -json all", off)
        resolved = {m["Path"]: m.get("Version") for m in common.json_stream(build.stdout)
                    if isinstance(m, dict) and not m.get("Main")}
        if build.returncode != 0:
            errors.append(f"{directory}: go list -m -json all: {common.error_of(build)}")
            resolved = None
        for module in mains:
            if not module.get("Dir"):
                continue
            mod_dir = common.rel(module["Dir"], root)
            main_paths[module["Path"]] = mod_dir
            per_module.append((mod_dir, module, off, resolved))
    seen = set()
    for mod_dir, module, off, resolved in per_module:
        if mod_dir in seen:
            continue
        seen.add(mod_dir)
        edit = _go(["mod", "edit", "-json"], root / mod_dir, "go mod edit -json", True)
        written = common.json_or_none(edit.stdout) or {}
        listing = _go(["list", "-e", "-json", "./..."], root / mod_dir, "go list -e -json ./...", off)
        packages = [p for p in common.json_stream(listing.stdout) if isinstance(p, dict)]
        if listing.returncode != 0:
            errors.append(f"{mod_dir}: go list ./...: {common.error_of(listing)}")
        manifest = common.rel(module.get("GoMod") or root / mod_dir / "go.mod", root)
        config: dict = {"packages": sorted(p["ImportPath"] for p in packages if p.get("ImportPath"))}
        mains_ = sorted(p["ImportPath"] for p in packages if p.get("Name") == "main")
        if mains_:
            config["main_packages"] = mains_
        tests = sorted({p["ImportPath"] for p in packages if p.get("TestGoFiles")}
                       | {p["ImportPath"] + "_test" for p in packages if p.get("XTestGoFiles")})
        if tests:
            config["test_packages"] = tests
        ignored = sorted(common.rel(Path(p["Dir"]) / f, root) for p in packages for f in p.get("IgnoredGoFiles") or [])
        if ignored:
            config["ignored_files"] = ignored
        for p in packages:
            if p.get("CgoFiles"):
                config["cgo"] = {"package": p["ImportPath"],
                                 "go_files": [common.rel(Path(p["Dir"]) / f, root) for f in p["CgoFiles"]],
                                 "c_files": [common.rel(Path(p["Dir"]) / f, root) for f in p.get("CFiles") or []],
                                 "headers": [common.rel(Path(p["Dir"]) / f, root) for f in p.get("HFiles") or []],
                                 "cflags": p.get("CgoCFLAGS") or [], "ldflags": p.get("CgoLDFLAGS") or []}
        if written.get("Replace"):
            config["replace"] = {r["Old"]["Path"]: r["New"]["Path"] + (f"@{r['New']['Version']}" if r["New"].get("Version") else "")
                                 for r in written["Replace"]}
        if written.get("Toolchain"):
            config["toolchain"] = written["Toolchain"]
        broken = [p["ImportPath"] for p in packages if p.get("Error")]
        if broken:
            raw.setdefault("package_errors", {})[mod_dir] = [f"{p['ImportPath']}: {p['Error'].get('Err', '')[:160]}"
                                                            for p in packages if p.get("Error")][:5]
        depends = []
        for req in written.get("Require") or []:
            if req["Path"] in main_paths:
                depends.append(req["Path"])
                continue
            if req.get("Indirect"):
                continue
            item = {"unit": module["Path"], "name": req["Path"], "declared": req.get("Version"),
                    "scope": "runtime", "declared_in": manifest}
            if resolved is not None:
                item["resolved"] = resolved.get(req["Path"])
            dependencies.append(item)
        for rep in written.get("Replace") or []:
            if rep["Old"]["Path"] in main_paths and rep["Old"]["Path"] not in depends:
                depends.append(rep["Old"]["Path"])
        for tool in written.get("Tool") or []:
            dependencies.append({"unit": module["Path"], "name": tool["Path"], "scope": "dev", "declared_in": manifest})
        units.append({"name": module["Path"], "kind": "go-module", "root": mod_dir, "manifest": manifest,
                      "source_roots": [mod_dir], "depends_on": sorted(set(depends)), "config": config})
        if module.get("GoVersion"):
            toolchains.append({"tool": "go", "version": module["GoVersion"], "declared_in": manifest})
        if written.get("Toolchain"):
            toolchains.append({"tool": "go", "version": written["Toolchain"], "declared_in": manifest})
    reached = {u["root"] for u in units}
    raw["go.mod not reached by a go command from its own directory"] = [m for m in mods if common.parent(m) not in reached]
    out = {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
           "toolchains": toolchains, "dependencies": dependencies}
    common.NOTES.update(errors=errors, raw=raw)
    return out
