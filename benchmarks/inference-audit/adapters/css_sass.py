"""The official Sass parser over SCSS and indented Sass, for the CSS graph (`css_sass.js`).

`sass-parser` is the Sass team's PostCSS-compatible wrapper of Dart Sass's own parser: the same grammar the compiler
reads, for both syntaxes, with `@use`, `@forward` (prefix, show, hide), variables and their flags, mixins, functions,
`@include` with content blocks, `@extend`, control flow and every expression as a tree. It is pinned in
`css_engines.json` and found in the folder `DAODAN_CSS_ENGINES` names. `index` parses each sheet, a file or a text
(a `<style lang="scss">` block), into the neutral tree `css.tree_records` reads.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402

SUFFIXES = (".scss", ".sass")
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def engines() -> Path | None:
    folder = os.environ.get("DAODAN_CSS_ENGINES")
    return Path(folder) if folder else None


def run(script: Path, name: str, payload: dict, work_dir: Path, timeout: int = 1800) -> tuple[dict | None, dict]:
    """One Node engine over a payload: its JSON output (None when it failed) and the measured run."""
    work_dir.mkdir(parents=True, exist_ok=True)
    settings, output = work_dir / f"{name}.json", work_dir / f"{name}-out.json"
    settings.write_text(json.dumps(payload), encoding="utf-8")
    output.unlink(missing_ok=True)
    node = Path(os.environ["DAODAN_NODE_BIN"]) / "node" if os.environ.get("DAODAN_NODE_BIN") else "node"
    measured = scip_graph.measured([str(node), str(script), str(settings), str(output)], str(work_dir), None, timeout)
    data = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else None
    return data, measured


def engine_index(script: Path, package: str, work_dir: Path, items: list[dict], field: str) -> dict:
    """A pinned engine over items: {"indexer", field: {key: result | {"error"}}}; every item gets an answer."""
    folder = engines()
    if not items:
        return {"indexer": None, field: {}}
    if folder is None or not (folder / package).is_dir():
        return {"indexer": {"name": package, "version": None, "seconds": 0, "peak_mb": None},
                field: {item["key"]: {"error": f"{package} not installed (DAODAN_CSS_ENGINES)"} for item in items}}
    data, measured = run(script, script.stem, {"engines": str(folder), "items": items}, Path(work_dir))
    indexer = {"name": package, "version": data["version"] if data else None, "seconds": measured["seconds"],
               "peak_mb": measured["peak_mb"]}
    if data is None:
        reason = f"the {package} run failed: {measured['stderr_tail'][-300:]}"
        return {"indexer": indexer, field: {item["key"]: {"error": reason} for item in items}}
    return {"indexer": indexer, field: data[field]}


def index(work_dir: Path, items: list[dict]) -> dict:
    """items: [{"key", "path" | "text", "syntax": "scss" | "sass"}] -> {"indexer", "sheets": {key: {tree} | {error}}}."""
    return engine_index(SCRIPT, "sass-parser", work_dir, items, "sheets")
