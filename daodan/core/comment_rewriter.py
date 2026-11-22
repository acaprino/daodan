"""
Comment Rewriter Module.

Analyzes and rewrites code comments following antirez commenting standards:
https://antirez.com/news/124

Comment Types (antirez taxonomy):

GOOD (to keep/enhance):
  1. Function Comments - API docs at function/class top (docstrings, Javadoc,
     JSDoc, SQL header blocks)
  2. Design Comments  - File-level, explain algorithms and design choices
  3. Why Comments     - Explain reasoning, not what the code does
  4. Teacher Comments - Educate about domain knowledge (math, protocols)
  5. Checklist Comments - Remind of coordinated changes elsewhere
  6. Guide Comments   - Lower cognitive load through rhythm and divisions

BAD (to remove/rewrite):
  7. Trivial Comments - Obvious statements (i++; // Increment i)
  8. Debt Comments    - TODO/FIXME that should be resolved or documented
  9. Backup Comments  - Commented-out code (use git history instead)

Multi-language: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust. Stylesheets
(CSS, SCSS, LESS) are analyzed and never rewritten.

Source is read from the syntax tree, never with expressions (AGENTS.md): the tree gives the comments, says whether a
comment body is code (it parses clean as a statement that does something) and which code a trailing comment
restates (the nodes starting on its line). Where the grammar does not load nothing is guessed: the file is left
alone and the analysis says so. A comment's own prose (debt, checklist, why words) has no grammar and is read
with words. The other languages are read through languages.<lang>.adapter.extract_comments() and
classified by their prose alone.
"""

from __future__ import annotations

import logging
import re
import textwrap
from bisect import bisect_left
from dataclasses import dataclass, field
from enum import Enum
from itertools import takewhile
from pathlib import Path
from typing import Any

from languages import _treesitter, detect_language, get_adapter
from languages.comments import COMMENT_NODES, CommentToken, tree_comments
from source_files import MAX_PARSE_BYTES

__all__ = [
    "CommentType",
    "CommentClassification",
    "CommentInfo",
    "CommentAnalysis",
    "CommentRewriter",
    "CommentRewriterError",
    "analyze_comments",
    "rewrite_file",
]

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_ISSUES_IN_REPORT = 20
MAX_COMMENTS_PER_SECTION = 10

# Single source of truth: keep in sync with `languages.SUPPORTED_EXTENSIONS`.
from languages import SUPPORTED_EXTENSIONS as _SUPPORTED_EXTENSIONS_MAP

SUPPORTED_SUFFIXES = frozenset(_SUPPORTED_EXTENSIONS_MAP.keys())


class CommentRewriterError(Exception):
    """Base exception for comment rewriter errors."""


class CommentType(Enum):
    FUNCTION = "function"
    DESIGN = "design"
    WHY = "why"
    TEACHER = "teacher"
    CHECKLIST = "checklist"
    GUIDE = "guide"
    TRIVIAL = "trivial"
    DEBT = "debt"
    BACKUP = "backup"
    DIRECTIVE = "directive"
    UNKNOWN = "unknown"


class CommentClassification(Enum):
    KEEP = "keep"
    ENHANCE = "enhance"
    REWRITE = "rewrite"
    DELETE = "delete"


@dataclass
class CommentInfo:
    line_number: int
    column: int
    text: str
    raw_text: str
    is_docstring: bool
    is_inline: bool
    is_block: bool
    is_doc_block: bool
    comment_type: CommentType
    classification: CommentClassification
    reason: str
    suggestion: str | None = None


@dataclass
class CommentAnalysis:
    file_path: str
    language: str
    total_comments: int
    total_lines: int
    comment_ratio: float
    comments: list[CommentInfo] = field(default_factory=list)
    by_type: dict[str, int] = field(default_factory=dict)
    by_classification: dict[str, int] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    # Why the file's grammar could not read it: commented-out code and restated lines were then not looked for.
    gap: str | None = None


# ---------------------------------------------------------------------------
# Pattern bank (language-agnostic where possible, language-aware where needed).
# ---------------------------------------------------------------------------

_DEBT_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\bXXX\b", re.IGNORECASE),
    re.compile(r"\bHACK\b", re.IGNORECASE),
    re.compile(r"\bBUG\b", re.IGNORECASE),
    re.compile(r"\bWORKAROUND\b", re.IGNORECASE),
    re.compile(r"\bTEMP\b", re.IGNORECASE),
    re.compile(r"\bTEMPORARY\b", re.IGNORECASE),
]

_CHECKLIST_PATTERNS = [
    re.compile(r"\bif you (?:change|modify|update)\b", re.IGNORECASE),
    re.compile(r"\bremember to\b", re.IGNORECASE),
    re.compile(r"\bdon'?t forget\b", re.IGNORECASE),
    re.compile(r"\balso update\b", re.IGNORECASE),
    re.compile(r"\bmust be kept in sync\b", re.IGNORECASE),
    re.compile(r"\bsee also\b", re.IGNORECASE),
    re.compile(r"\bwhen changing\b", re.IGNORECASE),
]

