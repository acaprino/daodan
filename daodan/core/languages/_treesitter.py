"""
Optional tree-sitter loader.

Returns a (parser, language) pair or None if tree-sitter or the requested
grammar is unavailable. Adapters call this and fall back to regex parsing
when it returns None; the snapshot instead records the file as a declared
gap (`snapshot.parser_profile`).

We prefer `tree-sitter-language-pack`, pinned to `PACK_VERSION`: Daodan puts
the release's bundle into its own cache, verified by sha256, and configures
the pack on it, so the pack never downloads. Per-grammar packages
(`tree-sitter-python`, `tree-sitter-java`, etc.) are used when the pack is
not installed or gives no grammar.

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

import hashlib
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable

__all__ = [
    "check_syntax_errors",
    "extract_ast_calls",
    "get_parser",
    "get_query",
    "get_tags_query",
    "load_failure",
    "mask_comments",
    "node_text",
    "query_captures",
    "query_tags",
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
    "c": "c",
    "cpp": "cpp",
    "swift": "swift",
    "elixir": "elixir",
    "php": "php",
    "vue": "vue",  # the templates of single-file components (`languages/sfc.py`)
    "svelte": "svelte",
    "angular": "angular",  # the markup the entry readers read (`daodan/data/entry-queries.json`)
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
    "c": "tree_sitter_c",
    "cpp": "tree_sitter_cpp",
}

# TypeError is included because a version mismatch between `tree-sitter` and a
# grammar package surfaces as one (e.g. `Language(capsule)` rejecting an
# incompatible capsule). Treating it as "unavailable" degrades to the regex
# fallback instead of crashing the whole analysis run.
_LOAD_ERRORS = (ImportError, AttributeError, TypeError, ValueError, LookupError)

# The pinned tree-sitter-language-pack release. The pack loads a grammar from the directory it is configured
# with, extracting it from the platform's bundle when the manifest sits beside it, and never verifies a bundle
# already in place: these sha256 are the only guard. The release's own manifest (`parsers.json`) and bundles.
PACK_VERSION = "1.13.5"
_PACK_RELEASE = f"https://github.com/xberg-io/tree-sitter-language-pack/releases/download/v{PACK_VERSION}"
PACK_MANIFEST = ("689db000f889084cc0e7052f031b277029fe893ab7846e51057822a3af997735", 25002)
PACK_BUNDLES = {
    "linux-aarch64": ("e47812e12009562b11e1362e503196ccb44c6f4f71ff794a611637e2e4d0897a", 18250861),
    "linux-x86_64": ("d1b4c48c8f1eef894a2eaa31762da404a7eba62e15bc75a9cd3bde4af64db88a", 18698076),
    "macos-arm64": ("74a576dbfd70bee0bfcdff7d2e0741b1078093500d6b3c36c52563ae81a7732a", 20918709),
    "macos-x86_64": ("1086d3a23659dae7d43d774f7836e88e3e526ba1d0f4fa0ea9bcf2cc3e6e32a2", 18285977),
    "windows-aarch64": ("1f7a4fa32d6a70da746a8595efed0b7c51e54050f2eac0d15edec76d1de9b3ff", 17671296),
    "windows-x86_64": ("fb0042c7f4b9ec9383647f7b4e1eee97236e484b0950732c33faffc007c3716e", 18063968),
}


def manifest_url() -> str:
    return f"{_PACK_RELEASE}/parsers.json"


def bundle_url(platform: str) -> str:
    return f"{_PACK_RELEASE}/parsers-{platform}.tar.zst"


def pack_platform(system: str = sys.platform, machine: str | None = None) -> str:
    """This process's platform in the pack's names: `windows-x86_64`, `macos-arm64` and so on.

    From `sys.platform` and the process's architecture (`PROCESSOR_ARCHITECTURE` on Windows, `os.uname`
    elsewhere), the one whose libraries the process loads. Never from `platform`: it asks Windows through WMI
    and, when WMI fails, runs `ver` through the shell.
    """
    if machine is None:
        machine = os.environ.get("PROCESSOR_ARCHITECTURE", "") if system == "win32" else os.uname().machine
    name = {"win32": "windows", "linux": "linux", "darwin": "macos"}.get(system, system)
    arm = machine.lower() in ("arm64", "aarch64")
    return f"{name}-{('arm64' if name == 'macos' else 'aarch64') if arm else 'x86_64'}"


def _daodan_home() -> Path:
    """Where Daodan keeps the pinned release: manifest.json, bundles/ and the libs/ the pack extracts into."""
    from embedding_worker import shared_cache_dir

    return shared_cache_dir() / "grammars" / "tree-sitter-language-pack" / f"v{PACK_VERSION}"


_USER_PACK_HOME: list[Path | None] = []


def _user_pack_home() -> Path | None:
    """The pack's own cache of this release, read before Daodan configures the pack: copies come from it."""
    if not _USER_PACK_HOME:
        try:
            import tree_sitter_language_pack as pack  # type: ignore

            _USER_PACK_HOME.append(Path(pack.cache_dir()).parent)
        except Exception:
            _USER_PACK_HOME.append(None)
    return _USER_PACK_HOME[0]


