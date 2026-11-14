"""Stylus's own parser over Stylus sheets, for the CSS graph (`css_stylus.js`).

`stylus` is the reference implementation (0.64.0, maintained at a slow pace; the only Stylus parser there is). Its
tree gives selectors with their `{x}` interpolations, properties, variables (no sigil: a word in a value is a
reference only where a variable of that name exists), mixins and functions with parameters, mixin calls written as
calls or as properties, `@extend`, `@import`/`@require`, `for` loops, `if`/`unless`, `@media` and `@keyframes`,
without evaluating anything. Pinned in `css_engines.json`.
"""
from __future__ import annotations

from pathlib import Path

from . import css_sass

SUFFIXES = (".styl", ".stylus")
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def index(work_dir: Path, items: list[dict]) -> dict:
    """items: [{"key", "path" | "text"}] -> {"indexer", "sheets": {key: {tree} | {error}}}."""
    return css_sass.engine_index(SCRIPT, "stylus", work_dir, items, "sheets")
