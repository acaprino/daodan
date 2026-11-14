"""Daodan's own detection, the baseline: `detect_language` and the perimeter of `tree_scope.Perimeter`.

Both are imported from the plugin, read only. The perimeter prunes what Git ignores, every dot directory and the
dependency and build directories by name (`vendor`, `node_modules`, `build`, `dist`, `target`, `venv`,
`__pycache__`); it never says why, so the pruned directories and files go to `excluded` without a `why`. Daodan's
language names are its own (`typescript` covers TSX, `css` covers SCSS, Sass and Less, `markup` is a dozen
template languages): they are mapped to Linguist's spelling, and for `css` and `markup` Linguist's name for the
file's extension is used. Where Daodan's vocabulary is coarser than Linguist's, the answer is the coarser one.
The plugin is found through DAODAN_SCRIPTS, else beside this repository.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from _lang import files, read_text, table

VERSION = "main working tree"
SCRIPTS = Path(os.environ.get("DAODAN_SCRIPTS") or Path(__file__).resolve().parents[3] / "plugins/codebase-map/skills/map/scripts")
NAMES = {"python": "Python", "java": "Java", "javascript": "JavaScript", "typescript": "TypeScript", "sql": "SQL",
         "plsql": "PLSQL", "rust": "Rust", "go": "Go", "kotlin": "Kotlin", "csharp": "C#", "vue": "Vue",
         "svelte": "Svelte", "c": "C", "cpp": "C++"}


def _by_extension(extension: str) -> str | None:
    """Linguist's name for an extension: the language that lists it first (`.html` is HTML, not Ecmarkup)."""
    found = [(name, entry.get("extensions") or []) for name, entry in table().items()]
    found = [(name, [e.lower() for e in exts]) for name, exts in found if extension in [e.lower() for e in exts]]
    for name, exts in found:
        if exts[0] == extension:
            return name
    return found[0][0] if found else None


def run(fixture_dir, work_dir) -> dict:
    sys.path.insert(0, str(SCRIPTS))
    from languages import detect_language
    from tree_scope import Perimeter

    base = Path(fixture_dir)
    perimeter = Perimeter(base)
    kept, walked = [], set()
    for here, names in perimeter.walk():
        walked.add(here.relative_to(base).as_posix())
        kept.extend((here / n).relative_to(base).as_posix() for n in names)
    kept_set = set(kept)
    everything = files(base)
    excluded, seen = [], set()
    for path in everything:
        if path in kept_set:
            continue
        parts = path.split("/")
        top = None
        for depth in range(1, len(parts)):
            folder = "/".join(parts[:depth])
            if folder not in walked and folder != ".":
                top = folder + "/"
                break
        entry = top or path
        if entry not in seen:
            seen.add(entry)
            excluded.append({"path": entry})
    languages = []
    for path in kept:
        canonical = detect_language(Path(path), read_text(base, path))
        if canonical is None:
            continue
        name = NAMES.get(canonical) or _by_extension(Path(path).suffix.lower())
        if name:
            languages.append({"path": path, "language": name})
    return {"languages": languages, "excluded": excluded,
            "_raw": {"pruned": len(everything) - len(kept), "git_ignore": perimeter.git_ignore}}
