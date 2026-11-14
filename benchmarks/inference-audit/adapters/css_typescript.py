"""The TypeScript compiler over a project's JS/TS/JSX/TSX, for the CSS graph: one program, every place a class, an
id, a CSS Module member, a custom property or a stylesheet import is written (`css_typescript.js`).

`index` writes a tsconfig holding the given files (`allowJs`, the project's own tsconfig extended when there is
one) and runs the script with the project's TypeScript (`node_modules/typescript`), else `DAODAN_TS_MODULE`,
else the TypeScript pinned with the CSS engines.
A class expression is evaluated, not guessed: a string, a template, a condition, `&&`, `||`, `+`, a call to
`clsx`, `classnames` or `tailwind-merge` (recognised by the package that declares the callee), `[...].join(' ')`,
and a name only through what the checker states: a string literal type, or the initializer of a const or of a
const object's property. Anything else is a hole of its kind. Records are those `css.graph` reads.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402

SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def _typescript(project_dir: Path) -> Path | None:
    """The project's TypeScript, else `DAODAN_TS_MODULE`, else the one pinned with the CSS engines."""
    own = project_dir / "node_modules/typescript"
    if own.is_dir():
        return own
    if os.environ.get("DAODAN_TS_MODULE"):
        return Path(os.environ["DAODAN_TS_MODULE"])
    pinned = Path(os.environ.get("DAODAN_CSS_ENGINES", "")) / "typescript"
    return pinned if os.environ.get("DAODAN_CSS_ENGINES") and pinned.is_dir() else None


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*")
                       if path.suffix in SUFFIXES and "node_modules" not in path.parts)
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    config = {"compilerOptions": options, "files": [str(project_dir / rel) for rel in files], "include": []}
    own = project_dir / "tsconfig.json"
    if own.is_file():
        config["extends"] = str(own)
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    tsconfig = work_dir / "css-tsconfig.json"
    tsconfig.write_text(json.dumps(config, indent=1), encoding="utf-8")
    settings = work_dir / "css-typescript.json"
    settings.write_text(json.dumps({"tsconfig": str(tsconfig), "root": str(project_dir), "files": files}),
                        encoding="utf-8")
    output = work_dir / "css-typescript-out.json"
    output.unlink(missing_ok=True)
    module = _typescript(project_dir)
    env = dict(os.environ, NODE_OPTIONS="--max-old-space-size=6144")
    if module is not None:
        env["DAODAN_TS_MODULE"] = str(module)
    node = Path(os.environ["DAODAN_NODE_BIN"]) / "node" if os.environ.get("DAODAN_NODE_BIN") else "node"
    run = scip_graph.measured([str(node), str(SCRIPT), str(settings), str(output)], str(work_dir), env, 3 * 3600)
    if not output.is_file():
        return {"indexer": {"name": "typescript", "version": None, "seconds": run["seconds"], "peak_mb": run["peak_mb"]},
                "records": [], "missing": {rel: "the TypeScript run failed" for rel in files}, "run": run}
    data = json.loads(output.read_text(encoding="utf-8"))
    walked = set(data["files"])
    return {"indexer": {"name": "typescript", "version": data["typescript"], "seconds": run["seconds"],
                        "peak_mb": run["peak_mb"]},
            "records": data["records"], "missing": {rel: "not in the TypeScript program" for rel in files
                                                    if rel not in walked},
            "run": {key: run[key] for key in ("returncode", "seconds", "peak_mb", "stderr_tail")}}