_WHY_PATTERNS = [
    re.compile(r"\bbecause\b", re.IGNORECASE),
    re.compile(r"\bthe reason\b", re.IGNORECASE),
    re.compile(r"\bwe (?:do|use) this\b", re.IGNORECASE),
    re.compile(r"\bthis is (?:necessary|needed|required)\b", re.IGNORECASE),
    re.compile(r"\bto avoid\b", re.IGNORECASE),
    re.compile(r"\bto prevent\b", re.IGNORECASE),
    re.compile(r"\bworkaround for\b", re.IGNORECASE),
    re.compile(r"\bdue to\b", re.IGNORECASE),
    re.compile(r"\brequired by\b", re.IGNORECASE),
    re.compile(r"\bhistorically\b", re.IGNORECASE),
]

_TEACHER_PATTERNS = [
    re.compile(r"\balgorithm\b", re.IGNORECASE),
    re.compile(r"\bprotocol\b", re.IGNORECASE),
    re.compile(r"\bformula\b", re.IGNORECASE),
    re.compile(r"\bequation\b", re.IGNORECASE),
    re.compile(r"\btheorem\b", re.IGNORECASE),
    re.compile(r"\bRFC\s*\d+\b", re.IGNORECASE),
    re.compile(r"\bsee (?:http|https)://\b", re.IGNORECASE),
    re.compile(r"\brefer to\b", re.IGNORECASE),
    re.compile(r"\bexplained in\b", re.IGNORECASE),
]

_GUIDE_PATTERNS = [
    re.compile(r"^[\s]*[-=]+[\s]*$"),
    re.compile(r"^[\s]*#+ "),
    re.compile(r"^\s*section\s*:?\s*", re.IGNORECASE),
    re.compile(r"^[\s]*[/*]+ "),
]

# The languages whose comments are read against the syntax tree of the file: whether a comment is commented-out code,
# and which code a trailing comment restates, are questions for the grammar. The other languages (Go, Kotlin, C#, C,
# C++, the single-file components, markup, stylesheets) were never read as code and are not now.
_READ_AS_CODE = frozenset({"python", "java", "javascript", "typescript", "sql", "plsql", "rust"})

# The nodes of a clean parse that do something: a comment body with one at its top level is code. What parses clean as
# prose (a lone name, `a.b`, `yes or no`, a labeled statement, `Note: retry`, `--- reads ---`) has none of them.
# `_NEEDS_FIELD`: a node counts only with the field it names (`x: int` is an annotation, `new thing` a name).
# `_LITERALS`: a call whose callee is one is no call (a name and a quotation in backticks parse as a tagged template).
_DOES_SOMETHING = frozenset({
    # python
    "assignment", "augmented_assignment", "call", "await", "yield", "import_statement", "import_from_statement",
    "future_import_statement", "if_statement", "for_statement", "while_statement", "try_statement", "with_statement",
    "match_statement", "function_definition", "class_definition", "decorated_definition", "return_statement",
    "raise_statement", "assert_statement", "delete_statement", "global_statement", "nonlocal_statement",
    # javascript and typescript
    "lexical_declaration", "variable_declaration", "assignment_expression", "augmented_assignment_expression",
    "call_expression", "new_expression", "await_expression", "yield_expression",
    "export_statement", "for_in_statement", "do_statement", "switch_statement", "throw_statement",
    "function_declaration", "generator_function_declaration", "class_declaration", "abstract_class_declaration",
    "interface_declaration", "type_alias_declaration", "enum_declaration",
    # java
    "local_variable_declaration", "method_invocation", "object_creation_expression", "import_declaration",
    "package_declaration", "enhanced_for_statement", "try_with_resources_statement", "method_declaration",
    "constructor_declaration", "field_declaration", "record_declaration",
    # rust
    "let_declaration", "macro_invocation", "compound_assignment_expr", "use_declaration", "function_item",
    "struct_item", "enum_item", "impl_item", "trait_item", "mod_item", "const_item", "static_item", "type_item",
    "return_expression", "if_expression", "for_expression", "while_expression", "loop_expression",
    "match_expression", "unsafe_block", "attribute_item",
    # sql
    "statement",
})
_NEEDS_FIELD = {"assignment": "right", "new_expression": "arguments"}
# `cython: language_level=3`, `vim: ts=4` and `TODO: retries = 3` parse as an annotated assignment, which a tool or a
# note writes far more often than a program does: an assignment with a type annotation is not commented-out code.
_NOT_WITH_FIELD = {"assignment": "type"}
_LITERALS = frozenset({"template_string", "string", "number", "regex", "true", "false", "null"})

