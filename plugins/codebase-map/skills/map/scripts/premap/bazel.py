"""Source: Bazel's own model of the build, `bazel query` and `bazel mod graph`, where a workspace is declared.

`commands` describes, for Daodan's container, in the top folder holding MODULE.bazel, WORKSPACE or
WORKSPACE.bazel: `bazel query` of every library, binary and test rule of `//...` as streamed JSON protos, and,
with a MODULE.bazel, `bazel mod graph --output=json` for the root module. Both reach the registries: Bazel
fetches the module graph and the rules its BUILD files load, and loading them runs Starlark. `read` turns each
rule into a `bazel-target` unit named by its label, rooted at its package, with the BUILD file that declares it,
its rule class, its source files, `defines` and `local_defines`, and its `deps` inside the workspace as edges;
the root module is a `bazel-module` unit (its `bazel_dep`s are libraries: never stated); the packages form the
workspace. A query that failed is a `model_failed` gap.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "bazel", "9.3.1", "model"
DOWNLOAD = (("https://github.com/bazelbuild/bazel/releases/download/9.3.1/bazel-9.3.1-linux-x86_64",
             "7f775b54bbec487efaf0f49ccda1d2ed02cd34f582edfdd6aeeec76e39ef585c"),)  # what the runner carries
WORKSPACES = ("MODULE.bazel", "WORKSPACE", "WORKSPACE.bazel")
BUILD_FILES = (*WORKSPACES, "BUILD", "BUILD.bazel")  # build files without a suffix the snapshot records
STARTUP = ["bazel", "--max_idle_secs=5"]  # the server ends once the commands are done
QUERY = 'kind(".*_(library|binary|test) rule", //...)'
SOURCES = ("srcs", "hdrs")
DEFINES = ("defines", "local_defines")


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def commands(context):
    marks = {rel for rel in context.inventory.files if PurePosixPath(rel).name in WORKSPACES}
    folders = sorted({_folder(rel) for rel in marks}, key=lambda f: (f.count("/"), f))
    tops = [f for f in folders if not any(o != f and _inside(f, o) for o in folders)]
    out = []
    for top in tops:
        out.append({"tool": "bazel", "argv": [*STARTUP, "query", QUERY, "--output=streamed_jsonproto",
                                              "--keep_going"], "cwd": top, "env": {}, "network": "registries"})
        if posixpath.join(top, "MODULE.bazel").removeprefix("./") in marks:
            out.append({"tool": "bazel", "argv": [*STARTUP, "mod", "graph", "--output=json"], "cwd": top,
                        "env": {}, "network": "registries"})
    return out or None


def _label_path(label: str, top: str) -> str | None:
    """`//pkg:file` as the file's path from the project's root; None for a label of another repository."""
    if not label.startswith("//"):
        return None
    package, _, name = label[2:].partition(":")
    return posixpath.normpath(posixpath.join(top, package, name or PurePosixPath(package).name))


def read(context, commands, results):
    units, workspaces, gaps = [], [], []
    for command, result in zip(commands, results):
        top, what = command["cwd"], command["argv"][len(STARTUP)]
        if result["returncode"] != 0 and not (what == "query" and result["returncode"] == 3 and result["stdout"]):
            gaps.append({"kind": "model_failed", "path": top,
                         "detail": f"bazel {what}: {(result['stderr'] or '').strip()[-300:]}"})
            continue
        if what == "mod":
            module = json.loads(result["stdout"])
            units.append({"name": module.get("name") or None, "kind": "bazel-module", "root": top,
                          "manifest": posixpath.join(top, "MODULE.bazel").removeprefix("./"),
                          "source_roots": [], "depends_on": [], "config": {}})
            continue
        if result["returncode"] == 3:  # --keep_going: some packages did not load
            gaps.append({"kind": "model_partial", "path": top,
                         "detail": f"bazel query: {(result['stderr'] or '').strip()[-300:]}"})
        rules = [json.loads(line)["rule"] for line in result["stdout"].splitlines() if line.strip()]
        labels = {rule["name"] for rule in rules}
        members = []
        for rule in rules:
            values = {a["name"]: a.get("stringListValue") or [] for a in rule.get("attribute", [])
                      if a.get("explicitlySpecified")}
            package = rule["name"][2:].partition(":")[0]
            folder = posixpath.normpath(posixpath.join(top, package)) if package else top
            sources = sorted({p for key in SOURCES for label in values.get(key, [])
                              for p in [_label_path(label, top)] if p})
            config = {"rule": rule["ruleClass"], "sources": sources}
            defines = sorted({d for key in DEFINES for d in values.get(key, [])})
            if defines:
                config["build_tags"] = defines
            manifest = rule["location"].rsplit(":", 2)[0]
            members.append(folder)
            units.append({"name": rule["name"], "kind": "bazel-target", "root": folder,
                          "manifest": posixpath.relpath(manifest, result["root"]) if result.get("root") else manifest,
                          "source_roots": sorted({_folder(s) for s in sources}),
                          "depends_on": sorted(d for d in values.get("deps", []) if d in labels), "config": config})
        if members:
            workspaces.append({"tool": "bazel", "root": top, "members": sorted(set(members))})
    facts = {key: value for key, value in (("units", units), ("workspace", workspaces)) if value}
    return {"facts": facts, "gaps": gaps}
