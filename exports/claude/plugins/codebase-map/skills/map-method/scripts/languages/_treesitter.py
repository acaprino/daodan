"""
Optional tree-sitter loader.

Returns a (parser, language) pair or None if tree-sitter or the requested
grammar is unavailable. Adapters call this and fall back to regex parsing
when it returns None.

We prefer `tree-sitter-language-pack` (modern, single dependency, bundles
many grammars) and fall back to per-grammar packages
(`tree-sitter-python`, `tree-sitter-java`, etc.) if the user has installed
those directly.

## Caching and Thread-safety

`get_parser` caches `(parser, language)` **per thread** via `threading.local()`,
and `load_failure` is likewise thread-local. Immutable Language handles are
shared across threads. Tree-sitter's C `Parser` instances
are not safe for concurrent `parser.parse(src)` calls across threads, so giving
each worker thread its own cached parser instance makes `ThreadPoolExecutor`
over many files safe without locking.

**Both success and failure are cached** for the thread lifetime. If you install
tree-sitter mid-process (e.g. from a REPL) or swap `sys.modules` in a test, call
`get_parser.cache_clear()` to invalidate every thread's cache and clear recorded
load failures so the next `get_parser(language)` re-probes the install state.
"""

from __future__ import annotations

import threading
from typing import Any, Callable

__all__ = [
    "check_syntax_errors",
    "extract_ast_calls",
    "get_parser",
    "get_query",
    "load_failure",
    "mask_comments",
    "node_text",
    "query_captures",
    "scan_ast_external_calls",
]


# Aliases used by tree-sitter-language-pack.
_LANG_PACK_ALIASES = {
    "python": "python",
    "java": "java",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
    "sql": "sql",
    "rust": "rust",
    "go": "go",
    "csharp": "csharp",
    "c_sharp": "csharp",
    "kotlin": "kotlin",
}

# Per-grammar package names for the fallback strategy.
_GRAMMAR_MODULES = {
    "python": "tree_sitter_python",
    "java": "tree_sitter_java",
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "tsx": "tree_sitter_typescript",
    "sql": "tree_sitter_sql",
    "rust": "tree_sitter_rust",
    "go": "tree_sitter_go",
    "csharp": "tree_sitter_c_sharp",
    "kotlin": "tree_sitter_kotlin",
}

# TypeError is included because a version mismatch between `tree-sitter` and a
# grammar package surfaces as one (e.g. `Language(capsule)` rejecting an
# incompatible capsule). Treating it as "unavailable" degrades to the regex
# fallback instead of crashing the whole analysis run.
_LOAD_ERRORS = (ImportError, AttributeError, TypeError, ValueError, LookupError)

_LOCAL = threading.local()
_CACHE_EPOCH = 0
_EPOCH_LOCK = threading.Lock()
_GRAMMARS: dict[str, tuple[Any, str | None]] = {}


def _thread_state() -> tuple[dict[str, tuple[Any, Any] | None], dict[str, str], dict[tuple[str, str], Any]]:
    """Return the calling thread's (parser_cache, load_failures, query_cache) dictionaries."""
    epoch = _CACHE_EPOCH
    if getattr(_LOCAL, "epoch", -1) != epoch:
        _LOCAL.epoch = epoch
        _LOCAL.parsers = {}
        _LOCAL.failures = {}
        _LOCAL.queries = {}
    return _LOCAL.parsers, _LOCAL.failures, _LOCAL.queries


def load_failure(language: str) -> str | None:
    """The reason an installed grammar pack gave no parser for `language`, if any."""
    _, failures, _ = _thread_state()
    return failures.get(language)


def _load_parser_uncached(language: str, failures: dict[str, str]) -> tuple[Any, Any] | None:
    failures.pop(language, None)
    pack_name = _LANG_PACK_ALIASES.get(language)
    if pack_name is None:
        return None

    # Strategy 1: tree-sitter-language-pack (preferred).
    #
    # Only `get_parser` is used. The pack's `get_language` returns a plain
    # capsule rather than a `tree_sitter.Language` on newer releases (the
    # package dropped its tree-sitter dependency), so building our own
    # `Parser(get_language(...))` would break there. The parser the pack hands
    # back already carries its language.
    try:
        from tree_sitter_language_pack import get_parser as _pack_get_parser  # type: ignore

        parser = _pack_get_parser(pack_name)
    except ImportError:
        pass
    except Exception as exc:
        # Installed but unusable: a version mismatch, or a grammar download
        # that failed. Every such error means the fallback, never a crash, and
        # the reason is kept for the result's notes.
        failures[language] = f"{type(exc).__name__}: {exc}"
    else:
        return parser, getattr(parser, "language", None)

    # Strategy 2: individual tree-sitter-<lang> package + tree-sitter core
    # (the >= 0.23 API, where Language() takes the grammar capsule and Parser()
    # takes the Language).
    try:
        from tree_sitter import Language, Parser  # type: ignore

        import_name = _GRAMMAR_MODULES.get(pack_name)
        if import_name is None:
            return None
        mod = __import__(import_name)
        # tree-sitter-typescript exposes both language_typescript and language_tsx.
        if pack_name == "typescript":
            lang_capsule = mod.language_typescript()
        elif pack_name == "tsx":
            lang_capsule = mod.language_tsx()
        else:
            lang_capsule = mod.language()
        lang_obj = Language(lang_capsule)
        parser = Parser(lang_obj)
        failures.pop(language, None)
        return parser, lang_obj
    except _LOAD_ERRORS:
        return None


