"""scip-typescript, for JavaScript and TypeScript: how the indexer runs. What its index states its own way
is the plugin's `indexers/typescript.py`.

`index` runs scip-typescript over a copy of the checkout with a generated tsconfig that holds every JS/TS
file of the snapshot (`allowJs`) and extends the project's own, after the engine pass's package install
(`npm ci --ignore-scripts`, `npm_modules`).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph  # noqa: E402

VERSION = "0.5.2"  # @sourcegraph/scip-typescript; needs Node >= 22.13
NODE = Path(os.environ.get("DAODAN_NODE_BIN", "/opt/node/bin"))
SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")


def _tsconfig(mirror: Path, files: list[str]) -> str | None:
    """Every JS/TS file of the snapshot in one program with `allowJs`; the project's own options kept."""
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    config = {"compilerOptions": options, "include": files, "exclude": []}
    own = mirror / "tsconfig.json"
    if own.is_file():
        own.rename(mirror / "tsconfig.project.json")
        config["extends"] = "./tsconfig.project.json"
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    own.write_text(json.dumps(config, indent=1), encoding="utf-8")
    return config.get("extends")


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    import resolve_edges as rx
    mirror = work_dir / "mirror-scip-typescript"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True, ignore=shutil.ignore_patterns("node_modules"))
    modules = rx.npm_modules(project_dir)  # the engine pass's own install: npm ci --ignore-scripts
    if modules is not None:
        for found in sorted(modules.parent.rglob("node_modules")):
            relative = found.relative_to(modules.parent)
            if "node_modules" in relative.parts[:-1]:
                continue
            link = mirror / relative
            if not link.exists():
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(found, target_is_directory=True)
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*")
                       if path.suffix in SUFFIXES and "node_modules" not in path.parts)
    extends = _tsconfig(mirror, [rel for rel in files if rel.endswith(SUFFIXES)])
    env = dict(os.environ, NODE_OPTIONS="--max-old-space-size=12288")
    env["PATH"] = f"{NODE}{os.pathsep}{env.get('PATH', '')}"
    output = work_dir / "scip-typescript-0.scip"
    run = {"prefix": "", **code_graph.measured(
        [str(NODE / "scip-typescript"), "index", "--cwd", str(mirror), "--output", str(output), "--no-progress-bar"],
        str(mirror), env, 3 * 3600)}
    run["index"] = str(output) if output.is_file() else None
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    return {"indexes": [[run["index"], ""]] if run["index"] else [], "runs": [run],
            "indexer": {"name": "scip-typescript", "version": VERSION, "seconds": run["seconds"],
                        "peak_mb": run["peak_mb"]},
            "node_modules": str(modules), "tsconfig_extends": extends}
