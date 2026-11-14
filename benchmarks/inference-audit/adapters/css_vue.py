"""Vue's own compiler over single-file components, for the CSS graph (`css_vue.js`).

`@vue/compiler-sfc` is the compiler Vue builds with: its descriptor gives every style block with `lang`, `scoped` and
`module`, its template tree every `class`, `:class`, `v-bind:class` and `id`, and `compileScript` the script's
bindings. The style blocks are read by the sheet readers of their dialect; the class expressions by
`css_expressions.js`. Pinned in `css_engines.json`.
"""
from __future__ import annotations

from pathlib import Path

from . import css_sass

SUFFIXES = (".vue",)
SCRIPT = Path(__file__).resolve().with_suffix(".js")


def index(work_dir: Path, items: list[dict]) -> dict:
    """items: [{"key", "path"}] -> {"indexer", "components": {key: {blocks, classes, ...} | {error}}}."""
    return css_sass.engine_index(SCRIPT, "@vue/compiler-sfc", work_dir, items, "components")