# What a trailing comment says in its first word, and the nodes (or operator tokens) of its line that say it too.
_STEPS = {"increment": frozenset({"++", "+="}), "decrement": frozenset({"--", "-="})}
_RESTATES: dict[str, dict[str, frozenset[str]]] = {
    "python": {
        **_STEPS,
        "return": frozenset({"return_statement"}),
        "loop": frozenset({"for_statement", "while_statement", "for_in_clause"}),
        "import": frozenset({"import_statement", "import_from_statement", "future_import_statement"}),
        "set": frozenset({"="}),
        "call": frozenset({"call"}),
        "if": frozenset({"if_statement"}),
    },
    "java": {
        **_STEPS,
        "return": frozenset({"return_statement"}),
        "loop": frozenset({"for_statement", "enhanced_for_statement", "while_statement"}),
        "set": frozenset({"="}),
        "new": frozenset({"object_creation_expression"}),
    },
    "javascript": {
        **_STEPS,
        "return": frozenset({"return_statement"}),
        "loop": frozenset({"for_statement", "for_in_statement", "while_statement"}),
        "import": frozenset({"import_statement"}),
    },
    "rust": {
        "increment": frozenset({"+="}),
        "decrement": frozenset({"-="}),
        "return": frozenset({"return_expression"}),
        "loop": frozenset({"for_expression", "while_expression", "loop_expression"}),
        "use": frozenset({"use_declaration"}),
        "match": frozenset({"match_expression"}),
    },
    "sql": {name: frozenset({name}) for name in ("select", "insert", "update", "delete")},
}
_RESTATES["typescript"] = _RESTATES["javascript"]

# A comment is an extra to every parser, so no grammar tells a tool directive from prose: the names the tools read are
# data. They are looked for anywhere in the lowercased body: a comment kept by mistake costs one line, a directive
# deleted changes what the compiler or linter does. A body that opens with `+` is a SQL hint, with `!` a shebang.
_DIRECTIVES = (
    "@ts-", "eslint", "tslint", "biome-ignore", "prettier-ignore", "istanbul", "c8 ignore", "v8 ignore", "@vite-ignore",
    "webpackchunkname", "@flow", "@jsx", "@license", "@preserve", "sourcemappingurl", "<reference", "#__pure__",
    "@__pure__", "noqa", "type: ignore", "pylint:", "mypy:", "pyright:", "flake8:", "ruff:", "isort:", "fmt: ",
    "nosec", "pragma", "coding:", "coding=", "nopmd", "checkstyle", "noinspection", "@formatter", "rustfmt",
    "clippy", "sqlfluff", "nolint", "#region", "#endregion", "editor-fold", "language=", "vim:", "-*-", "cython:", "pytype:", "pyre-",
)
_DIRECTIVE_OPENERS = ("+", "!")

_DEBT_REMOVAL_PATTERN = re.compile(
    r"\b(?:TODO|FIXME|XXX|HACK|BUG|WORKAROUND|TEMP|TEMPORARY)\b:?\s*",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Validation.
# ---------------------------------------------------------------------------


def _validate_source_file(file_path: Path) -> str:
    """Validate the file and return its detected language."""
    if not file_path.exists():
        raise CommentRewriterError(f"File does not exist: {file_path}")
    if not file_path.is_file():
        raise CommentRewriterError(f"Path is not a file: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise CommentRewriterError(
            f"Unsupported file extension {file_path.suffix!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_SUFFIXES))}"
        )
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise CommentRewriterError(
            f"File too large: {file_size:,} bytes (max {MAX_FILE_SIZE_BYTES:,} bytes)"
        )
    content_for_detect = ""
    try:
        # Read just enough to detect PL/SQL via content. Small read is cheap.
        with file_path.open("rb") as fh:
            content_for_detect = fh.read(16 * 1024).decode("utf-8", errors="ignore")
    except OSError:
        pass
    lang = detect_language(file_path, content_for_detect)
    if lang is None:
        raise CommentRewriterError(f"Could not detect language for: {file_path}")
    return lang


def _read_preserving_newlines(path: Path) -> tuple[str, str, bool]:
    """
    Read a source file without letting Python normalize its line endings.

    Returns (content, newline, ends_with_newline) where `content` uses "\\n"
    throughout (what the analysis code expects) and the other two carry the
    information needed to write the file back in its original shape. Reading
    through `read_text` would collapse CRLF to LF and lose the distinction,
    which is how a rewrite of one comment ends up re-encoding every line of a
    LF file checked out on Windows.
    """
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except UnicodeDecodeError:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            raw = fh.read()

    if "\r\n" in raw:
        newline = "\r\n"
    elif "\r" in raw:
        newline = "\r"
    else:
        newline = "\n"

    content = raw.replace("\r\n", "\n").replace("\r", "\n")
    return content, newline, raw.endswith(("\n", "\r"))


def _write_preserving_newlines(path: Path, text: str, newline: str) -> None:
    """Write `text` (LF-separated) using `newline` verbatim, no translation."""
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text if newline == "\n" else text.replace("\n", newline))