def get_parser(language: str) -> tuple[Any, Any] | None:
    """
    Return (parser, language_obj) for the requested language, or None if
    tree-sitter is not installed or the grammar is unavailable.

    The immutable `language_obj` is shared across threads; mutable parsers are
    separate. An unavailable grammar returns None and permits regex fallback.

    Result is cached per thread. Call `get_parser.cache_clear()` after a
    mid-process install to re-probe across all threads.
    """
    parsers, failures, _ = _thread_state()
    if language in parsers:
        return parsers[language]
    # Language handles are immutable. Load one under the same lock used by
    # invalidation, then give each thread its own mutable Parser instance.
    with _EPOCH_LOCK:
        if language not in _GRAMMARS:
            loaded = _load_parser_uncached(language, failures)
            _GRAMMARS[language] = (
                loaded[1] if loaded else None,
                failures.get(language),
            )
        lang_obj, failure = _GRAMMARS[language]
        if failure is not None:
            failures[language] = failure
    result = None
    if lang_obj is not None:
        try:
            from tree_sitter import Parser  # type: ignore

            try:
                parser = Parser(lang_obj)
            except TypeError:
                parser = Parser()
                parser.set_language(lang_obj)
            result = parser, lang_obj
        except _LOAD_ERRORS as exc:
            failures[language] = f"{type(exc).__name__}: {exc}"
    parsers[language] = result
    return result


def _cache_clear() -> None:
    global _CACHE_EPOCH
    with _EPOCH_LOCK:
        _CACHE_EPOCH += 1
        _GRAMMARS.clear()


get_parser.cache_clear = _cache_clear  # type: ignore[attr-defined]


def get_query(language: str, sexp: str) -> Any | None:
    """
    Compile and cache a tree-sitter S-expression `Query` per thread.

    Returns None when tree-sitter or the grammar's `Language` object is
    unavailable or when the query syntax is rejected by the grammar ABI.
    """
    _, _, queries = _thread_state()
    key = (language, sexp)
    if key in queries:
        return queries[key]
    pair = get_parser(language)
    if pair is None or pair[1] is None:
        queries[key] = None
        return None
    lang_obj = pair[1]
    query_obj = None
    try:
        from tree_sitter import Query  # type: ignore

        query_obj = Query(lang_obj, sexp)
    except Exception:
        try:
            if hasattr(lang_obj, "query"):
                query_obj = lang_obj.query(sexp)
        except Exception:
            query_obj = None
    queries[key] = query_obj
    return query_obj


def query_captures(language: str, sexp: str, root: Any) -> dict[str, list[Any]]:
    """
    Execute a compiled S-expression query against `root` and return `{capture_name: [nodes]}`.

    Supports both `tree-sitter >= 0.23` (`QueryCursor(query).captures(root)`)
    and `0.21-0.22` (`query.captures(root)`), returning `{}` if unavailable.
    """
    if root is None:
        return {}
    query = get_query(language, sexp)
    if query is None:
        return {}
    try:
        try:
            from tree_sitter import QueryCursor  # type: ignore

            raw = QueryCursor(query).captures(root)
        except ImportError:
            raw = query.captures(root)
        if isinstance(raw, dict):
            return {k: list(v) for k, v in raw.items()}
        out: dict[str, list[Any]] = {}
        for item in raw:
            if isinstance(item, tuple) and len(item) == 2:
                first, second = item
                if isinstance(second, str):
                    out.setdefault(second, []).append(first)
                elif isinstance(first, str):
                    out.setdefault(first, []).append(second)
        return out
    except Exception:
        return {}


