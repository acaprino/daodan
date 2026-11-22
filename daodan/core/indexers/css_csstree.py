"""The ESLint fork of CSSTree over plain CSS, for the stylesheet graph (`css_csstree.js`).

`@eslint/css-tree` is the CSSTree parser the ESLint CSS language plugin reads with: the CSS grammars of the
specifications, relaxed nesting, `@layer`, `@container`, `@scope`, `@import ... layer() supports()`, `Raw` for what its
grammar does not read, and `mdn-data`'s lexer for what a value names (keyframes, font families, container names). It is
pinned in `css_engines/`. `index` parses each sheet, a file or a text (a `<style>` block, a style attribute), into the
neutral tree `css.tree_records` reads: facts of the tree and the lexer, never the parser's own tree. What the parser
keeps as Raw is a `hole` node of that tree, and a text it cannot parse is `{"error"}`: a file in `files.missing`.
"""
from __future__ import annotations

from pathlib import Path

from . import css_sass

SUFFIXES = (".css", ".pcss", ".postcss")
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def index(runner, items: list[dict]) -> dict:
    """items: [{"key", "path" | "text", "kind", "words", "svelte"}] -> {"indexer", "sheets": {key: {tree} | {error}}}."""
    return css_sass.engine_index(runner, SCRIPT, "@eslint/css-tree", items, "sheets")