def _validate_output_path(output_path: Path, source_path: Path) -> Path:
    resolved = output_path.resolve()
    if resolved.exists() and not resolved.is_file():
        raise CommentRewriterError(f"Output path exists but is not a file: {resolved}")
    if not resolved.parent.exists():
        raise CommentRewriterError(f"Output directory does not exist: {resolved.parent}")
    return resolved


# A formatter reads the project's configuration, which can be code (prettier.config.js and its plugins), and the
# project's code runs only in Daodan's container (AGENTS.md): the rewrite leaves formatting to the user.
FORMAT_UNDONE = ("Formatting left undone: a formatter runs the project's configuration (prettier.config.js, its "
                 "plugins), and Daodan runs no project code outside its container")


# ---------------------------------------------------------------------------
# Reading the syntax tree.
# ---------------------------------------------------------------------------


def _is_directive(text_lower: str) -> bool:
    return text_lower.startswith(_DIRECTIVE_OPENERS) or any(name in text_lower for name in _DIRECTIVES)


def _first_word(text: str) -> str:
    return "".join(takewhile(lambda ch: ch.isalnum() or ch == "_", text.lower()))


def _is_statement(node: Any) -> bool:
    """Whether `node` is a statement that does something (see `_DOES_SOMETHING`)."""
    if node.type not in _DOES_SOMETHING:
        return False
    field = _NEEDS_FIELD.get(node.type)
    if field is not None and node.child_by_field_name(field) is None:
        return False
    barred = _NOT_WITH_FIELD.get(node.type)
    if barred is not None and node.child_by_field_name(barred) is not None:
        return False
    if node.type == "call_expression":  # a template literal is no callee, and ``Swift `repos[0]` `` is a tag, not a call
        callee, arguments = node.child_by_field_name("function"), node.child_by_field_name("arguments")
        return callee is not None and callee.type not in _LITERALS and (
            arguments is None or arguments.type != "template_string"
        )
    return True


def _statement_rows(root: Any) -> set[int]:
    """The rows of the parsed body that hold a statement that does something, at the top level, where JavaScript,
    Java and Rust wrap an expression in its `expression_statement`. A call inside a sum is no statement."""
    rows: set[int] = set()
    for top in root.children:
        node = next(iter(top.named_children), top) if top.type == "expression_statement" else top
        if _is_statement(node):
            rows.update(range(top.start_point[0], top.end_point[0] + 1))
    return rows


def _nodes_by_row(root: Any, rows: set[int]) -> dict[int, list[Any]]:
    """The nodes that start on each of `rows`, comments left out. A region the grammar could not read (an ERROR
    node) gives none: what the code on its lines is cannot be said from it."""
    wanted = sorted(rows)
    found: dict[int, list[Any]] = {row: [] for row in wanted}
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type in COMMENT_NODES or node.type == "ERROR":
            continue
        first, last = node.start_point[0], node.end_point[0]
        at = bisect_left(wanted, first)
        if at == len(wanted) or wanted[at] > last:
            continue
        if first in found:
            found[first].append(node)
        stack.extend(node.children)
    return found


def _units(tokens: list[CommentToken]) -> list[list[CommentToken]]:
    """The comments a commented-out block is read in: a run of stand-alone line comments on consecutive lines of
    one column, or one trailing comment. Block comments and doc comments are never code."""
    units: list[list[CommentToken]] = []
    run: list[CommentToken] = []
    for token in tokens:
        if token.is_block or token.is_doc_block:
            run = []
        elif token.is_inline:
            units.append([token])
            run = []
        elif run and run[-1].line_number + 1 == token.line_number and run[-1].column == token.column:
            run.append(token)
        else:
            run = [token]
            units.append(run)
    return units