_CALL_NODE_TYPES = frozenset({
    "call_expression",
    "method_invocation",
    "invocation_expression",
    "new_expression",
    "object_creation_expression",
    "explicit_constructor_invocation",
    "macro_invocation",
})
_CALL_SIBLING_BOUNDARIES = frozenset({
    "function_declaration",
    "function_definition",
    "function_item",
    "method_declaration",
    "method_definition",
    "arrow_function",
    "function_expression",
    "closure_expression",
    "lambda_expression",
    "func_literal",
    "generator_function_declaration",
    "generator_function",
    "function",
    "class",
    "class_declaration",
    "abstract_class_declaration",
    "interface_declaration",
    "enum_declaration",
    "record_declaration",
    "annotation_type_declaration",
    "macro_definition",
    "type_annotation",
    "type_arguments",
})

_CALL_QUERIES = {
    "javascript": "[(call_expression) (new_expression)] @call",
    "typescript": "[(call_expression) (new_expression)] @call",
    "tsx": "[(call_expression) (new_expression)] @call",
    "java": "[(method_invocation) (object_creation_expression) (explicit_constructor_invocation)] @call",
    "rust": "[(call_expression) (macro_invocation)] @call",
    "go": "(call_expression) @call",
}


def _reference_name(node: Any, source_bytes: bytes) -> str:
    """Render a call target without copying argument literals or comments."""
    if node is None:
        return ""
    if node.type in _CALL_NODE_TYPES:
        name = _callee_name_from_node(node, source_bytes)
        return name + "()" if name else ""
    if node.type in ("member_expression", "field_expression", "scoped_identifier", "scoped_type_identifier"):
        owner = node.child_by_field_name("object") or node.child_by_field_name("value") or node.child_by_field_name("path")
        member = node.child_by_field_name("property") or node.child_by_field_name("field") or node.child_by_field_name("name")
        owner_name = _reference_name(owner, source_bytes)
        member_name = _reference_name(member, source_bytes)
        separator = "::" if node.type.startswith("scoped_") else "."
        return f"{owner_name}{separator}{member_name}" if owner_name and member_name else ""
    if node.type in ("parenthesized_expression", "non_null_expression", "generic_function"):
        children = [c for c in node.named_children if c.type not in _COMMENT_NODE_TYPES]
        return _reference_name(children[0], source_bytes) if children else ""
    if node.type == "generic_type":
        name = node.child_by_field_name("name")
        if name is None:
            name = next((c for c in node.named_children if c.type not in ("type_arguments", *_COMMENT_NODE_TYPES)), None)
        return _reference_name(name, source_bytes)
    if node.type in ("subscript_expression", "index_expression"):
        owner = node.child_by_field_name("object") or node.child_by_field_name("value")
        name = _reference_name(owner, source_bytes)
        return name + "[]" if name else ""
    raw = node_text(node, source_bytes).strip()
    if raw and len(raw) <= 80 and all(c.isalnum() or c in "_$.:<>?!#" for c in raw):
        return raw
    return ""


def _callee_name_from_node(node: Any, source_bytes: bytes) -> str:
    """Extract a concise callee identifier or `receiver.method` from a call AST node."""
    ntype = getattr(node, "type", "")
    if ntype == "macro_invocation":
        macro = node.child_by_field_name("macro")
        name = _reference_name(macro, source_bytes)
        return name + "!" if name else ""
    if ntype in ("new_expression", "object_creation_expression", "explicit_constructor_invocation"):
        target = node.child_by_field_name("constructor") or node.child_by_field_name("type")
        return _reference_name(target, source_bytes)
    if ntype == "method_invocation":
        name_node = node.child_by_field_name("name")
        obj_node = node.child_by_field_name("object")
        if name_node is not None:
            mname = node_text(name_node, source_bytes).strip()
            if obj_node is not None:
                oname = _reference_name(obj_node, source_bytes)
                if oname:
                    return f"{oname}.{mname}"
            return mname
    fn_node = (
        node.child_by_field_name("function")
        or node.child_by_field_name("expression")
        or node.child_by_field_name("name")
    )
    if fn_node is None:
        children = getattr(node, "children", None) or ()
        if children:
            fn_node = children[0]
    if fn_node is None:
        return ""
    return _reference_name(fn_node, source_bytes)


