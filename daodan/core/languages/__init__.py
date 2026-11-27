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

from pathlib import Path

from file_formats import SOURCES

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
from .detect import detect as _detect

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


# File extension to language map, from Daodan's register of file formats (`data/file-formats.json`). An extension
# more than one language shares (`.sql`, `.ts`, `.h`) is decided on the content (see detect_language). Markup gives
# the rules of its `<style>` blocks; indented Sass is read as the SCSS its indentation implies, and PostCSS sheets
# are CSS.
SUPPORTED_EXTENSIONS: dict[str, str] = SOURCES


def detect_language(file_path: Path, content: str | None = None) -> str | None:
    """
    The language of a file: its extension, then the rules of that extension on its content (`languages.detect`),
    then the extension's own language. Returns the canonical language identifier, or None if unsupported.

    A `.h` header with text is read from its syntax tree by `detect/rules/header.py` (Objective-C, C++, or C).
    """
    return _detect(file_path, content).language


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