class _Reading:
    """A file's syntax tree and what it says of the comments in it."""

    def __init__(self, parser: Any, source: bytes, language: str) -> None:
        self._parser = parser
        self._language = language
        root = parser.parse(source).root_node
        self.tokens = tree_comments(root, source)
        self.code = self._commented_out_code()
        self._rows = _nodes_by_row(
            root, {t.line_number - 1 for t in self.tokens if t.is_inline and not t.is_block}
        )

    @classmethod
    def open(cls, content: str, language: str, file_path: str) -> _Reading | str:
        """The reading of `content`, or why its grammar could not read it."""
        # A `.tsx` file is the TypeScript the `typescript` grammar does not read: JSX has a grammar of its own.
        grammar = "tsx" if language == "typescript" and file_path.lower().endswith(".tsx") else language
        pair = _treesitter.get_parser(grammar)
        if pair is None:
            reason = _treesitter.load_failure(grammar)
            return f"the {language} grammar is not available" + (f" ({reason})" if reason else "")
        source = content.encode("utf-8")
        if len(source) > MAX_PARSE_BYTES:  # the snapshot parses no source above this size either
            return f"the file exceeds the parsing size limit ({MAX_PARSE_BYTES:,} bytes)"
        return cls(pair[0], source, language)

    def _commented_out_code(self) -> set[tuple[int, int]]:
        """The (line, column) of the comments that are code: the rows of a unit that parses clean that hold a
        statement doing something, or else each comment that does alone. A line of a clean unit that no such
        statement holds (`TODO: re-enable` above `check(x)`) is prose and stays."""
        code: set[tuple[int, int]] = set()
        for unit in _units(self.tokens):
            rows = self._code_rows(unit)
            if rows is None and len(unit) > 1:
                rows = {at for at, token in enumerate(unit) if self._code_rows([token])}
            code.update((unit[at].line_number, unit[at].column) for at in rows or ())
        return code

    def _code_rows(self, unit: list[CommentToken]) -> set[int] | None:
        """The rows of `unit` that are code, its body parsed with the grammar of the file; None if it parses with an
        error."""
        marker = _line_marker_for(self._language)
        lines = textwrap.dedent("\n".join(t.raw_text.removeprefix(marker) for t in unit)).split("\n")
        root = self._parser.parse("\n".join(lines).encode("utf-8")).root_node
        if root.has_error:
            return None
        rows = _statement_rows(root)
        if rows:  # a bare `#` between two statements goes with them
            rows |= {at for at in range(min(rows), max(rows)) if not lines[at].strip()}
        return rows

    def restates(self, token: CommentToken) -> bool:
        """Whether a trailing comment opens with the word of a node that starts on its line: the code says it."""
        if not token.is_inline or token.is_block:
            return False
        word = _first_word(token.text)
        types = _RESTATES.get(self._language, {}).get(word)
        if not types:
            return False
        nodes = self._rows.get(token.line_number - 1, [])
        return any(node.type in types for node in nodes) or (word == "import" and any(self._requires(n) for n in nodes))

    def _requires(self, node: Any) -> bool:
        """A call of `require`: CommonJS's spelling of an import."""
        callee = node.child_by_field_name("function") if node.type == "call_expression" else None
        return callee is not None and callee.type == "identifier" and callee.text == b"require"


# ---------------------------------------------------------------------------
# Classification.
# ---------------------------------------------------------------------------


def classify_comment(
    token: CommentToken,
    language: str,
    reading: _Reading | None = None,
) -> tuple[CommentType, CommentClassification, str]:
    """
    Classify a comment according to antirez taxonomy.

    Doc blocks (JSDoc / Javadoc) and Python docstrings are treated as
    "function" comments. SQL header blocks (/* ... */ at file start, or
    long top-level block comments) are treated as "design". `reading` is the
    file's syntax tree: without it no comment is judged to be code or to
    restate its line.
    """
    text = token.text
    text_lower = text.lower()

    # Doc blocks (Javadoc /**, JSDoc /**) - treat as function docs.
    if token.is_doc_block:
        if len(text) < 10:
            return (
                CommentType.FUNCTION,
                CommentClassification.ENHANCE,
                "Doc block too brief - needs more detail",
            )
        return (
            CommentType.FUNCTION,
            CommentClassification.KEEP,
            "Doc block provides API documentation",
        )

    # A tool reads it: never code, never trivial, never touched.
    if _is_directive(text_lower):
        return (
            CommentType.DIRECTIVE,
            CommentClassification.KEEP,
            "Tool directive - a compiler or linter reads it",
        )

    # Backup (commented-out code).
    if reading is not None and (token.line_number, token.column) in reading.code and not any(
        pattern.match(text) for pattern in _DEBT_PATTERNS
    ):  # a comment that opens with a debt marker is debt, whatever it parses as
        return (
            CommentType.BACKUP,
            CommentClassification.DELETE,
            "Commented-out code should be removed (use git history)",
        )

    # Debt (TODO/FIXME).
    for pattern in _DEBT_PATTERNS:
        if pattern.search(text):
            return (
                CommentType.DEBT,
                CommentClassification.REWRITE,
                "Debt marker found - resolve or document in design comments",
            )

    # Trivial (trailing, restates the code before it).
    if reading is not None and reading.restates(token):
        return (
            CommentType.TRIVIAL,
            CommentClassification.DELETE,
            "Comment restates what code already says",
        )

    # Checklist.
    for pattern in _CHECKLIST_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.CHECKLIST,
                CommentClassification.KEEP,
                "Checklist comment - reminds of coordinated changes",
            )

    # Why.
    for pattern in _WHY_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.WHY,
                CommentClassification.KEEP,
                "Why comment - explains reasoning behind code",
            )

    # Teacher.
    for pattern in _TEACHER_PATTERNS:
        if pattern.search(text_lower):
            return (
                CommentType.TEACHER,
                CommentClassification.KEEP,
                "Teacher comment - educates about domain concepts",
            )

    # Guide.
    for pattern in _GUIDE_PATTERNS:
        if pattern.match(text):
            return (
                CommentType.GUIDE,
                CommentClassification.KEEP,
                "Guide comment - provides structure and rhythm",
            )

    # Block comment that wasn't a doc block: candidate design comment.
    if token.is_block and len(text) > 40:
        return (
            CommentType.DESIGN,
            CommentClassification.KEEP,
            "Block comment - likely design/algorithm explanation",
        )

    # Short inline comments are often trivial.
    if token.is_inline and len(text) < 20:
        return (
            CommentType.TRIVIAL,
            CommentClassification.ENHANCE,
            "Short inline comment - consider expanding or removing",
        )

    return (
        CommentType.UNKNOWN,
        CommentClassification.ENHANCE,
        "Cannot classify automatically - human review needed",
    )


