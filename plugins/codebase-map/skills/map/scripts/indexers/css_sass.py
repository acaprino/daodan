"""The official Sass parser over SCSS and indented Sass, for the stylesheet graph (`css_sass.js`).

`sass-parser` is the Sass team's PostCSS-compatible wrapper of Dart Sass's own parser: the same grammar the compiler
reads, for both syntaxes, with `@use`, `@forward` (prefix, show, hide), variables and their flags, mixins, functions,
`@include` with content blocks, `@extend`, control flow and every expression as a tree. It is pinned in
`css_engines/`. `index` parses each sheet, a file or a text (a `<style lang="scss">` block), into the neutral tree
`css.tree_records` reads.

Every engine adapter runs its script through the `runner` the stage supplies (`css.run`): `runner(script, payload)`
runs `node <script> IN OUT` in the project's directory, IN being the payload with `engines` added, the folder of the
installed `css_engines/` packages, and returns `(OUT as data or None, {"seconds", "peak_mb", "stderr_tail"})`.
"""
from __future__ import annotations

from pathlib import Path

SUFFIXES = (".scss", ".sass")
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def engine_index(runner, script: Path, package: str, items: list[dict], field: str) -> dict:
    """A pinned engine over items: {"indexer", field: {key: result | {"error"}}}; every item gets an answer."""
    if not items:
        return {"indexer": None, field: {}}
    data, measured = runner(script, {"items": items})
    indexer = {"name": package, "version": data["version"] if data else None, "seconds": measured.get("seconds"),
               "peak_mb": measured.get("peak_mb")}
    if data is None:
        reason = f"the {package} run failed: {(measured.get('stderr_tail') or '')[-300:]}"
        return {"indexer": indexer, field: {item["key"]: {"error": reason} for item in items}}
    return {"indexer": indexer, field: data[field]}


def index(runner, items: list[dict]) -> dict:
    """items: [{"key", "path" | "text", "syntax": "scss" | "sass"}] -> {"indexer", "sheets": {key: {tree} | {error}}}."""
    return engine_index(runner, SCRIPT, "sass-parser", items, "sheets")
