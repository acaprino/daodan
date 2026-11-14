"""CMake: targets as CMake's file API (codemodel-v2) reports them after a configure, plus the presets.

At the top-most CMakeLists.txt: `cmake --list-presets` when a CMakePresets.json sits there (read only), then
a configure into a build directory outside the project (`cmake -S <project> -B <work>/build`, one per
configure preset when there are presets, the plain configure otherwise) with a codemodel-v2 query. Configuring
runs the CMakeLists.txt scripts and probes the compilers: project code by construction.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import native_common as common

VERSION = "CMake 3.28 (Ubuntu 24.04)"
VERSION_COMMAND = ["cmake", "--version"]
TRIGGERS = ("CMakeLists.txt",)
COMMAND = "cmake --list-presets; cmake -S . -B <work>/build (file API codemodel-v2)"


def _reply(build: Path) -> dict | None:
    reply = build / ".cmake/api/v1/reply"
    index = sorted(reply.glob("index-*.json"))
    if not index:
        return None
    data = json.loads(index[-1].read_text(encoding="utf-8"))
    entry = next((r for r in data.get("objects", []) if r.get("kind") == "codemodel"), None)
    if not entry:
        return None
    model = json.loads((reply / entry["jsonFile"]).read_text(encoding="utf-8"))
    model["_reply"], model["_cmake"] = reply, data.get("cmake", {}).get("version", {}).get("string")
    return model


def _configure(project: Path, build: Path, preset: str | None):
    query = build / ".cmake/api/v1/query/codemodel-v2"
    query.parent.mkdir(parents=True, exist_ok=True)
    query.touch()
    args = ["cmake", "-S", str(project), "-B", str(build)]
    if preset:
        args += ["--preset", preset]
    return common.run(args, project, name="cmake configure" + (f" --preset {preset}" if preset else ""))


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir), Path(work_dir)
    lists = common.find(root, {"CMakeLists.txt"})
    if "CMakeLists.txt" in lists:
        tops = ["."]
    else:
        tops = [common.parent(p) for p in lists
                if not any(common.parent(p).startswith(common.parent(q) + "/") for q in lists if q != p)]
    units, toolchains, errors, raw = {}, [], [], {}
    for n, top in enumerate(tops):
        project = root / top
        presets = []
        if (project / "CMakePresets.json").is_file():
            listed = common.run(["cmake", "--list-presets"], project, name="cmake --list-presets")
            presets = re.findall(r'^\s+"([^"]+)"', listed.stdout, re.M)
            raw.setdefault("presets", {})[top] = presets or common.error_of(listed)
        for preset in presets or [None]:
            build = work / f"build-{n}-{preset or 'default'}"
            done = _configure(project, build, preset)
            model = _reply(build) if build.is_dir() else None
            if done.returncode != 0 or model is None:
                errors.append(f"{top} {preset or ''}: {common.error_of(done)}")
                if model is None:
                    continue
            configuration = model["configurations"][0]
            directories = configuration["directories"]
            projects = configuration["projects"]
            for directory in directories:
                minimum = (directory.get("minimumCMakeVersion") or {}).get("string")
                if minimum and directory.get("source") == ".":
                    toolchains.append({"tool": "cmake", "version": minimum,
                                       "declared_in": common.join(top, "CMakeLists.txt")})
            ids = {t["id"]: t["name"] for t in configuration["targets"]}
            for ref in configuration["targets"]:
                target = json.loads((model["_reply"] / ref["jsonFile"]).read_text(encoding="utf-8"))
                if target["type"] == "UTILITY":
                    continue
                source_dir = target["paths"]["source"]
                unit_root = common.rel(project / source_dir, root)
                key = (unit_root, target["name"])
                sources = [common.rel(project / s["path"], root) for s in target.get("sources", [])
                           if not s.get("isGenerated") and not s["path"].startswith("/")]
                config = {"project": projects[ref.get("projectIndex", 0)]["name"], "type": target["type"],
                          "sources": sorted(sources)}
                includes, defines = [], []
                for group in target.get("compileGroups", []):
                    language = group.get("language", "").lower()
                    standard = (group.get("languageStandard") or {}).get("standard")
                    if standard:
                        config["cxx_standard" if language == "cxx" else f"{language}_standard"] = standard
                    includes += [common.rel(i["path"], root) for i in group.get("includes", [])]
                    defines += [d["define"] for d in group.get("defines", [])]
                if includes:
                    config["include_directories"] = sorted(set(includes))
                if defines:
                    config["compile_definitions"] = sorted(set(defines))
                if target.get("nameOnDisk"):
                    config["artifact"] = target["nameOnDisk"]
                unit = units.setdefault(key, {
                    "name": target["name"], "kind": "cmake-target", "root": unit_root,
                    "manifest": common.join(unit_root, "CMakeLists.txt"),
                    "source_roots": sorted({common.parent(s) for s in sources}),
                    "depends_on": sorted({ids[d["id"]] for d in target.get("dependencies", []) if d["id"] in ids}),
                    "config": config})
                if preset:
                    unit["config"].setdefault("presets", []).append(preset)
    common.NOTES.update(errors=errors, raw=raw)
    return {"units": list(units.values()), "toolchains": toolchains}
