"""
Language adapter dispatch for the codebase mapping.

Maps file extensions to language adapters that implement the LanguageAdapter
protocol. Each adapter provides structural extraction (classes, functions,
imports, external calls) and comment syntax info.

Supported languages:
    Python, Java, JavaScript, TypeScript (incl. TSX/JSX), SQL, PL/SQL, Rust, Go,
    CSS (incl. SCSS and LESS), C, C++.

Tree-sitter is used when available via the optional `tree-sitter-language-pack`
package, with regex-based fallback per language. Python uses the stdlib `ast`
module so it works without any external dependency.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import (
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    LanguageAdapter,
    NestedDefinition,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken

__all__ = [
    "LanguageAdapter",
    "ParameterInfo",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "ExternalCallInfo",
    "NestedDefinition",
    "ParseResult",
    "CommentToken",
    "Language",
    "detect_language",
    "get_adapter",
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_LANGUAGES",
]


# Canonical language identifiers used internally.
class Language:
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SQL = "sql"
    PLSQL = "plsql"
    RUST = "rust"
    GO = "go"
    CSS = "css"
    KOTLIN = "kotlin"
    CSHARP = "csharp"
    VUE = "vue"
    SVELTE = "svelte"
    ASTRO = "astro"
    MARKUP = "markup"
    C = "c"
    CPP = "cpp"


SUPPORTED_LANGUAGES: tuple[str, ...] = (
    Language.PYTHON,
    Language.JAVA,
    Language.JAVASCRIPT,
    Language.TYPESCRIPT,
    Language.SQL,
    Language.PLSQL,
    Language.RUST,
    Language.GO,
    Language.CSS,
    Language.KOTLIN,
    Language.CSHARP,
    Language.VUE,
    Language.SVELTE,
    Language.ASTRO,
    Language.MARKUP,
    Language.C,
    Language.CPP,
)


# File extension to language map. PL/SQL detection also looks at content
# (see detect_language) because .sql is ambiguous between SQL and PL/SQL.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".java": Language.JAVA,
    ".js": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".mts": Language.TYPESCRIPT,
    ".cts": Language.TYPESCRIPT,
    ".sql": Language.SQL,
    ".ddl": Language.SQL,
    ".dml": Language.SQL,
    # PL/SQL specific extensions (Oracle).
    ".pks": Language.PLSQL,  # Package spec
    ".pkb": Language.PLSQL,  # Package body
    ".plsql": Language.PLSQL,
    ".pls": Language.PLSQL,
    ".pck": Language.PLSQL,
    ".prc": Language.PLSQL,  # Procedure
    ".fnc": Language.PLSQL,  # Function
    ".trg": Language.PLSQL,  # Trigger
    # Rust.
    ".rs": Language.RUST,
    # Go.
    ".go": Language.GO,
    # Kotlin.
    ".kt": Language.KOTLIN,
    ".kts": Language.KOTLIN,
    # C#.
    ".cs": Language.CSHARP,
    # C and C++. A `.h` header is C unless its text says C++ or Objective-C (see detect_language).
    ".c": Language.C,
    ".h": Language.C,
    ".cc": Language.CPP,
    ".cpp": Language.CPP,
    ".cxx": Language.CPP,
    ".hpp": Language.CPP,
    ".hh": Language.CPP,
    ".hxx": Language.CPP,
    # Single-file frontend components.
    ".vue": Language.VUE,
    ".svelte": Language.SVELTE,
    ".astro": Language.ASTRO,
    # Markup: the rules of its `<style>` blocks.
    **dict.fromkeys((".cshtml", ".ejs", ".erb", ".ftl", ".handlebars", ".hbs", ".htm", ".html", ".j2",
                     ".jinja", ".jsp", ".jspx", ".liquid", ".mustache", ".njk", ".razor", ".twig", ".vm",
                     ".xhtml"), Language.MARKUP),
    # Stylesheets. Indented Sass is read as the SCSS its indentation implies;
    # PostCSS sheets are CSS.
    ".css": Language.CSS,
    ".scss": Language.CSS,
    ".sass": Language.CSS,
    ".less": Language.CSS,
    ".pcss": Language.CSS,
    ".postcss": Language.CSS,
}


# Oracle-specific markers. We intentionally do NOT match generic "begin",
# "exception", "create or replace function" - PostgreSQL plpgsql uses those
# too. PL/SQL is only detected when the source uses Oracle-specific syntax.
#
# `%TYPE` and `%ROWTYPE` use a word-boundary regex so a SQL `LIKE '%type%'`
# pattern (common in pg_catalog queries) does NOT false-route to PL/SQL.
_PLSQL_LITERAL_MARKERS = (
    "create or replace package",
    "create or replace type body",
    "dbms_output",
    "utl_file",
    "utl_http",
    "bfilename",
    "extproc",
    "pragma autonomous",
    "pragma serially_reusable",
    "pragma exception_init",
    "pragma restrict_references",
)
_PLSQL_ROWTYPE_RE = re.compile(r"\w%(?:rowtype|type)\b", re.IGNORECASE)

# A `.h` header is C++ when its text, comments and string literals left out, has
# a construct C does not: a namespace body (its name nested too, `a::b`), a class
# body, a template, an access label, a using-directive. `extern "C"` under
# `__cplusplus` is a C header's own guard. One with a directive of Objective-C's is
# Objective-C, which the snapshot does not read.
_C_NOISE_RE = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', re.DOTALL)
# What C lacks: a namespace (an anonymous one or an alias opening a line: C names a struct tag or a variable
# `namespace`), a class, a template, an access specifier, `using namespace`, a name of `std::`, and a C++ standard
# library header (the last two are Linguist's own rule for `.h`).
_CPP_HEADER_RE = re.compile(
    r"\bnamespace\s+\w+(?:\s*::\s*(?:inline\s+)?\w+)*\s*\{|^[ \t]*namespace\s*\{|^[ \t]*namespace\s+\w+\s*=(?!=)"
    r"|\bclass\s+\w+[^;(){}]*\{|\btemplate\s*<|^\s*(?:public|private|protected)\s*:|\busing\s+namespace\b|\bstd::\w"
    r"|^\s*#\s*include\s*<(?:cstdint|string|vector|map|list|array|bitset|queue|stack|forward_list|unordered_map"
    r"|unordered_set|(?:i|o|io)stream)>",
    re.MULTILINE,
)
_OBJC_HEADER_RE = re.compile(r"^\s*@(?:interface|implementation|protocol|class|property|end)\b", re.MULTILINE)
# A `.ts` file that is an XML document is a Qt Linguist translation (`<!DOCTYPE TS>`), not TypeScript.
_XML_RE = re.compile(r"\s*<(?:\?xml|!DOCTYPE)\b")


def detect_language(file_path: Path, content: str | None = None) -> str | None:
    """
    Detect the language of a file by extension. For ambiguous .sql files,
    inspect content for PL/SQL-specific markers; for .h and .ts files, for
    another language's (C++, Objective-C, XML).

    Returns the canonical language identifier or None if unsupported.
    """
    suffix = file_path.suffix.lower()
    lang = SUPPORTED_EXTENSIONS.get(suffix)

    if suffix == ".h" and content is not None:
        code = _C_NOISE_RE.sub(" ", content)
        if _OBJC_HEADER_RE.search(code):
            return None
        if _CPP_HEADER_RE.search(code):
            return Language.CPP
    if suffix == ".ts" and content is not None and _XML_RE.match(content):
        return None

    # Disambiguate .sql vs PL/SQL by content if provided.
    if lang == Language.SQL and content is not None:
        lowered = content.lower()
        if any(marker in lowered for marker in _PLSQL_LITERAL_MARKERS):
            return Language.PLSQL
        if _PLSQL_ROWTYPE_RE.search(content):
            return Language.PLSQL

    return lang


def get_adapter(language: str) -> LanguageAdapter:
    """
    Return the adapter for a given canonical language identifier.

    The argument is case-insensitive ("Python", "PYTHON", "python" all work).

    Raises ValueError if the language is not supported. Imports are lazy so
    that missing optional dependencies (tree-sitter) only fail when actually
    needed. Adapter modules MUST NOT do fallible work at import time -- if a
    future adapter's `__init__` raises, the resulting ImportError surfaces
    here instead of the documented ValueError.
    """
    language = language.lower()
    if language == Language.PYTHON:
        from . import python as _mod
        return _mod.adapter
    if language == Language.JAVA:
        from . import java as _mod
        return _mod.adapter
    if language == Language.JAVASCRIPT:
        from . import javascript as _mod
        return _mod.adapter
    if language == Language.TYPESCRIPT:
        from . import typescript as _mod
        return _mod.adapter
    if language == Language.SQL:
        from . import sql as _mod
        return _mod.adapter
    if language == Language.PLSQL:
        from . import plsql as _mod
        return _mod.adapter
    if language == Language.RUST:
        from . import rust as _mod
        return _mod.adapter
    if language == Language.GO:
        from . import go as _mod
        return _mod.adapter
    if language == Language.CSS:
        from . import stylesheet as _mod
        return _mod.adapter
    if language == Language.KOTLIN:
        from . import kotlin as _mod
        return _mod.adapter
    if language == Language.CSHARP:
        from . import csharp as _mod
        return _mod.adapter
    if language == Language.VUE:
        from . import sfc as _mod
        return _mod.vue_adapter
    if language == Language.SVELTE:
        from . import sfc as _mod
        return _mod.svelte_adapter
    if language == Language.ASTRO:
        from . import sfc as _mod
        return _mod.astro_adapter
    if language == Language.MARKUP:
        from . import markup as _mod
        return _mod.adapter
    if language == Language.C:
        from . import cfamily as _mod
        return _mod.c_adapter
    if language == Language.CPP:
        from . import cfamily as _mod
        return _mod.cpp_adapter
    raise ValueError(f"Unsupported language: {language!r}")