def _fetch(url: str, target: Path, *, sha256: str) -> Path:
    from resolve_edges import download

    return download(url, target, sha256=sha256)


def _matches(path: Path, digest: str, size: int) -> bool:
    try:
        if not path.is_file() or path.stat().st_size != size:
            return False
        sha = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                sha.update(chunk)
    except OSError:
        return False
    return sha.hexdigest() == digest


def _settle(target: Path, digest: str, size: int, write: Callable[[Path], Any]) -> bool:
    """Whether `target` holds its pinned file once `write(path)` has written it under a name of this process's own
    beside it, renamed into place if it matches: another process sees the whole file or none (the pack's own
    writes do the same), and nothing it may read is removed. The name of its own goes, whatever happens."""
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    os.close(handle)
    private = Path(name)
    try:
        write(private)
        if not _matches(private, digest, size):
            return False
        try:
            os.replace(private, target)
        except OSError:  # Windows: a process that placed it holds it open
            return _matches(target, digest, size)
        return True
    finally:
        private.unlink(missing_ok=True)


def place_grammars(home: Path, platform: str, user_home: Path | None, fetch) -> str | None:
    """Put the pinned manifest and the platform's bundle into `home`, each verified by its sha256.

    A file already there is verified and kept, or replaced. A missing one is copied from `user_home`, the pack's
    own cache, which is only read, else fetched through `fetch(url, target, sha256=)`; a copy or a download that
    does not match its pin never takes the file's place. Several processes may place at once (`_settle`).
    Returns why the release is not in place, or None.
    """
    if platform not in PACK_BUNDLES:
        return f"no pinned grammar bundle for platform {platform}"
    digest, size = PACK_BUNDLES[platform]
    bundle = f"{platform}-{digest}.tar.zst"
    wanted = [("manifest.json", manifest_url(), *PACK_MANIFEST), (f"bundles/{bundle}", bundle_url(platform), digest, size)]
    (home / "libs").mkdir(parents=True, exist_ok=True)
    for rel, url, digest, size in wanted:
        target = home / rel
        if _matches(target, digest, size):
            continue
        source = user_home / rel if user_home is not None else None
        if source is not None and source.is_file() and _settle(
                target, digest, size, lambda private: shutil.copyfile(source, private)):
            continue
        try:
            placed = _settle(target, digest, size, lambda private: fetch(url, private, sha256=digest))
        except (OSError, ValueError) as error:
            return f"download failed: {error}"
        if not placed:
            return f"download failed: checksum mismatch for {url}"
    return None


_PLACED: list[str | None] = []


