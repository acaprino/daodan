"""Source: Meson's own model of the build, `meson introspect --targets --projectinfo`, per top meson.build folder.

`commands` describes, for Daodan's container, with the network closed: `meson setup` into a build folder outside
the copy (wraps never downloaded, Ninja on the path but never run; it runs meson.build and probes the compilers) and the
introspection of that folder; beside it, `meson introspect meson.build`, which reads the build files without
configuring. `read` keeps the configured answer, else the source tree's one with a `model_partial` gap (what
the configure decides, dependencies and conditions, is then unknown). Each target is a `meson-target` unit:
the folder of the meson.build defining it, its sources' folders, the targets it links as edges, its type,
sources, include folders and `-D` definitions as the compiler gets them. An edge is a target whose output
file the linker of another one reads.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "meson", "1.12.1", "model"
DOWNLOAD = (  # what the runner carries: Meson, and Ninja, its backend, which the setup only finds
    ("https://files.pythonhosted.org/packages/py3/m/meson/meson-1.12.1-py3-none-any.whl",
     "930bc7542cbd9f57009e182fd014eba48cf1a0180a7b9006d2d32d8f168d8b02"),
    ("https://files.pythonhosted.org/packages/6e/53/ebfed7b689c338dd8ebeec9c0730c8d56821292f14e2536e5f3ef1a05744/"
     "ninja-1.13.2-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
     "65a24341b5ac09fcadcc37082660be40a94174e51a937fabf6e2cae26225fa2c"))
FILE = "meson.build"
SECTIONS = ["--targets", "--projectinfo"]
SETUP = ('b=$(mktemp -d) && meson setup --wrap-mode nodownload "$b" >&2'
         ' && meson introspect "$b" ' + " ".join(SECTIONS))


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def commands(context):
    builds = sorted({_folder(rel) for rel in context.inventory.files if PurePosixPath(rel).name == FILE},
                    key=lambda f: (f.count("/"), f))
    tops = [f for f in builds if not any(o != f and _inside(f, o) for o in builds)]
    return [command for top in tops for command in (
        {"tool": "meson", "argv": ["sh", "-c", SETUP], "cwd": top, "env": {}, "network": "none"},
        {"tool": "meson", "argv": ["meson", "introspect", FILE, *SECTIONS], "cwd": top, "env": {},
         "network": "none"})] or None


def read(context, commands, results):
    root = next((r["root"] for r in results if r.get("root")), "/")
    by_folder: dict[str, list] = {}
    for command, result in zip(commands, results):
        by_folder.setdefault(command["cwd"], []).append(result)
    units, gaps = [], []

    def rel(path: str, base: str) -> str | None:
        full = posixpath.normpath(path if posixpath.isabs(path) else posixpath.join(root, base, path))
        value = posixpath.relpath(full, root)
        return None if value.startswith("..") else value

    for top, (configured, plain) in by_folder.items():
        chosen = configured if configured["returncode"] == 0 else plain if plain["returncode"] == 0 else None
        if chosen is None:
            gaps.append({"kind": "model_failed", "path": top, "detail": "; ".join(
                f"{name}: {(r['stderr'] or '').strip()[-300:]}" for name, r in (("meson setup", configured),
                                                                                 ("meson introspect", plain)))})
            continue
        if chosen is plain:
            gaps.append({"kind": "model_partial", "path": top, "detail": "dependencies, conditions and links "
                         f"unknown: meson setup: {(configured['stderr'] or '').strip()[-300:]}"})
        targets = json.loads(chosen["stdout"])["targets"]
        outputs = {f: t["name"] for t in targets for f in t.get("filename", [])}
        for target in targets:
            groups = [g for g in target.get("target_sources", []) if "sources" in g]
            sources = sorted({p for g in groups for s in g["sources"] for p in [rel(s, top)] if p})
            parameters = [p for g in groups for p in g.get("parameters", [])]
            linked = [p for g in target.get("target_sources", []) if "linker" in g for p in g.get("parameters", [])]
            manifest = rel(target["defined_in"], top)
            config = {"type": target["type"], "sources": sources}
            includes = sorted({p for i in parameters if i.startswith("-I") for p in [rel(i[2:], top)] if p})
            defines = sorted({d[2:] for d in parameters if d.startswith("-D")})
            if includes:
                config["include_dirs"] = includes
            if defines:
                config["build_tags"] = defines
            units.append({"name": target["name"], "kind": "meson-target", "root": _folder(manifest),
                          "manifest": manifest, "source_roots": sorted({_folder(s) for s in sources}),
                          "depends_on": sorted({name for file, name in outputs.items() if name != target["name"]
                                                and any(file == p or file.endswith("/" + p) for p in linked)}),
                          "config": config})
    return {"facts": {"units": units} if units else {}, "gaps": gaps}
