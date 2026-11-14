"""Go's whole-program call graph: `golang.org/x/tools/cmd/callgraph`, algorithm VTA, tests included.

`analyze` installs the tool at a pinned release (`go install`, checked against the Go checksum database) and
runs it once over the root module: `./...` and the directories that pattern skips (`_x`, `.x`), never a nested
module. VTA types every function the program holds, reached from a `main` or not; the tool folds synthetic
wrappers into the edges that cross them (`DeleteSyntheticNodes`), and a generic instance keeps its origin's
position. An edge is kept when its call site is in the project. The site is where SSA puts the call: the `(` of
the call, or the `go` / `defer` keyword. A function declared in the project is `rel:line:col` (its name, or the
`func` of a literal); any other is its SSA name, with its module read from the path that declares it.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402

VERSION = "v0.52.0"  # golang.org/x/tools, 2026-10-10
GO = Path(os.environ.get("DAODAN_GO_ROOT", "/opt/go"))
FIELDS = ("{{posn .Caller}}", "{{.Caller}}", "{{posn .Callee}}", "{{.Callee}}", "{{.Filename}}:{{.Line}}:{{.Column}}",
          "{{.Dynamic}}", "{{.Description}}")


def _position(text: str) -> tuple[str, int, int] | None:
    """`file:line:col` as `token.Position` prints it; None for `-`."""
    parts = text.rsplit(":", 2)
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        return None
    return parts[0], int(parts[1]), int(parts[2])


def _unescape(path: str) -> str:
    """A module path as the module cache spells it (`!x` stands for `X`)."""
    out, upper = [], False
    for char in path:
        if char == "!":
            upper = True
            continue
        out.append(char.upper() if upper else char)
        upper = False
    return "".join(out)


class _Place:
    """Where a function is declared: the project, the Go release, or a module in the cache."""

    def __init__(self, root: Path, goroot: Path, modcache: Path, go_version: str):
        self.root, self.goroot, self.modcache, self.go_version = f"{root}/", f"{goroot}/src/", f"{modcache}/", go_version

    def rel(self, path: str) -> str | None:
        return path[len(self.root):] if path.startswith(self.root) else None

    def external(self, path: str | None, name: str) -> dict:
        if path and path.startswith(self.goroot):
            return {"manager": "gomod", "package": "github.com/golang/go/src", "version": self.go_version}
        if path and path.startswith(self.modcache):
            module, _, rest = path[len(self.modcache):].partition("@")
            return {"manager": "gomod", "package": _unescape(module), "version": rest.split("/", 1)[0]}
        return {"manager": "gomod", "package": "", "version": ""}  # a function with no position

    def function(self, posn: str, name: str) -> tuple[str, dict | None]:
        position = _position(posn)
        rel = self.rel(position[0]) if position else None
        if rel is not None:
            return f"{rel}:{position[1]}:{position[2]}", None
        return name, self.external(position[0] if position else None, name)


def patterns(project_dir: Path) -> list[str]:
    """`./...` and each directory of the root module it skips, outside nested modules and `testdata`."""
    roots = scip_graph.manifest_dirs(project_dir, "go.mod")
    found = set()
    for path in project_dir.rglob("*.go"):
        rel = path.relative_to(project_dir).as_posix()
        parts = rel.split("/")[:-1]
        if not parts or ".git" in parts or "testdata" in parts or scip_graph.owner(rel, roots) != "":
            continue
        if any(part.startswith(("_", ".")) for part in parts):
            found.add("/".join(parts))
    return ["./...", *(f"./{directory}" for directory in sorted(found))]


def analyze(project_dir: Path, work_dir: Path) -> dict:
    import resolve_edges as rx
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    cache = rx.shared_cache_dir() / "go"
    env = dict(os.environ, GOROOT=str(GO), GOPATH=str(cache / "path"), GOCACHE=str(cache / "build"),
               GOTOOLCHAIN="local", GOFLAGS="-mod=readonly", GOTELEMETRY="off")
    env["PATH"] = f"{GO / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    tool = cache / "callgraph" / VERSION
    if not (tool / "callgraph").is_file():
        install = subprocess.run([str(GO / "bin/go"), "install", f"golang.org/x/tools/cmd/callgraph@{VERSION}"],
                                 env=dict(env, GOBIN=str(tool)), capture_output=True, text=True, timeout=1800)
        if install.returncode != 0:
            raise RuntimeError(f"go install callgraph@{VERSION}: {install.stderr[-2000:]}")
    subprocess.run([str(GO / "bin/go"), "mod", "download"], cwd=project_dir, env=env, capture_output=True,
                   timeout=1800)
    go_version = (GO / "VERSION").read_text(encoding="utf-8").split("\n", 1)[0].strip()
    loaded = patterns(project_dir)
    output = work_dir / "callgraph.tsv"
    command = [str(tool / "callgraph"), "-algo=vta", "-test", f"-format={chr(9).join(FIELDS)}", *loaded]
    run = scip_graph.measured(["sh", "-c", 'exec "$@" > "$0"', str(output), *command], str(project_dir), env,
                              3 * 3600)
    engine = {"name": "golang.org/x/tools/cmd/callgraph -algo=vta -test", "version": VERSION, "go": go_version,
              "seconds": run["seconds"], "peak_mb": run["peak_mb"], "patterns": loaded}
    if run["returncode"] != 0:
        engine.update(returncode=run["returncode"], stderr_tail=run["stderr_tail"])
        return {"edges": [], "engine": engine}
    gomodcache = subprocess.run([str(GO / "bin/go"), "env", "GOMODCACHE"], env=env, capture_output=True, text=True)
    place = _Place(project_dir, GO.resolve(), Path(gomodcache.stdout.strip() or cache / "path/pkg/mod"), go_version)
    edges, seen, lines = [], set(), 0
    with output.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            lines += 1
            fields = line.rstrip("\n").split("\t")
            if len(fields) != len(FIELDS):
                continue
            caller_posn, caller_name, callee_posn, callee_name, site, dynamic, description = fields
            position = _position(site)
            rel = place.rel(position[0]) if position else None
            if rel is None:
                continue
            caller, _ = place.function(caller_posn, caller_name)
            callee, external = place.function(callee_posn, callee_name)
            edge = (caller, callee, f"{rel}:{position[1]}:{position[2]}", dynamic, description)
            if edge in seen:
                continue
            seen.add(edge)
            edges.append({"caller": caller, "callee": callee, "site": edge[2], "kind": dynamic,
                          "description": description, "external": external})
    engine["lines"] = lines
    return {"edges": edges, "engine": engine}