def _ensure_grammars(pack: Any) -> str | None:
    """Once per process: the pinned release in Daodan's cache and the pack configured on it, or why not."""
    if not _PLACED:
        version = getattr(pack, "__version__", None)
        if version != PACK_VERSION:
            reason = f"tree-sitter-language-pack {version} is installed, Daodan reads with {PACK_VERSION}"
        else:
            user_home, home = _user_pack_home(), _daodan_home()
            reason = place_grammars(home, pack_platform(), user_home, _fetch)
            if reason is None:
                try:
                    pack.configure(pack.PackConfig(cache_dir=str(home / "libs")))
                except Exception as exc:
                    reason = f"{type(exc).__name__}: {exc}"
        _PLACED.append(reason)
    return _PLACED[0]


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

    # Strategy 1: tree-sitter-language-pack (preferred), on the pinned release
    # Daodan placed in its own cache (`_ensure_grammars`).
    #
    # Only `get_parser` is used. The pack's `get_language` returns a plain
    # capsule rather than a `tree_sitter.Language` on newer releases (the
    # package dropped its tree-sitter dependency), so building our own
    # `Parser(get_language(...))` would break there. The parser the pack hands
    # back already carries its language.
    try:
        import tree_sitter_language_pack as _pack  # type: ignore
    except ImportError:
        pass
    else:
        reason = _ensure_grammars(_pack)
        if reason is not None:
            failures[language] = reason
        else:
            try:
                parser = _pack.get_parser(pack_name)
            except Exception as exc:
                # Installed but unusable: a grammar missing from the bundle,
                # or a library that does not load. The reason is kept for the
                # result's notes and the snapshot's declared gap.
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
        _PLACED.clear()


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


def get_tags_query(language: str) -> str | None:
    """Return the bundled tree-sitter tags.scm query from tree-sitter-language-pack when available."""
    pack_name = _LANG_PACK_ALIASES.get(language, language)
    try:
        from tree_sitter_language_pack import get_tags_query as _pack_tags_query  # type: ignore

        return _pack_tags_query(pack_name)
    except Exception:
        return None


def query_tags(language: str, root: Any) -> dict[str, list[Any]]:
    """Run the official tree-sitter tags.scm query for `language` against `root`."""
    sexp = get_tags_query(language)
    return query_captures(language, sexp, root) if sexp else {}


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
    "kotlin": "(call_expression) @call",
    "csharp": "[(invocation_expression) (object_creation_expression)] @call",
    "c": "(call_expression) @call",
    "cpp": "[(call_expression) (new_expression)] @call",
}


def _reference_name(node: Any, source_bytes: bytes) -> str:
    """Render a call target without copying argument literals or comments."""
    if node is None:
        return ""
    if node.type in _CALL_NODE_TYPES:
        name = _callee_name_from_node(node, source_bytes)
        return name + "()" if name else ""
    if node.type == "navigation_suffix":
        children = [c for c in node.named_children if c.type not in _COMMENT_NODE_TYPES]
        return _reference_name(children[-1], source_bytes) if children else ""
    if node.type == "navigation_expression":
        named = [c for c in node.named_children if c.type not in _COMMENT_NODE_TYPES]
        if len(named) >= 2:
            owner_name = _reference_name(named[0], source_bytes)
            member_name = _reference_name(named[-1], source_bytes)
            return f"{owner_name}.{member_name}" if owner_name and member_name else ""
    if node.type in ("member_expression", "member_access_expression", "field_expression", "scoped_identifier", "scoped_type_identifier"):
        owner = (
            node.child_by_field_name("object")
            or node.child_by_field_name("expression")
            or node.child_by_field_name("value")
            or node.child_by_field_name("path")
            or node.child_by_field_name("argument")  # C and C++ `s.f`, `p->f`
        )
        member = (
            node.child_by_field_name("property")
            or node.child_by_field_name("field")
            or node.child_by_field_name("name")
        )
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
        is_err = getattr(node, "type", "") == "ERROR" or getattr(node, "is_missing", False) or (
            getattr(node, "has_error", False) and not getattr(node, "children", None))  # a missing token
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