def _ast_call_nodes(body_node: Any, language: str | None, *, owned: bool = True) -> list[Any]:
    """Find call nodes, pruning nested callable/type bodies for an owned scope."""
    if body_node is None:
        return []
    query = _CALL_QUERIES.get(language or "")
    captures = query_captures(language, query, body_node).get("call", []) if query else []
    if captures:
        calls = []
        for node in captures:
            parent = node.parent if node != body_node else None
            while owned and parent is not None and parent != body_node:
                if parent.type in _CALL_SIBLING_BOUNDARIES:
                    break
                parent = parent.parent
            else:
                calls.append(node)
        return sorted(calls, key=lambda n: (n.start_byte, -n.end_byte))
    calls = []
    stack = [body_node]
    while stack:
        node = stack.pop()
        ntype = getattr(node, "type", "")
        if node != body_node and (ntype == "macro_definition" or (owned and ntype in _CALL_SIBLING_BOUNDARIES)):
            continue
        if ntype in _CALL_NODE_TYPES:
            calls.append(node)
        stack.extend(reversed(getattr(node, "children", None) or ()))
    return calls


def extract_ast_calls(
    body_node: Any,
    source_bytes: bytes,
    language: str | None = None,
) -> list[str]:
    """
    Collect distinct outgoing function/method call names inside `body_node`
    in source order, using tree-sitter S-expression queries when available and
    a fast AST walk fallback that does not descend into nested function literals.
    """
    if body_node is None:
        return []
    seen: list[str] = []
    seen_set: set[str] = set()

    for node in _ast_call_nodes(body_node, language):
        callee = _callee_name_from_node(node, source_bytes)
        if callee and callee not in seen_set:
            seen_set.add(callee)
            seen.append(callee)
    return seen


def scan_ast_external_calls(
    root: Any,
    source_bytes: bytes,
    content: str,
    language: str,
    scanner: Callable[[str], list[Any]],
) -> list[Any]:
    """Apply existing API categories only to actual call targets, never literals."""
    lines = content.splitlines()
    calls = []
    seen = set()
    for node in _ast_call_nodes(root, language, owned=False):
        name = _callee_name_from_node(node, source_bytes)
        if not name:
            continue
        prefix = "new " if node.type in ("new_expression", "object_creation_expression") else ""
        line_number = node.start_point[0] + 1
        for call in scanner(f"{prefix}{name}(_);"):
            key = call.call_type, line_number
            if key in seen:
                continue
            seen.add(key)
            call.line_number = line_number
            call.context = lines[line_number - 1].strip()[:100]
            calls.append(call)
    return calls


def check_syntax_errors(root: Any) -> str | None:
    """Return a `syntax error: line <N>` note if the tree-sitter AST contains errors."""
    if root is None or not getattr(root, "has_error", False):
        return None
    stack = [root]
    first_line: int | None = None
    while stack:
        node = stack.pop()
        is_err = getattr(node, "type", "") == "ERROR" or getattr(node, "is_missing", False)
        if is_err:
            line = getattr(node, "start_point", (0, 0))[0] + 1
            if first_line is None or line < first_line:
                first_line = line
        if getattr(node, "has_error", False):
            children = getattr(node, "children", None) or ()
            for ch in reversed(children):
                stack.append(ch)
    if first_line is None:
        first_line = getattr(root, "start_point", (0, 0))[0] + 1
    return f"syntax error: line {first_line}"


_COMMENT_NODE_TYPES = frozenset({"comment", "line_comment", "block_comment"})


def mask_comments(root: Any, source_bytes: bytes, fallback_text: str) -> str:
    """Replace comment node byte spans with spaces (preserving newlines) for line-preserving regex scans."""
    if root is None:
        return fallback_text
    spans: list[tuple[int, int]] = []
    stack = [root]
    while stack:
        node = stack.pop()
        if getattr(node, "type", "") in _COMMENT_NODE_TYPES:
            start_b = getattr(node, "start_byte", 0)
            end_b = getattr(node, "end_byte", 0)
            if 0 <= start_b < end_b <= len(source_bytes):
                spans.append((start_b, end_b))
            continue
        children = getattr(node, "children", None) or ()
        for ch in reversed(children):
            stack.append(ch)
    if not spans:
        return fallback_text
    buf = bytearray(source_bytes)
    for start_b, end_b in spans:
        for idx in range(start_b, end_b):
            if buf[idx] not in (10, 13):  # preserve \n and \r so line numbers stay identical
                buf[idx] = 32
    return buf.decode("utf-8", errors="replace")


def node_text(node: Any, source_bytes: bytes) -> str:
    """
    Return the source text covered by a tree-sitter node.

    Returns "" when the node carries out-of-range or missing byte offsets
    (seen on ERROR/MISSING nodes in a partially parsed tree). Callers treat an
    empty name as "nothing extractable here" and skip the node, so an empty
    string is the intended degradation rather than a swallowed bug.
    """
    try:
        return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
    except (AttributeError, TypeError, ValueError):
        return ""
