"""The project's Tailwind, for the stylesheet graph: which class tokens are Tailwind utilities (`css_tailwind.js`).

`index` asks the project's Tailwind for the order of every token: a token Tailwind does not generate has none. Each
entry is read with the Tailwind Node resolves from its folder (a workspace package's `node_modules/tailwindcss`, else
the root's), and `valid` gives each token the version of the one that generates it. Tailwind 3 reads the project's
`tailwind.config.*` at its root; Tailwind 4 the design system of each CSS entry that imports `tailwindcss`
(`entries`). Loading Tailwind, a config or a plugin runs the project's code, as Tailwind's own build does: the
script runs through the runner the graph gives it, the container's (`css.tailwind_runner`), never on the host. A
project whose manifests declare no `tailwindcss` (and holds no installed one) runs nothing: `valid` is None and no
token is one.
"""
from __future__ import annotations

from pathlib import Path

from tree_scope import DEPENDENCY_DIRS

from .css_sass import failure

SCRIPT = Path(__file__).resolve().with_suffix(".js")
CONFIGS = ("tailwind.config.js", "tailwind.config.cjs", "tailwind.config.mjs", "tailwind.config.ts")
PACKAGE = "tailwindcss"  # the npm package of the Tailwind asked


def declared(project_dir: Path) -> bool:
    """Whether the project has a Tailwind to ask: a `package.json` outside dependency folders that names
    `PACKAGE`, or one installed at the root."""
    if (project_dir / "node_modules" / PACKAGE / "package.json").is_file():
        return True
    return any(f'"{PACKAGE}"' in path.read_text(encoding="utf-8", errors="replace")
               for path in project_dir.rglob("package.json")
               if not any(part in DEPENDENCY_DIRS or part.startswith(".")
                          for part in path.relative_to(project_dir).parent.parts))


def index(project_dir: Path, runner, tokens: list[str], entries: list[str] | None = None) -> dict:
    project_dir = Path(project_dir).resolve()
    if not declared(project_dir):
        return {"indexer": {"name": "tailwindcss", "version": None, "seconds": 0, "peak_mb": None}, "valid": None,
                "version": None, "error": "tailwindcss not declared"}
    config = next((project_dir / name for name in CONFIGS if (project_dir / name).is_file()), None)
    sources = [{"path": rel, "text": (project_dir / rel).read_text(encoding="utf-8")} for rel in entries or ()]
    data, run = runner(SCRIPT, {"tailwind": "node_modules/tailwindcss",
                                "config": config.relative_to(project_dir).as_posix() if config else None,
                                "entries": sources, "tokens": tokens})
    data = data or {"version": None, "valid": None, "error": failure("tailwindcss", run)[-600:]}
    return {"indexer": {"name": "tailwindcss", "version": data["version"], "seconds": run.get("seconds"),
                        "peak_mb": run.get("peak_mb")},
            "valid": data["valid"], "version": data["version"], "error": data["error"],
            "config": config.relative_to(project_dir).as_posix() if config else None, "tokens": len(tokens)}
