"""Source: CMake's own model of the build, the file API's codemodel-v2, after a configure of each top CMake folder.

`commands` describes, for Daodan's container, with the network closed, a configure into a build folder outside the
copy, with a codemodel-v2 query: of each CMakeLists.txt that no other one's folder holds, of each one below them
that calls `project()` (a project of its own, which the top may never add), and, where a CMakePresets.json sits
beside it, of each configure preset it names (not hidden). Configuring runs the project's CMake scripts. The
command prints the reply files, each after a record separator line naming it. `read` turns each target CMake
reports, interface libraries included (not `UTILITY` or imported ones), into a `cmake-target` unit named by the
target: its folder, the CMakeLists.txt of that folder, the folders of its sources, the targets it links as
edges, its type, sources, include folders, compile definitions and the presets that define it; a folder an
outer configure reached keeps that configure's targets. `cmake_minimum_required` is a toolchain. The folders a
configure reached are `covers`: a reader's `cmake-target` there that names no target CMake reports is dropped. A
configure that failed is a `model_failed` gap; a CMakeLists.txt no configure reached, `model_partial`.

What a configure needs comes first, as the CI of such a project does it, in the preparation with the registries
open (`preparation.NEEDS`): where a top folder declares vcpkg (vcpkg.json) `vcpkg install` in manifest mode with
the baseline it names, else where it declares Conan (conanfile.txt, conanfile.py) `conan install`, its conan.lock
honoured, building only what has no binary; each writes an initial cache (`-C`) naming its toolchain file, which
every configure of that folder reads. Both declared: the one a preset's `CMAKE_TOOLCHAIN_FILE` names, else vcpkg,
with a `choice` gap; an install that fails is a `restore_failed` gap naming the manager and its error, and the
configures run without it. A preset's toolchain file whose `CMAKE_<LANG>_COMPILER` is in `preparation.COMPILERS` brings
that compiler onto the path; any other stays the configure's gap, which names it.
"""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import PurePosixPath

import preparation
from premap import meson

NAME, VERSION, RANK = "cmake", "4.4.5", "model"  # its codemodel (2.11) lists interface libraries too
DOWNLOAD = (("https://github.com/Kitware/CMake/releases/download/v4.4.5/cmake-4.4.5-linux-x86_64.tar.gz",
             "ed85135c5a5135b45e50423cb406dea04ca3338da0b8ef3c9ede963559680be0"),
            meson.DOWNLOAD[1])  # what the runner carries: CMake, and Ninja, the generator a preset may name
FILE = "CMakeLists.txt"
LINKS = ("dependencies", "linkLibraries", "compileDependencies")  # a target's edges to the others
SEPARATOR = "\x1e"  # starts the line naming each reply file in the command's output
PREP = preparation.STATE + "/prep"  # per top folder, what its preparation wrote: `init.cmake`
SCRIPT = ('b=$(mktemp -d) && q="$b/.cmake/api/v1" && mkdir -p "$q/query" && : > "$q/query/codemodel-v2"'
          f' && i="{PREP}/$2/init.cmake" && if [ -f "$i" ]; then set -- "$1" -C "$i"; else set -- "$1"; fi'
          ' && p="$1" && shift && cmake "$@" -S . -B "$b" ${p:+--preset "$p"} >&2 && cd "$q/reply"'
          ' && for f in *.json; do printf "\\036%s\\n" "$f"; cat "$f"; done')  # $1: the preset or empty, $2: key
VCPKG = (f'vcpkg install --x-manifest-root=. --x-install-root="{PREP}/$1/vcpkg_installed" --triplet=x64-linux'
         ' >&2 && printf \'%s\\n\''
         ' "set(CMAKE_TOOLCHAIN_FILE \\"$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake\\" CACHE FILEPATH \\"\\")"'
         ' "set(VCPKG_MANIFEST_INSTALL OFF CACHE BOOL \\"\\")"'
         ' "set(VCPKG_TARGET_TRIPLET x64-linux CACHE STRING \\"\\")"'
         f' "set(VCPKG_INSTALLED_DIR \\"{PREP}/$1/vcpkg_installed\\" CACHE PATH \\"\\")" > "{PREP}/$1/init.cmake"')
CONAN = (f'conan profile detect --force >&2 && conan install . $([ -f conan.lock ] && echo --lockfile=conan.lock)'
         f' --output-folder="{PREP}/$1/conan" --build=missing -s build_type=Release'
         ' -c tools.cmake.cmaketoolchain:user_presets="" >&2'  # nothing written into the project
         f' && t=$(find "{PREP}/$1/conan" -name conan_toolchain.cmake | head -n 1) && [ -n "$t" ]'
         ' && printf \'%s\n\' "set(CMAKE_TOOLCHAIN_FILE \\"$t\\" CACHE FILEPATH \\"\\")"'
         f' "set(CMAKE_BUILD_TYPE Release CACHE STRING \\"\\")" > "{PREP}/$1/init.cmake"')  # the type it installed
MANAGERS = (("vcpkg", ("vcpkg.json",), VCPKG), ("conan", ("conanfile.txt", "conanfile.py"), CONAN))
COMPILER = re.compile(r"(?i)set\s*\(\s*CMAKE_(?:C|CXX)_COMPILER\s+\"?([^\s\")]+)")
PROJECT = re.compile(r"(?im)^[ \t]*project[ \t]*\(")  # the call that makes a CMakeLists.txt a project's top
PRESETS = "CMakePresets.json"
STANDARDS = {"C": "c", "CXX": "c++"}  # a compile group's language, as a toolchain


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def _error(stderr: str | None) -> str:
    """CMake's first error, from its `CMake Error` line on, whitespace folded; else the output's tail."""
    text = stderr or ""
    start = text.find("CMake Error")
    return " ".join((text[start:] if start >= 0 else text[-300:]).split())[:400]