def suggest_rewrite(comment: CommentInfo) -> str | None:
    if comment.classification == CommentClassification.DELETE:
        return None
    if comment.comment_type == CommentType.DEBT:
        task_text = _DEBT_REMOVAL_PATTERN.sub("", comment.text)
        return (
            f"DESIGN DECISION: {task_text.strip()}\n"
            f"Context: [Add why this is deferred and conditions for completion]"
        )
    if comment.comment_type == CommentType.TRIVIAL:
        return "WHY: [Explain the reasoning behind this code, not what it does]"
    if comment.comment_type == CommentType.FUNCTION and comment.classification == CommentClassification.ENHANCE:
        return (
            "Brief description of what this does.\n\n"
            "Args:\n  [parameter]: [description]\n"
            "Returns:\n  [description of return value]\n"
            "Raises:\n  [Exception]: [when it is raised]"
        )
    return None


# ---------------------------------------------------------------------------
# Rewriter.
# ---------------------------------------------------------------------------


class CommentRewriter:
    """Analyzes and (optionally) rewrites comments following antirez standards."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def _analyze_impl(
        self,
        content: str,
        file_path: str,
        language: str,
        include_suggestions: bool,
    ) -> CommentAnalysis:
        lines = content.splitlines()

        analysis = CommentAnalysis(
            file_path=file_path,
            language=language,
            total_comments=0,
            total_lines=len(lines),
            comment_ratio=0.0,
        )

        reading = _Reading.open(content, language, file_path) if language in _READ_AS_CODE else None
        if isinstance(reading, str):
            analysis.gap, reading = reading, None
        if reading is not None:
            tokens = reading.tokens
        else:
            # The stylesheet adapter reads `//` by dialect, which only the path gives.
            tokens = get_adapter(language).extract_comments(content, *((file_path,) if language == "css" else ()))
        for token in tokens:
            # Python docstrings are strings, not comment nodes: they are pulled
            # separately via the AST helper `_add_python_docstrings` later in
            # this method, so the per-token loop never sees docstrings.
            is_docstring = False
            comment_type, classification, reason = classify_comment(
                token=token,
                language=language,
                reading=reading,
            )
            info = CommentInfo(
                line_number=token.line_number,
                column=token.column,
                text=token.text,
                raw_text=token.raw_text,
                is_docstring=is_docstring,
                is_inline=token.is_inline,
                is_block=token.is_block,
                is_doc_block=token.is_doc_block,
                comment_type=comment_type,
                classification=classification,
                reason=reason,
            )
            if include_suggestions:
                info.suggestion = suggest_rewrite(info)
            analysis.comments.append(info)

        # Python-specific: pull docstrings from AST as well.
        if language == "python":
            self._add_python_docstrings(content, analysis, include_suggestions)

        analysis.comments.sort(key=lambda c: c.line_number)
        analysis.total_comments = len(analysis.comments)
        if analysis.total_lines > 0:
            analysis.comment_ratio = (analysis.total_comments / analysis.total_lines) * 100
        for c in analysis.comments:
            analysis.by_type[c.comment_type.value] = analysis.by_type.get(c.comment_type.value, 0) + 1
            analysis.by_classification[c.classification.value] = (
                analysis.by_classification.get(c.classification.value, 0) + 1
            )
        for c in analysis.comments:
            if c.classification in (CommentClassification.DELETE, CommentClassification.REWRITE):
                analysis.issues.append(
                    f"Line {c.line_number}: [{c.comment_type.value}] {c.reason}"
                )
        return analysis

    def _add_python_docstrings(
        self,
        content: str,
        analysis: CommentAnalysis,
        include_suggestions: bool,
    ) -> None:
        import ast

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    continue
                line_num = getattr(node, "lineno", 1)
                token = CommentToken(
                    line_number=line_num,
                    column=0,
                    text=docstring,
                    raw_text=f'"""{docstring}"""',
                    is_inline=False,
                    is_block=True,
                    is_doc_block=False,  # Python docstring, not /** */
                )
                # Force classification as a function/design comment.
                comment_type = CommentType.FUNCTION
                classification = (
                    CommentClassification.ENHANCE
                    if len(docstring) < 10
                    else CommentClassification.KEEP
                )
                reason = (
                    "Docstring too brief - needs more detail"
                    if len(docstring) < 10
                    else "Docstring provides API documentation"
                )
                info = CommentInfo(
                    line_number=line_num,
                    column=0,
                    text=docstring,
                    raw_text=token.raw_text,
                    is_docstring=True,
                    is_inline=False,
                    is_block=True,
                    is_doc_block=False,
                    comment_type=comment_type,
                    classification=classification,
                    reason=reason,
                )
                if include_suggestions:
                    info.suggestion = suggest_rewrite(info)
                analysis.comments.append(info)

    def analyze_file(self, file_path: Path) -> CommentAnalysis:
        file_path = Path(file_path).resolve()
        language = _validate_source_file(file_path)
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if self.verbose:
                logger.warning(f"File contains non-UTF8 characters: {file_path}")
        return self._analyze_impl(content, str(file_path), language, include_suggestions=True)

    def analyze_content(
        self,
        content: str,
        file_path: str = "<string>",
        language: str | None = None,
    ) -> CommentAnalysis:
        if language is None:
            language = detect_language(Path(file_path), content)
            if language is None:
                raise CommentRewriterError(
                    "Could not detect language. Pass language= explicitly."
                )
        return self._analyze_impl(content, file_path, language, include_suggestions=True)

    def rewrite_file(
        self,
        file_path: Path,
        output_path: Path | None = None,
        dry_run: bool = True,
    ) -> tuple[str, list[str]]:
        file_path = Path(file_path).resolve()
        language = _validate_source_file(file_path)
        if language == "css":
            # CSS has no line comment to emit, and in plain CSS `//` is not a
            # comment: it joins the next prelude or declaration, which the browser
            # drops, so removing it could make a dropped rule apply. Stylesheet
            # comments are analyzed, never rewritten.
            raise CommentRewriterError(
                f"Stylesheets are analyzed, never rewritten: {file_path.name}"
            )
        if output_path is not None:
            output_path = _validate_output_path(Path(output_path), file_path)

        content, newline, ends_with_newline = _read_preserving_newlines(file_path)

        lines = content.splitlines()
        analysis = self._analyze_impl(content, str(file_path), language, include_suggestions=True)
        if analysis.gap:
            return content, [
                f"Left unchanged: {analysis.gap}; commented-out code and restated lines "
                "are read from the syntax tree, never guessed"
            ]
        changes: list[str] = []

        lines_to_delete: set[int] = set()
        line_modifications: dict[int, str] = {}

        for comment in analysis.comments:
            # Don't modify docstrings or doc blocks automatically.
            if comment.is_docstring or comment.is_doc_block:
                continue
            line_idx = comment.line_number - 1
            if not (0 <= line_idx < len(lines)):
                continue
            old_line = lines[line_idx]

            if comment.classification == CommentClassification.DELETE:
                if comment.is_inline and not comment.is_block:
                    new_line = old_line[: comment.column].rstrip()
                    if new_line.strip():
                        line_modifications[line_idx] = new_line
                        changes.append(
                            f"Line {comment.line_number}: Removed inline comment: {comment.text[:50]}..."
                        )
                    else:
                        lines_to_delete.add(line_idx)
                        changes.append(
                            f"Line {comment.line_number}: Deleted line (empty after comment removal)"
                        )
                elif not comment.is_block:
                    # Stand-alone line comment.
                    lines_to_delete.add(line_idx)
                    changes.append(
                        f"Line {comment.line_number}: Deleted comment line: {comment.text[:50]}..."
                    )
                # Block comments: do not auto-delete to avoid removing
                # documentation by accident; just flag in changes.
                else:
                    changes.append(
                        f"Line {comment.line_number}: [skipped] Block comment flagged for deletion - requires manual review"
                    )

            elif comment.classification == CommentClassification.REWRITE and comment.suggestion:
                indent = len(old_line) - len(old_line.lstrip())
                indent_str = " " * indent
                marker = _line_marker_for(language)
                suggestion_lines = comment.suggestion.split("\n")
                suggestion_text = "\n".join(
                    f"{indent_str}{marker} {line}" for line in suggestion_lines
                )
                if line_idx not in line_modifications:
                    line_modifications[line_idx] = suggestion_text + "\n" + old_line
                    changes.append(
                        f"Line {comment.line_number}: Suggested rewrite for: {comment.text[:50]}..."
                    )

        for idx, new_content in line_modifications.items():
            if idx not in lines_to_delete:
                lines[idx] = new_content
        for idx in sorted(lines_to_delete, reverse=True):
            if 0 <= idx < len(lines):
                lines.pop(idx)
        rewritten = "\n".join(lines)
        if ends_with_newline:
            rewritten += "\n"

        if not dry_run:
            target = output_path or file_path
            if target.exists():
                backup_path = target.with_suffix(target.suffix + ".tmp")
                try:
                    backup_path.write_bytes(target.read_bytes())
                    _write_preserving_newlines(target, rewritten, newline)
                    backup_path.unlink()
                except Exception:
                    if backup_path.exists():
                        # replace(), not rename(): on Windows rename() onto an
                        # existing target raises FileExistsError, turning a
                        # recoverable write failure into a lost file.
                        backup_path.replace(target)
                    raise
            else:
                _write_preserving_newlines(target, rewritten, newline)
            changes.append(f"Wrote changes to: {target}")
            changes.append(FORMAT_UNDONE)

        return rewritten, changes

    def generate_report(self, analysis: CommentAnalysis) -> str:
        lines = [
            f"# Comment Analysis: {Path(analysis.file_path).name}",
            "",
            f"**File:** `{analysis.file_path}`",
            f"**Language:** {analysis.language}",
            f"**Total Lines:** {analysis.total_lines}",
            f"**Total Comments:** {analysis.total_comments}",
            f"**Comment Ratio:** {analysis.comment_ratio:.1f} per 100 lines",
            *([f"**Gap:** {analysis.gap}; commented-out code and restated lines were not looked for"]
              if analysis.gap else []),
            "",
            "---",
            "",
            "## Summary by Type",
            "",
        ]
        for type_name, count in sorted(analysis.by_type.items()):
            lines.append(f"- **{type_name}**: {count}")
        lines.extend(["", "## Summary by Classification", ""])
        for class_name, count in sorted(analysis.by_classification.items()):
            icon = {
                "keep": "[OK]",
                "enhance": "[~]",
                "rewrite": "[!]",
                "delete": "[X]",
            }.get(class_name, "[?]")
            lines.append(f"- {icon} **{class_name}**: {count}")
        if analysis.issues:
            lines.extend(["", "## Issues Found", ""])
            for issue in analysis.issues[:MAX_ISSUES_IN_REPORT]:
                lines.append(f"- {issue}")
            if len(analysis.issues) > MAX_ISSUES_IN_REPORT:
                lines.append(f"- ... and {len(analysis.issues) - MAX_ISSUES_IN_REPORT} more")
        lines.extend(["", "---", "", "## Detailed Analysis", ""])
        for classification in CommentClassification:
            class_comments = [c for c in analysis.comments if c.classification == classification]
            if not class_comments:
                continue
            lines.append(f"### {classification.value.upper()} ({len(class_comments)})")
            lines.append("")
            for comment in class_comments[:MAX_COMMENTS_PER_SECTION]:
                type_badge = f"[{comment.comment_type.value}]"
                preview = comment.text[:60] + "..." if len(comment.text) > 60 else comment.text
                lines.append(f"- **Line {comment.line_number}** {type_badge}: `{preview}`")
                lines.append(f"  - Reason: {comment.reason}")
                if comment.suggestion:
                    lines.append(f"  - Suggestion: _{comment.suggestion[:80]}..._")
            if len(class_comments) > MAX_COMMENTS_PER_SECTION:
                lines.append(f"- ... and {len(class_comments) - MAX_COMMENTS_PER_SECTION} more")
            lines.append("")
        lines.extend([
            "---",
            "",
            "_Analysis based on antirez commenting standards: https://antirez.com/news/124_",
        ])
        return "\n".join(lines)


def _line_marker_for(language: str) -> str:
    return {
        "python": "#",
        "java": "//",
        "javascript": "//",
        "typescript": "//",
        "sql": "--",
        "plsql": "--",
        "rust": "//",
        "go": "//",
    }.get(language, "#")


# ---------------------------------------------------------------------------
# Convenience functions.
# ---------------------------------------------------------------------------


def analyze_comments(file_path: Path) -> CommentAnalysis:
    return CommentRewriter().analyze_file(file_path)


def rewrite_file(
    file_path: Path,
    output_path: Path | None = None,
    dry_run: bool = True,
) -> tuple[str, list[str]]:
    return CommentRewriter().rewrite_file(file_path, output_path, dry_run)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python comment_rewriter.py <file_path>")
        print("")
        print("Analyzes file comments following antirez standards.")
        print("Supports Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust; stylesheets are analyzed only.")
        sys.exit(1)
    test_file = Path(sys.argv[1])
    try:
        rewriter = CommentRewriter(verbose=True)
        analysis = rewriter.analyze_file(test_file)
        print(rewriter.generate_report(analysis))
    except CommentRewriterError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
