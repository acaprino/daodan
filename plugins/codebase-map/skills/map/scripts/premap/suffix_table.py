"""Source: the language the snapshot gives each file from its suffix table (`languages.detect_language`).

Totals per language, in Linguist's spelling where Daodan's name has one; a coarser name (`css` covers SCSS,
`markup` a dozen template languages) stays as Daodan writes it. The language of each file stays in the
snapshot. go-enry replaces this source.
"""
from __future__ import annotations

import collections

import snapshot

NAME, VERSION, RANK = "snapshot.py", snapshot.STORE_SCHEMA, "scanner"
NAMES = {"python": "Python", "java": "Java", "javascript": "JavaScript", "typescript": "TypeScript", "sql": "SQL",
         "plsql": "PLSQL", "rust": "Rust", "go": "Go", "kotlin": "Kotlin", "csharp": "C#", "vue": "Vue",
         "svelte": "Svelte", "astro": "Astro", "c": "C", "cpp": "C++", "css": "CSS"}


def run(context) -> dict:
    counts = collections.Counter(header.get("language") for header in context.inventory.headers.values())
    return {"facts": {"languages": [{"language": NAMES.get(name, name), "files": n}
                                    for name, n in sorted((k, v) for k, v in counts.items() if k)]}}
