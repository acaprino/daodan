"""
TypeScript adapter. Builds on the JavaScript adapter's tree walker, which also reads:

- interface declarations (kind="interface")
- enum declarations (kind="enum")
- type alias declarations (kind="type-alias")

A file whose grammar does not load is reported unread (`languages/reading.py`).

The tree-sitter `typescript` grammar handles `.ts`; `tsx` is a separate grammar
that also covers JSX/TSX. We detect TSX via file path suffix when called.
"""

from __future__ import annotations

from ._treesitter import get_parser
from .base import ParseResult
from .comments import CommentToken, extract_c_style_comments
from .reading import code_lines, unread

# NOTE: `javascript` is imported lazily inside the methods/helpers below so a
# TS-only user with a broken JS grammar package does not see TS parsing fail
# at module import time. The chain TS -> JS is intentional code reuse but
# should not be a load-time dependency.

__all__ = ["adapter"]

_LANGUAGE_NAME = "typescript"


def _ts_parse(content: str, is_tsx: bool) -> ParseResult | None:
    from . import javascript as _js  # lazy import; see module docstring

    pair = get_parser("tsx" if is_tsx else "typescript")
    if pair is None:
        return None
    parser, _lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as e:
        # Mirror the Java/JS pattern: surface via the JS holder so
        # _TypeScriptAdapter.parse will annotate notes.
        _js._TS_ERROR_HOLDER["last"] = f"{type(e).__name__}: {e}"
        return None

    # The shared declaration walker reads the same tree for JS/TS constructs,
    # including namespace-qualified members and interface/enum declarations.
    js_result = _js._ts_parse(
        content,
        language="tsx" if is_tsx else _LANGUAGE_NAME,
        pre_parsed=(tree, src),
    )
    if js_result is None:
        return None

    js_result.language = _LANGUAGE_NAME
    # Re-tag parser provenance so downstream display shows TS, not JS.
    js_result.notes = [n.replace("=tree-sitter", "=tree-sitter (ts)") for n in js_result.notes]
    return js_result


class _TypeScriptAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        from . import javascript as _js  # lazy import

        _js._TS_ERROR_HOLDER.pop("last", None)
        is_tsx = file_path.lower().endswith(".tsx")
        result = _ts_parse(content, is_tsx=is_tsx)
        if result is None:
            result = unread(self.language, "tsx" if is_tsx else _LANGUAGE_NAME, _js._TS_ERROR_HOLDER.pop("last", None))
        result.file_path = file_path
        return result

    def strip_comments_and_blanks(self, content: str, file_path: str | None = None) -> int | None:
        """`file_path` tells a `.tsx` file, whose JSX text is no comment, from a `.ts` file."""
        return code_lines(content, "tsx" if (file_path or "").lower().endswith(".tsx") else _LANGUAGE_NAME)

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter = _TypeScriptAdapter()
