"""Source: CMake's own model of the build, the file API's codemodel-v2, after a configure of each top CMake folder.

`commands` describes, for Daodan's container, with the network closed, a configure into a build folder outside the
copy, with a codemodel-v2 query: of each CMakeLists.txt that no other one's folder holds, of each one below them
that calls `project()` (a project of its own, which the top may never add), and, where a CMakePresets.json sits
beside it, of each configure preset it names (not hidden). Configuring runs the project's CMake scripts. The
command prints the reply files, each after a record separator line naming it. `read` turns each target CMake
reports, interface libraries included (not `UTILITY` or imported ones), into a `cmake-target` unit named by the
target: its folder, the CMakeLists.txt of that folder, the folders of its sources, the targets it links as
edges, its type, sources, include folders, compile definitions and the presets that define it; a folder an
outer configure reached keeps that configure's targets. `cmake_minimum_required` is a toolchain. A configure
that failed is a `model_failed` gap; a CMakeLists.txt no configure reached, `model_partial`.
"""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import PurePosixPath

from premap import meson

NAME, VERSION, RANK = "cmake", "4.4.5", "model"  # its codemodel (2.11) lists interface libraries too
DOWNLOAD = (("https://github.com/Kitware/CMake/releases/download/v4.4.5/cmake-4.4.5-linux-x86_64.tar.gz",
             "ed85135c5a5135b45e50423cb406dea04ca3338da0b8ef3c9ede963559680be0"),
            meson.DOWNLOAD[1])  # what the runner carries: CMake, and Ninja, the generator a preset may name
FILE = "CMakeLists.txt"
LINKS = ("dependencies", "linkLibraries", "compileDependencies")  # a target's edges to the others
SEPARATOR = "\x1e"  # starts the line naming each reply file in the command's output
SCRIPT = ('b=$(mktemp -d) && q="$b/.cmake/api/v1" && mkdir -p "$q/query" && : > "$q/query/codemodel-v2"'
          ' && cmake -S . -B "$b" ${1:+--preset "$1"} >&2 && cd "$q/reply"'
          ' && for f in *.json; do printf "\\036%s\\n" "$f"; cat "$f"; done')  # $1: the preset, or empty
PROJECT = re.compile(r"(?im)^[ \t]*project[ \t]*\(")  # the call that makes a CMakeLists.txt a project's top
PRESETS = "CMakePresets.json"


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def _presets(context, top: str) -> list[str]:
    rel = posixpath.join(top, PRESETS).removeprefix("./")
    if rel not in context.inventory.headers:
        return []
    data = json.loads(context.inventory.text(rel))
    return [p["name"] for p in data.get("configurePresets", []) if not p.get("hidden")]


def commands(context):
    lists = sorted({_folder(rel) for rel in context.inventory.files if PurePosixPath(rel).name == FILE},
                   key=lambda f: (f.count("/"), f))
    tops = [f for f in lists if not any(o != f and _inside(f, o) for o in lists)]
    tops += [f for f in lists if f not in tops
             and PROJECT.search(context.inventory.text(posixpath.join(f, FILE).removeprefix("./")))]
    return [{"tool": "cmake", "argv": ["sh", "-c", SCRIPT, "cmake", preset], "cwd": top, "env": {},
             "network": "none"} for top in tops for preset in ["", *_presets(context, top)]] or None


def replies(stdout: str) -> dict[str, dict]:
    """The reply files the command printed, by name."""
    out = {}
    for record in stdout.split(SEPARATOR)[1:]:
        name, _, text = record.partition("\n")
        out[name.strip()] = json.loads(text)
    return out


def read(context, commands, results):
    root = next((r["root"] for r in results if r.get("root")), "/")
    units: dict[tuple, dict] = {}
    toolchains, gaps, reached, version = [], [], {}, None  # reached: folder -> the configure that reached it first

    def rel(path: str, base: str) -> str | None:
        full = posixpath.normpath(path if posixpath.isabs(path) else posixpath.join(root, base, path))
        value = posixpath.relpath(full, root)
        return None if value.startswith("..") else "." if value == "." else value

    for command, result in zip(commands, results):
        top, preset = command["cwd"], command["argv"][-1]
        files = replies(result["stdout"]) if result["returncode"] == 0 else {}
        index = next((files[n] for n in sorted(files) if n.startswith("index-")), None)
        entry = next((o for o in (index or {}).get("objects", []) if o.get("kind") == "codemodel"), None)
        if entry is None:
            gaps.append({"kind": "model_failed", "path": top, **({"preset": preset} if preset else {}),
                         "detail": f"cmake configure: {(result['stderr'] or '').strip()[-300:]}"})
            continue
        version = version or index.get("cmake", {}).get("version", {}).get("string")
        configuration = files[entry["jsonFile"]]["configurations"][0]
        directories = configuration["directories"]
        folders = [rel(d["source"], top) for d in directories]
        for folder, directory in zip(folders, directories):
            reached.setdefault(folder, top)
            minimum = (directory.get("minimumCMakeVersion") or {}).get("string")
            toolchain = {"tool": "cmake", "version": minimum,
                         "declared_in": posixpath.join(folder, FILE).removeprefix("./") + "#cmake_minimum_required"}
            if minimum and directory["source"] == "." and toolchain not in toolchains:
                toolchains.append(toolchain)
        refs = [r for r in configuration["targets"] + configuration.get("abstractTargets", [])
                if files[r["jsonFile"]]["type"] != "UTILITY" and not files[r["jsonFile"]].get("imported")]
        names = {r["id"]: r["name"] for r in refs}
        for ref in refs:
            target, folder = files[ref["jsonFile"]], folders[ref["directoryIndex"]]
            if reached[folder] != top:  # an outer configure holds this folder
                continue
            sources = sorted({p for s in target.get("sources", []) if not s.get("isGenerated")
                              for p in [rel(s["path"], top)] if p})
            groups = target.get("compileGroups", [])
            config = {"type": target["type"], "sources": sources}
            includes = sorted({p for g in groups for i in g.get("includes", []) for p in [rel(i["path"], top)] if p})
            defines = sorted({d["define"] for g in groups for d in g.get("defines", [])})
            if includes:
                config["include_dirs"] = includes
            if defines:
                config["build_tags"] = defines
            unit = units.setdefault((folder, target["name"]), {
                "name": target["name"], "kind": "cmake-target", "root": folder,
                "manifest": posixpath.join(folder, FILE).removeprefix("./"),
                "source_roots": sorted({_folder(s) for s in sources}),
                "depends_on": sorted({names[d["id"]] for key in LINKS for d in target.get(key, [])
                                      if d["id"] in names and d["id"] != ref["id"]}),
                "config": config})
            if preset:
                unit["config"].setdefault("presets", []).append(preset)
    failed = {g["path"] for g in gaps}
    if reached:
        for rel_path in sorted(rel for rel in context.inventory.files if PurePosixPath(rel).name == FILE):
            if _folder(rel_path) not in reached and _folder(rel_path) not in failed:
                gaps.append({"kind": "model_partial", "path": rel_path,
                             "detail": "no configure reached this CMakeLists.txt: its targets are unknown"})
    facts = {"units": list(units.values()), "toolchains": toolchains} if units or toolchains else {}
    return {"facts": facts, "gaps": gaps, **({"version": version} if version else {})}
