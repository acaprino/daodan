"""What a reader reports of a source without reading symbols from it: its lines of code, or that it read nothing.

Both come from the syntax tree. A grammar that does not load gives no tree, and so no count and no symbol: a
declared gap, never a reading by expression (`snapshot.parser_profile` declares the same gap for the snapshot).
"""

from __future__ import annotations

from . import _treesitter
from .base import ParseResult

__all__ = ["code_lines", "is_unread", "unread"]

UNREAD = "parser=none"

# The comment nodes of the grammars Daodan wires: Kotlin names its block comment `multiline_comment`, SQL `marginalia`.
_COMMENTS = _treesitter._COMMENT_NODE_TYPES | {"multiline_comment", "marginalia"}


def code_lines(content: str, grammar: str) -> int | None:
    """The lines of `content` that hold a token outside every comment node of the tree, or None without a tree.

    A line inside a multi-line string counts unless it is blank; a comment opener inside a string is no comment.
    """
    pair = _treesitter.get_parser(grammar)
    if pair is None:
        return None
    source = content.encode("utf-8")
    try:
        root = pair[0].parse(source).root_node
    except Exception:  # parse() is contractually non-raising; a failure is an unknown count, never a guess
        return None
    rows: set[int] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type in _COMMENTS:
            continue
        if node.children:
            stack.extend(node.children)
            continue
        first = node.start_point[0]
        for offset, piece in enumerate(source[node.start_byte:node.end_byte].split(b"\n")):
            if piece.strip():
                rows.add(first + offset)
    return len(rows)


def unread(language: str, grammar: str, error: str | None) -> ParseResult:
    """The result of a file no tree was read from: no symbol, and the reason in its notes.

    `error` is what the grammar raised on this source, None when the grammar did not load at all.
    """
    reason = (f"tree-sitter raised: {error}" if error is not None
              else f"tree-sitter unavailable: {_treesitter.load_failure(grammar) or 'no tree-sitter grammar installed'}")
    return ParseResult(file_path="", language=language, notes=[UNREAD, reason])


def is_unread(result: ParseResult) -> bool:
    """Whether `result` is that of a file no tree was read from."""
    return bool(result.notes) and result.notes[0].startswith(UNREAD)  # a component's reader adds ` (vue)`
