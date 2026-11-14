"""Svelte's own compiler over components, for the CSS graph (`css_svelte.js`).

`svelte/compiler`'s modern tree gives every `class`, `class={...}`, `class:name` and `id` of the markup; the style
block is scoped by default, `:global` and `<style global>` global, and is read by the sheet reader of its dialect.
Pinned in `css_engines.json`.
"""
from __future__ import annotations

from pathlib import Path

from . import css_sass

SUFFIXES = (".svelte",)
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def index(work_dir: Path, items: list[dict]) -> dict:
    """items: [{"key", "path"}] -> {"indexer", "components": {key: {blocks, classes, ...} | {error}}}."""
    return css_sass.engine_index(SCRIPT, "svelte", work_dir, items, "components")
