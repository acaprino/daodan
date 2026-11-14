"""Less's own parser over Less sheets, for the CSS graph (`css_less.js`).

`less` is the reference implementation; its parser gives variables at every level (`@x`, `@@x`), detached rulesets,
mixin definitions with parameters and guards, mixin calls with and without parentheses and through namespaces,
`:extend`, `@import` with its options and `@plugin`, without evaluating anything (no plugin runs). It is pinned in
`css_engines.json`. `index` parses each sheet, a file or a text (a `<style lang="less">` block), into the neutral
tree `css.tree_records` reads.
"""
from __future__ import annotations

from pathlib import Path

from . import css_sass

SUFFIXES = (".less",)
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def index(work_dir: Path, items: list[dict]) -> dict:
    """items: [{"key", "path" | "text"}] -> {"indexer", "sheets": {key: {tree} | {error}}}."""
    return css_sass.engine_index(SCRIPT, "less", work_dir, items, "sheets")
