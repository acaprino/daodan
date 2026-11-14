"""The project's Tailwind, for the stylesheet graph: which class tokens are Tailwind utilities (`css_tailwind.js`).

`index` asks the installed `node_modules/tailwindcss` for the order of every token: a token Tailwind does not
generate has none. Tailwind 3 reads the project's `tailwind.config.*` at its root; Tailwind 4 the design system of each
CSS entry that imports `tailwindcss` (`entries`). Loading a config or a plugin runs the project's code, as Tailwind's
own build does: the script runs through the stage's runner (`css_sass`), in the container like every engine.
Without Tailwind installed, `valid` is None and no token is one.
"""
from __future__ import annotations

from pathlib import Path

from .css_sass import failure

SCRIPT = Path(__file__).resolve().with_suffix(".js")
CONFIGS = ("tailwind.config.js", "tailwind.config.cjs", "tailwind.config.mjs", "tailwind.config.ts")


def index(project_dir: Path, runner, tokens: list[str], entries: list[str] | None = None) -> dict:
    project_dir = Path(project_dir).resolve()
    package = project_dir / "node_modules/tailwindcss"
    if not (package / "package.json").is_file():
        return {"indexer": {"name": "tailwindcss", "version": None, "seconds": 0, "peak_mb": None}, "valid": None,
                "version": None, "error": "tailwindcss not installed"}
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
