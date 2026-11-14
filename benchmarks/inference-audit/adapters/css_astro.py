"""Astro's own compiler over `.astro` files, for the CSS graph (`css_astro.js`).

`@astrojs/compiler` gives the elements, their attributes (`class`, `class:list`, `id`, with expressions as text, read
with acorn) and the style blocks: scoped by default, `is:global` and `is:inline` global, `define:vars` keys declared
as custom properties. Pinned in `css_engines.json`.
"""
from __future__ import annotations

from pathlib import Path

from . import css_sass

SUFFIXES = (".astro",)
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def index(work_dir: Path, items: list[dict]) -> dict:
    """items: [{"key", "path"}] -> {"indexer", "components": {key: {blocks, classes, ...} | {error}}}."""
    return css_sass.engine_index(SCRIPT, "@astrojs/compiler", work_dir, items, "components")
