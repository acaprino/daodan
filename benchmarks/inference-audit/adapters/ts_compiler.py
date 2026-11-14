"""The TypeScript compiler API in batch, for JavaScript and TypeScript: a second source beside the SCIP index.

`analyze` builds one program over a copy of the checkout (`allowJs`, the generated tsconfig of the plugin's
`indexers/typescript.py`, the engine pass's package install) and asks the checker, in one Node process
(`ts_compiler.js`), for every call and `new`: `getResolvedSignature(call).declaration`, else the symbol at the
callee's name through `getAliasedSymbol`. TypeScript 7.0 ships without a JavaScript API; `@typescript/typescript6`
re-exports the 6.0 one (the TypeScript blog, 7.0 announcement). An edge's `callee` is `file:line:column` of the
declaration's start (1-based line, UTF-8 byte column, the snapshot's unit), project-relative for a project
file; an external carries the npm package of the file it is declared in.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402

VERSION = "6.0.2"  # @typescript/typescript6, which re-exports typescript 6.0.x
TOOLS = Path(os.environ.get("DAODAN_STRONG_JS", "/opt/strong-js"))  # where the npm tools are installed
NODE = Path(os.environ.get("DAODAN_NODE_BIN", "/opt/node/bin"))
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def _link(source: str, destination: str) -> None:
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def mirror(project_dir: Path, work_dir: Path) -> Path:
    """A copy of the checkout with its packages inside it (hard links), so every file resolves under it."""
    import resolve_edges as rx
    here = Path(work_dir) / "mirror-strong-js"
    if here.exists():
        return here
    shutil.copytree(project_dir, here, symlinks=True, ignore=shutil.ignore_patterns("node_modules", ".git"))
    own = Path(project_dir) / "node_modules"
    modules = own if own.is_dir() else rx.npm_modules(Path(project_dir))  # npm ci --ignore-scripts, shared cache
    if modules is not None:
        for found in sorted(modules.parent.rglob("node_modules")):
            relative = found.relative_to(modules.parent)
            if "node_modules" in relative.parts[:-1] or (here / relative).exists():
                continue
            (here / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(found, here / relative, symlinks=True, copy_function=_link)
    return here


_PACKAGES: dict = {}


def package_of(path: Path) -> dict | None:
    """`{"manager", "package", "version"}` of the nearest package.json with a name above a file."""
    for parent in Path(path).parents:
        if parent in _PACKAGES:
            return _PACKAGES[parent]
        manifest = parent / "package.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            if data.get("name"):
                _PACKAGES[parent] = {"manager": "npm", "package": data["name"], "version": data.get("version")}
                return _PACKAGES[parent]
        if parent.name == "node_modules":
            break
    return None


class Lines:
    """UTF-16 (JavaScript) columns to UTF-8 byte columns, per file."""

    def __init__(self):
        self.cache: dict = {}

    def byte(self, path: Path, line: int, column: int) -> int:
        if path not in self.cache:
            try:
                self.cache[path] = path.read_text(encoding="utf-8").split("\n")
            except (OSError, UnicodeError):
                self.cache[path] = []
        text = self.cache[path][line - 1] if 1 <= line <= len(self.cache[path]) else ""
        if text.isascii():
            return column
        return len(text.encode("utf-16-le")[:2 * column].decode("utf-16-le", errors="ignore").encode("utf-8"))


def where(path: Path, root: Path, line: int, column: int, lines: Lines) -> tuple[str, dict | None]:
    """`(rel:line:byte column, None)` inside the project, `(package path:line:column, package)` outside it."""
    resolved = Path(path).resolve()
    try:
        rel = resolved.relative_to(root)
        if "node_modules" not in rel.parts:
            return f"{rel.as_posix()}:{line}:{lines.byte(resolved, line, column)}", None
    except ValueError:
        pass
    package = package_of(resolved) or {"manager": "unknown", "package": resolved.parent.name, "version": None}
    tail = "/".join(resolved.parts[-2:])
    return f"{tail}:{line}:{column}", package


def analyze(project_dir: Path, work_dir: Path, files: list[str] | None = None, label: str = "") -> dict:
    from indexers import typescript
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    here = mirror(Path(project_dir), work_dir)
    root = here.resolve()
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in Path(project_dir).rglob("*")
                       if path.suffix in typescript.SUFFIXES and "node_modules" not in path.parts)
    if not (here / "tsconfig.project.json").exists() and not (here / ".strong-js-tsconfig").exists():
        typescript._tsconfig(here, [rel for rel in files if rel.endswith(typescript.SUFFIXES)])
        (here / ".strong-js-tsconfig").write_text("generated\n", encoding="utf-8")
    output = work_dir / f"ts-compiler{'-' + label if label else ''}.jsonl"
    env = dict(os.environ, NODE_OPTIONS="--max-old-space-size=12288",
               DAODAN_TS_MODULE=str(TOOLS / "node_modules/@typescript/typescript6"))
    env["PATH"] = f"{NODE}{os.pathsep}{env.get('PATH', '')}"
    node = shutil.which("node", path=env["PATH"]) or "node"
    run = scip_graph.measured([node, str(SCRIPT), str(here / "tsconfig.json"), str(output)], str(here), env, 3 * 3600)
    edges, counts, lines, current = [], {}, Lines(), None
    if output.is_file():
        with output.open(encoding="utf-8") as handle:
            for text in handle:
                row = json.loads(text)
                if "file" in row:
                    current = Path(row["file"])
                    continue
                if "counts" in row:
                    counts = row["counts"]
                    continue
                site, _ = where(current, root, *row["site"], lines)
                caller = where(current, root, *row["caller"], lines)[0] if row.get("caller") else site.rsplit(":", 2)[0]
                decl = row.get("decl")
                if not decl:
                    continue
                callee, external = where(Path(decl["file"]), root, *decl["start"], lines)
                edges.append({"caller": caller, "callee": callee, "site": site, "kind": row["kind"],
                              "external": external, "via": row["via"], "declaration": decl["kind"],
                              "receiver_any": row.get("receiver_any")})
    return {"edges": edges, "counts": counts, "run": run,
            "engine": {"name": "typescript (compiler API, @typescript/typescript6)", "version": counts.get("version"),
                       "seconds": run["seconds"], "peak_mb": run["peak_mb"]}}
