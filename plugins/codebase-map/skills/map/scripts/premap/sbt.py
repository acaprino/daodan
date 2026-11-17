"""Source: sbt's own loaded build, each project's `thisProject` as `show` prints it, at each top sbt build.

`commands` describes, for Daodan's container, in each folder holding a `build.sbt` or a `project/build.properties`
that no other one holds, with the sbt launcher Daodan carries: `sbt projects`, which lists every project the build
loads (by a `lazy val`, by code, by a plugin's `extraProjects`), then `sbt "show <id>/thisProject"` for each one,
which prints its id, base folder and classpath dependencies; both outputs on stdout. sbt compiles the build
definition (build.sbt, `project/*.scala`, its plugins) and loads it; it reaches the registries (sbt itself, Scala,
the build's plugins). `read` turns each project into an `sbt-project` unit named by its id, rooted at its base
folder, with the folder's build.sbt as manifest when it holds one, and the projects of the build it depends on as
edges; the build is an `sbt` workspace whose members are its projects' folders other than its root. A build that
did not load is a `model_failed` gap.
"""
from __future__ import annotations

import posixpath
import re

NAME, VERSION, RANK = "sbt", "1.13.1", "model"  # the launcher; the build's `sbt.version` is what loads it
DOWNLOAD = (("https://github.com/sbt/sbt/releases/download/v1.13.1/sbt-1.13.1.tgz",
             "4a20e36c1642b6d5be34ef641d2ed6c8c0d464e6145283730d5566716e4083be"),)  # what the runner carries
MARKS = ("build.sbt", "project/build.properties")
SBT = "sbt -batch -no-colors -Dsbt.server.forcestart=false -Dsbt.supershell=false"
SCRIPT = (f'{SBT} projects > /tmp/sbt-projects.txt; r=$?; cat /tmp/sbt-projects.txt; [ $r -eq 0 ] || exit $r;'
          r' set --; for i in $(sed -n "s/^\[info\] \t[ *]*\([^ ]*\)$/\1/p" /tmp/sbt-projects.txt);'
          f' do set -- "$@" "show $i/thisProject"; done; exec {SBT} "$@"')
PROJECT = re.compile(r"Project\(id ([^,]+), base: ([^,)]+)(.*)\)")
DEPENDENCY = re.compile(r"ResolvedClasspathDependency\(ProjectRef\([^,]+,([^)]+)\)")


def _top(rel: str) -> str:
    for mark in MARKS:
        if rel == mark or rel.endswith("/" + mark):
            folder = rel[: -len(mark)].rstrip("/")
            return folder or "."
    return ""


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def commands(context):
    folders = sorted({f for f in map(_top, context.inventory.files) if f}, key=lambda f: (f.count("/"), f))
    tops = [f for f in folders if not any(o != f and _inside(f, o) for o in folders)]
    return [{"tool": "sbt", "argv": ["sh", "-c", SCRIPT], "cwd": top,
             "env": {"SBT_OPTS": "-Xmx1g", "JAVA_OPTS": "-Xmx1g"}, "network": "registries"} for top in tops] or None


def read(context, commands, results):
    units, workspaces, gaps = [], [], []
    headers = getattr(getattr(context, "inventory", None), "headers", {})
    for command, result in zip(commands, results):
        root = result.get("root") or "/"
        found = {}
        for line in (result["stdout"] or "").splitlines():
            match = PROJECT.search(line)
            if match:
                base = posixpath.relpath(posixpath.normpath(match.group(2)), root)
                if not base.startswith(".."):
                    dependencies = match.group(3).split("dependencies: List(", 1)
                    found[match.group(1)] = (base, DEPENDENCY.findall(dependencies[1]) if len(dependencies) > 1 else [])
        if result["returncode"] != 0 or not found:
            gaps.append({"kind": "model_failed", "path": command["cwd"],
                         "detail": f"sbt: {(result['stderr'] or result['stdout'] or '').strip()[-300:]}"})
            continue
        for name, (base, needs) in found.items():
            manifest = posixpath.join(base, "build.sbt").removeprefix("./")
            units.append({"name": name, "kind": "sbt-project", "root": base,
                          "manifest": manifest if manifest in headers else None,
                          "depends_on": sorted(set(needs) & set(found) - {name})})
        top = posixpath.normpath(command["cwd"])
        members = sorted({base for base, _ in found.values() if base != top})
        if members:
            workspaces.append({"tool": "sbt", "root": top, "members": members})
    facts = {key: value for key, value in (("units", units), ("workspace", workspaces)) if value}
    return {"facts": facts, "gaps": gaps}
