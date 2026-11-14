"""The project's Tailwind, for the CSS graph: which class tokens are Tailwind utilities (`css_tailwind.js`).

`index` asks the installed `node_modules/tailwindcss` for the order of every token: a token Tailwind does not
generate has none. Tailwind 3 reads the project's `tailwind.config.*` at its root; Tailwind 4 the design system of each
CSS entry that imports `tailwindcss` (`entries`). Loading a config or a plugin runs the project's code, as Tailwind's
own build does. Without Tailwind installed, `valid` is None and no token is one.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402

SCRIPT = Path(__file__).resolve().with_suffix(".js")
CONFIGS = ("tailwind.config.js", "tailwind.config.cjs", "tailwind.config.mjs", "tailwind.config.ts")


def index(project_dir: Path, work_dir: Path, tokens: list[str], entries: list[str] | None = None) -> dict:
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    package = project_dir / "node_modules/tailwindcss"
    if not (package / "package.json").is_file():
        return {"indexer": {"name": "tailwindcss", "version": None, "seconds": 0, "peak_mb": None}, "valid": None,
                "version": None, "error": "tailwindcss not installed"}
    config = next((project_dir / name for name in CONFIGS if (project_dir / name).is_file()), None)
    settings = work_dir / "css-tailwind.json"
    sources = [{"path": str(project_dir / rel), "text": (project_dir / rel).read_text(encoding="utf-8")}
               for rel in entries or ()]
    settings.write_text(json.dumps({"tailwind": str(package), "config": str(config) if config else None,
                                    "entries": sources, "tokens": tokens}), encoding="utf-8")
    output = work_dir / "css-tailwind-out.json"
    output.unlink(missing_ok=True)
    node = Path(os.environ["DAODAN_NODE_BIN"]) / "node" if os.environ.get("DAODAN_NODE_BIN") else "node"
    run = scip_graph.measured([str(node), str(SCRIPT), str(settings), str(output)], str(project_dir), None, 1800)
    data = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else {
        "version": None, "valid": None, "error": run["stderr_tail"][-600:]}
    return {"indexer": {"name": "tailwindcss", "version": data["version"], "seconds": run["seconds"],
                        "peak_mb": run["peak_mb"]},
            "valid": data["valid"], "version": data["version"], "error": data["error"],
            "config": config.relative_to(project_dir).as_posix() if config else None, "tokens": len(tokens)}
