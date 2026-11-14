"""The TypeScript compiler over a project's JS/TS/JSX/TSX, for the stylesheet graph: one program, every place a class,
an id, a CSS Module member, a custom property or a stylesheet import is written (`css_typescript.js`).

`index` gives the script a tsconfig holding the given files (`allowJs`, the project's own tsconfig extended when
there is one) and runs it through the stage's runner (`css_sass`) with the TypeScript pinned in `css_engines/`; the
types come from the project's packages.
A class expression is evaluated, not guessed: a string, a template, a condition, `&&`, `||`, `+`, a call to
`clsx`, `classnames` or `tailwind-merge` (recognised by the package that declares the callee), `[...].join(' ')`,
and a name only through what the checker states: a string literal type, or the initializer of a const or of a
const object's property. Anything else is a hole of its kind. Records are those `css.graph` reads.
"""
from __future__ import annotations

from pathlib import Path

from .css_sass import failure

SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def index(project_dir: Path, runner, files: list[str] | None = None) -> dict:
    project_dir = Path(project_dir).resolve()
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*")
                       if path.suffix in SUFFIXES and "node_modules" not in path.parts)
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    config = {"compilerOptions": options, "files": list(files), "include": []}
    if (project_dir / "tsconfig.json").is_file():
        config["extends"] = "./tsconfig.json"
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    data, run = runner(SCRIPT, {"tsconfig": config, "files": files})
    if data is None:
        reason = failure("typescript", run)
        return {"indexer": {"name": "typescript", "version": None, "seconds": run.get("seconds"),
                            "peak_mb": run.get("peak_mb")},
                "records": [], "missing": {rel: reason for rel in files}, "run": run}
    walked = set(data["files"])
    return {"indexer": {"name": "typescript", "version": data["typescript"], "seconds": run.get("seconds"),
                        "peak_mb": run.get("peak_mb")},
            "records": data["records"], "missing": {rel: "not in the TypeScript program" for rel in files
                                                    if rel not in walked},
            "run": run}
