"""
Style blocks of markup: the rules of every `<style>` element in HTML, template
languages, Astro, Vue and Svelte files.

A rule written in a page's `<style>` styles the screen as one in a `.css` file
does, so it is a symbol with its exact span. Each block is read by the
stylesheet adapter in its own dialect (`lang="scss"`, `"sass"`, `"less"`,
`"postcss"`; plain CSS otherwise), with everything outside it blanked so lines
stay those of the file. A block in a dialect the product has no reader for
(Stylus) is named in the notes, never skipped silently. Nothing else of the
markup is read here: class attributes are usages, not symbols.
"""

from __future__ import annotations

import re
from collections import Counter

from .base import ParseResult
from .comments import CommentToken

__all__ = ["adapter", "style_blocks", "style_symbols"]

_LANGUAGE_NAME = "markup"
_STYLE_RE = re.compile(r"<style\b(?P<attrs>[^>]*)>(?P<body>.*?)</style\s*>", re.IGNORECASE | re.DOTALL)
_LANG_RE = re.compile(r"""\b(?:lang|type)\s*=\s*['"]?(?:text/)?([\w-]+)""", re.IGNORECASE)
_DIALECTS = {"css": "css", "postcss": "css", "pcss": "css", "scss": "scss", "sass": "sass", "less": "less"}
_UNREAD = {"stylus": "no Stylus reader in the product", "styl": "no Stylus reader in the product"}


def style_blocks(content: str) -> list[tuple[str | None, int, str, str]]:
    """(dialect or None, first line, the file blanked outside the block, lang) for every `<style>` element."""
    blocks = []
    for match in _STYLE_RE.finditer(content):
        lang = _LANG_RE.search(match.group("attrs") or "")
        name = lang.group(1).lower() if lang else "css"
        start, end = match.span("body")
        masked = "".join(ch if ch == "\n" else " " for ch in content[:start]) + content[start:end]
        blocks.append((_DIALECTS.get(name, "css" if name not in _UNREAD else None),
                       content.count("\n", 0, match.start()) + 1, masked, name))
    return blocks


def style_symbols(content: str, result: ParseResult) -> None:
    """Add the rules, variables and mixins of the file's style blocks to a parse result, with their notes."""
    from .stylesheet import adapter as sheets

    dialects = []
    for dialect, line, masked, name in style_blocks(content):
        if dialect is None:
            result.notes.append(f"style block at line {line} not read: {_UNREAD[name]}")
            continue
        block = sheets.parse(masked, f"style.{dialect}")
        result.classes.extend(block.classes)
        result.functions.extend(block.functions)
        result.constants.extend(name for name in block.constants if name not in result.constants)
        result.exported_symbols.extend(name for name in block.exported_symbols if name not in result.exported_symbols)
        if dialect not in dialects:
            dialects.append(dialect)
    if dialects:
        result.notes.append(f"style blocks: stylesheet ({', '.join(dialects)})")
    # A rule repeated across blocks keeps one symbol per occurrence, as in one sheet.
    seen: Counter[str] = Counter()
    names = {info.name for info in result.classes}
    for info in sorted(result.classes, key=lambda item: item.line_number):
        raw = info.name
        seen[raw] += 1
        if seen[raw] > 1:
            number = seen[raw]
            while f"{raw} ({number})" in names:
                number += 1
            info.name = f"{raw} ({number})"
            names.add(info.name)


class _MarkupAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        result = ParseResult(file_path=file_path, language=self.language, notes=["parser=markup (style blocks)"])
        style_symbols(content, result)
        return result

    def count_imports(self, content: str, file_path: str | None = None) -> int:
        return 0

    def extract_comments(self, content: str, file_path: str | None = None) -> list[CommentToken]:
        from .stylesheet import adapter as sheets

        found: list[CommentToken] = []
        for dialect, _, masked, _ in style_blocks(content):
            if dialect is not None:
                found += sheets.extract_comments(masked, f"style.{dialect}")
        return found


adapter = _MarkupAdapter()
