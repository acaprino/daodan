"""
Single-File Component (Vue `.vue` and Svelte `.svelte`) adapter.

Masks everything outside `<script ...>...</script>` blocks with spaces while
preserving exact UTF-8 byte offsets and line numbers, then delegates script
parsing to the TypeScript or JavaScript adapter so `ParseResult.semantic` spans
align 1:1 with the original `.vue` or `.svelte` file on disk. The rules of the
`<style>` blocks are added beside the script's symbols (`markup.style_symbols`).
"""

from __future__ import annotations

import re

from .base import ParseResult
from .comments import CommentToken, extract_c_style_comments

__all__ = ["vue_adapter", "svelte_adapter", "mask_non_script"]

_SCRIPT_BLOCK_RE = re.compile(
    rb"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_TS_ATTR_RE = re.compile(
    rb"""\blang\s*=\s*['"]?(?:ts|tsx|typescript)\b""",
    re.IGNORECASE,
)


def mask_non_script(content: str) -> tuple[str, bool, bool]:
    """Return `(masked_source, is_typescript, has_script)` with identical byte offsets per line."""
    raw = content.encode("utf-8")
    masked = bytearray(len(raw))
    for i, b in enumerate(raw):
        masked[i] = b if b in (0x0A, 0x0D) else 0x20

    is_ts = False
    has_script = False
    for match in _SCRIPT_BLOCK_RE.finditer(raw):
        has_script = True
        if _TS_ATTR_RE.search(match.group("attrs") or b""):
            is_ts = True
        start, end = match.span("body")
        masked[start:end] = raw[start:end]

    return masked.decode("utf-8", errors="replace"), is_ts, has_script


class _SfcAdapter:
    def __init__(self, language: str) -> None:
        self.language = language

    def parse(self, content: str, file_path: str) -> ParseResult:
        from .markup import style_symbols

        result = self._script(content, file_path)
        style_symbols(content, result)
        return result

    def _script(self, content: str, file_path: str) -> ParseResult:
        from . import javascript as _js
        from . import typescript as _ts

        masked, is_ts, has_script = mask_non_script(content)
        if not has_script:
            return ParseResult(
                file_path=file_path,
                language=self.language,
                notes=[f"parser=sfc-no-script ({self.language})"],
                semantic={
                    "version": 1,
                    "backend": "tree-sitter",
                    "status": "ast",
                    "notes": [],
                    "scopes": [{"id": "module", "parent": None, "kind": "module"}],
                    "declarations": [],
                    "imports": [],
                    "exports": [],
                    "references": [],
                },
            )

        delegate = _ts.adapter if is_ts else _js.adapter
        virtual_ext = ".ts" if is_ts else ".js"
        result = delegate.parse(masked, file_path + virtual_ext)
        result.file_path = file_path
        result.language = self.language
        result.notes = [f"{n} ({self.language})" for n in result.notes]
        return result

    def count_imports(self, content: str) -> int:
        from . import javascript as _js

        masked, _, has_script = mask_non_script(content)
        return _js.adapter.count_imports(masked) if has_script else 0

    def extract_comments(self, content: str) -> list[CommentToken]:
        masked, _, has_script = mask_non_script(content)
        return extract_c_style_comments(masked) if has_script else []


vue_adapter = _SfcAdapter("vue")
svelte_adapter = _SfcAdapter("svelte")