def _preset_data(context, top: str) -> dict:
    rel = posixpath.join(top, PRESETS).removeprefix("./")
    return json.loads(context.inventory.text(rel)) if rel in context.inventory.headers else {}


def _presets(context, top: str) -> list[str]:
    return [p["name"] for p in _preset_data(context, top).get("configurePresets", []) if not p.get("hidden")]


def _key(top: str) -> str:
    return "root" if top == "." else top.replace("/", "__")


def _preset_field(presets: dict, name: str, field: str):
    """A configure preset's field, its `inherits` followed: the first that sets it wins."""
    seen, todo = set(), [name]
    while todo:
        current = todo.pop(0)
        if current in seen or current not in presets:
            continue
        seen.add(current)
        value = presets[current].get(field)
        if value:
            return value
        inherits = presets[current].get("inherits") or []
        todo += [inherits] if isinstance(inherits, str) else list(inherits)
    return None


def _compilers(context, top: str, preset: str) -> list[str]:
    """The needs that bring the compilers a preset's toolchain file sets."""
    presets = {p["name"]: p for p in _preset_data(context, top).get("configurePresets", [])}
    file = _preset_field(presets, preset, "toolchainFile")
    if not file:
        return []
    rel = posixpath.normpath(posixpath.join(top, file.replace("${sourceDir}", ".").lstrip("/")))
    if rel not in context.inventory.headers:
        return []
    found = {PurePosixPath(c).name for c in COMPILER.findall(context.inventory.text(rel))}
    return sorted({preparation.COMPILERS[c] for c in found if c in preparation.COMPILERS})


def _manager(context, top: str) -> tuple[str | None, str | None]:
    """The dependency manager the folder declares, and the `choice` it took when it declares two."""
    declared = [m for m in MANAGERS if any(posixpath.join(top, f).removeprefix("./") in context.inventory.headers
                                           for f in m[1])]
    if len(declared) < 2:
        return (declared[0] if declared else None), None
    named = {str(p.get("cacheVariables", {}).get("CMAKE_TOOLCHAIN_FILE", ""))
             for p in _preset_data(context, top).get("configurePresets", [])}
    chosen = next((m for m in declared if any(m[0] in value for value in named)), declared[0])
    return chosen, f"{' and '.join(m[0] for m in declared)} declared: {chosen[0]} prepares the configure"


def commands(context):
    lists = sorted({_folder(rel) for rel in context.inventory.files if PurePosixPath(rel).name == FILE},
                   key=lambda f: (f.count("/"), f))
    tops = [f for f in lists if not any(o != f and _inside(f, o) for o in lists)]
    tops += [f for f in lists if f not in tops
             and PROJECT.search(context.inventory.text(posixpath.join(f, FILE).removeprefix("./")))]
    out = []
    for top in tops:
        manager, choice = _manager(context, top)
        if manager:
            out.append({"tool": "cmake", "argv": ["sh", "-c", f'mkdir -p "{PREP}/$1" && {manager[2]}', "prepare",
                                                  _key(top)],
                        "cwd": top, "env": {}, "network": "registries", "needs": [manager[0]],
                        **({"choice": choice} if choice else {})})
        for preset in ["", *_presets(context, top)]:
            needs = _compilers(context, top, preset) if preset else []
            out.append({"tool": "cmake", "argv": ["sh", "-c", SCRIPT, "cmake", preset, _key(top)], "cwd": top,
                        "env": {}, "network": "none", **({"needs": needs} if needs else {})})
    return out or None


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
        if command["argv"][3] == "prepare":
            if command.get("choice"):
                gaps.append({"kind": "choice", "path": command["cwd"], "detail": command["choice"]})
            if result["returncode"] != 0:
                gaps.append({"kind": "restore_failed", "path": command["cwd"], "manager": command["needs"][0],
                             "detail": (result["stderr"] or "").strip()[-300:] or f"exit {result['returncode']}"})
            continue
        top, preset = command["cwd"], command["argv"][4]
        files = replies(result["stdout"]) if result["returncode"] == 0 else {}
        index = next((files[n] for n in sorted(files) if n.startswith("index-")), None)
        entry = next((o for o in (index or {}).get("objects", []) if o.get("kind") == "codemodel"), None)
        if entry is None:
            gaps.append({"kind": "model_failed", "path": top, **({"preset": preset} if preset else {}),
                         "detail": f"cmake configure: {_error(result['stderr'])}"})
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
            graph = target.get("backtraceGraph") or {}
            for group in groups:  # the language standard CMake applies, where the target that gets it is defined
                standard, tool = (group.get("languageStandard") or {}), STANDARDS.get(group.get("language"))
                node = graph["nodes"][standard["backtraces"][0]] if standard.get("backtraces") else None
                if tool and standard.get("standard") and node is not None:
                    where = rel(graph["files"][node["file"]], top)
                    toolchain = {"tool": tool, "version": standard["standard"], "line": node.get("line"),
                                 "declared_in": f"{where}#{group['language']}_STANDARD"}
                    if toolchain not in toolchains:
                        toolchains.append(toolchain)
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
    return {"facts": facts, "gaps": gaps, "covers": {"cmake-target": sorted(reached)},
            **({"version": version} if version else {})}
