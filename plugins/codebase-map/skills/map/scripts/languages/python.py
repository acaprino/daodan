"""
Python language adapter. Uses the stdlib `ast` module, so it works without
any external dependency.

This module preserves the original ast_parser.py behavior. The other adapters
provide a similar shape but with less detail (decorators, kw-only args, etc.
are Python-specific).
"""

from __future__ import annotations

import ast
import io
import sys
import tokenize

from .base import (
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    NestedDefinition,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken, extract_python_comments
from .semantic import python_semantics

__all__ = ["adapter", "MINIMUM_PYTHON", "require_minimum_interpreter"]


# The stdlib grammar IS the running interpreter's grammar, and its acceptance is
# monotonic: every syntax a version adds is rejected by the older ones, and no
# file is accepted by an older interpreter with a different reading. A too-old
# interpreter therefore fails loudly, one `parse-error` per file, rather than
# putting an invented symbol into the graph. 3.12 is the minimum at which every
# file of the measured corpus parses: three used `type X = ...` (PEP 695) and one
# a nested-quote f-string (PEP 701), both new in 3.12. Measured over 22,536 files
# in evals/codebase-map/python-parser/RESULTS.md, sections 2 and 6.
MINIMUM_PYTHON = (3, 12)

# Cap on prefix re-parses per broken file. Of 1,892 mutated real files, 1,297
# needed one attempt and 7 reached a cap of 60 (RESULTS.md, section 3).
MAX_SALVAGE_ATTEMPTS = 60


def require_minimum_interpreter(entry: str = "the Codebase Map helper suite") -> None:
    """Refuse to run below `MINIMUM_PYTHON`, once, before any file is read.

    The floor is a hard dependency, not advice: the grammar `ast` uses is the
    running interpreter's, so a map run below the floor rejects every file written
    with newer syntax and records it with no symbols. Acceptance is monotonic, so
    the loss is silent per file and total across a project that uses PEP 695 or
    PEP 701.

    A uv-managed invocation satisfies the floor by provisioning an interpreter,
    because the script's PEP 723 header declares `requires-python`. A direct
    `python <script>.py` on an older interpreter ends here with the recovery
    command rather than producing a map that looks complete.
    """
    running = sys.version_info[:2]
    if running < MINIMUM_PYTHON:
        floor = f"{MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}"
        raise SystemExit(
            f"{entry} requires Python {floor} or later; this process is "
            f"{running[0]}.{running[1]}. The Python grammar is the running "
            f"interpreter's, so an older one rejects every file using newer syntax "
            f"and yields no symbols for it. Run the helpers through uv, which "
            f"provisions a compliant interpreter from their `requires-python` "
            f"header (`uv run --no-config --no-project --script <script>.py ...`), "
            f"or install CPython {floor} or later.")

_DEF_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
# PEP 695 `type X = ...` exists from 3.12; on an older interpreter the attribute
# is absent and an alias is simply not a definition this adapter can see.
_TYPE_ALIAS = getattr(ast, "TypeAlias", None)


# ---------------------------------------------------------------------------
# External call detection (preserved from ast_parser.py).
# ---------------------------------------------------------------------------

_DB_METHODS = frozenset([
    "find_one", "find_many", "insert_one", "insert_many",
    "update_one", "update_many", "delete_one", "delete_many",
    "aggregate", "execute", "executemany", "fetchone", "fetchall", "fetchmany",
    "commit", "rollback",
])
_DB_RECEIVERS = frozenset([
    "cursor", "collection", "session", "conn", "connection", "db", "database",
])
_DB_MODULES = frozenset([
    "motor", "beanie", "pymongo", "sqlalchemy", "sqlite3", "psycopg2",
    "asyncpg", "databases", "tortoise", "peewee", "mongoengine",
])
_NETWORK_MODULES = frozenset([
    "aiohttp", "httpx", "requests", "urllib", "urllib3", "grpc",
])
_NETWORK_METHODS = frozenset([
    "get", "post", "put", "delete", "patch", "head", "options", "fetch",
    "request",
])
_NETWORK_CONSTRUCTORS = frozenset([
    "ClientSession", "AsyncClient", "Session", "Client",
])
_FS_METHODS = frozenset([
    "read_text", "write_text", "read_bytes", "write_bytes",
    "mkdir", "rmdir", "unlink", "rename", "replace",
])
_FS_FUNCTIONS = frozenset(["open"])
_FS_MODULES = frozenset(["shutil", "os", "os.path"])
_MSG_METHODS = frozenset([
    "publish", "consume", "subscribe", "basic_publish", "basic_consume",
    "send_message", "receive",
])
_MSG_MODULES = frozenset([
    "kafka", "redis", "celery", "kombu", "pika", "aio_pika", "nats",
])
_IPC_MODULES = frozenset([
    "subprocess", "multiprocessing", "mmap",
])
_IPC_CONSTRUCTORS = frozenset([
    "Popen", "Process", "Pool",
])


def _build_external_prefixes() -> frozenset[str]:
    """
    Build the "treat as external" prefix set from the stdlib plus a curated
    list of common third-party packages. `sys.stdlib_module_names` is Python
    3.10+ and covers every stdlib module name exhaustively, which fixes the
    historical false-positive on `argparse`, `enum`, `sys`, etc.
    """
    stdlib = sys.stdlib_module_names
    third_party = frozenset({
        "pytest", "mock", "requests", "aiohttp", "httpx",
        "pydantic", "sqlalchemy", "django", "flask", "fastapi", "celery",
        "redis", "kafka", "boto3", "numpy", "pandas", "scipy",
    })
    return frozenset(stdlib) | third_party


_COMMON_EXTERNAL_PREFIXES = _build_external_prefixes()


def _annotation_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "?"


def _default_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "..."


def _extract_docstring(node) -> str | None:
    if (
        getattr(node, "body", None)
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value.strip()
    return None


def _decorators(node) -> tuple[bool, bool, bool]:
    is_cm = is_sm = is_prop = False
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            if d.id == "classmethod":
                is_cm = True
            elif d.id == "staticmethod":
                is_sm = True
            elif d.id == "property":
                is_prop = True
    return is_cm, is_sm, is_prop


def _decorator_texts(node) -> list[str]:
    return [_annotation_str(d) or "?" for d in node.decorator_list]


# The stdlib AST holds the whole signature, so every field is extracted.
_FUNCTION_FIELDS = ("parameters", "parameter_kinds", "annotations", "defaults",
                    "returns", "async", "generator", "decorators")
_CLASS_FIELDS = ("bases", "decorators", "attributes")


def _parameters(args: ast.arguments) -> list[ParameterInfo]:
    """Every parameter in declaration order, with how a caller passes it."""
    positional = [*args.posonlyargs, *args.args]
    # Defaults fill the tail of the positional parameters, positional-only ones included.
    first_default = len(positional) - len(args.defaults)
    params: list[ParameterInfo] = []
    for index, arg in enumerate(positional):
        params.append(ParameterInfo(
            name=arg.arg,
            annotation=_annotation_str(arg.annotation),
            default=_default_str(args.defaults[index - first_default]) if index >= first_default else None,
            kind="positional_only" if index < len(args.posonlyargs) else None,
        ))
    if args.vararg is not None:
        params.append(ParameterInfo(name=args.vararg.arg, annotation=_annotation_str(args.vararg.annotation),
                                    kind="var_positional"))
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        params.append(ParameterInfo(name=arg.arg, annotation=_annotation_str(arg.annotation),
                                    default=_default_str(default), kind="keyword_only"))
    if args.kwarg is not None:
        params.append(ParameterInfo(name=args.kwarg.arg, annotation=_annotation_str(args.kwarg.annotation),
                                    kind="var_keyword"))
    return params


def _is_generator(node) -> bool:
    """A yield in the body itself, not in a nested function, class or lambda."""
    stack = list(node.body)
    while stack:
        current = stack.pop()
        if isinstance(current, (ast.Yield, ast.YieldFrom)):
            return True
        if not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            stack.extend(ast.iter_child_nodes(current))
    return False


def _extract_calls_from_ast(node) -> list[str]:
    """Collect distinct outgoing function/method calls inside a Python function body."""
    seen: list[str] = []
    seen_set: set[str] = set()
    body = getattr(node, "body", None) or ()
    stack = list(reversed(body))
    while stack:
        curr = stack.pop()
        if isinstance(curr, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(curr, ast.Call):
            fn = curr.func
            name = ""
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                try:
                    name = ast.unparse(fn)
                except Exception:
                    name = fn.attr
            if name and "\n" not in name and len(name) <= 80 and name not in seen_set:
                seen_set.add(name)
                seen.append(name)
        for child in reversed(list(ast.iter_child_nodes(curr))):
            stack.append(child)
    return seen


def _parse_function(node) -> FunctionInfo:
    is_cm, is_sm, is_prop = _decorators(node)
    return FunctionInfo(
        name=node.name,
        parameters=_parameters(node.args),
        return_annotation=_annotation_str(node.returns),
        is_async=isinstance(node, ast.AsyncFunctionDef),
        is_classmethod=is_cm,
        is_staticmethod=is_sm,
        is_property=is_prop,
        visibility="private" if node.name.startswith("_") and not node.name.startswith("__") else "public",
        docstring=_extract_docstring(node),
        line_number=node.lineno,
        end_line=getattr(node, "end_lineno", None),
        calls_made=_extract_calls_from_ast(node),
        decorators=_decorator_texts(node),
        is_generator=_is_generator(node),
        signature_fields=_FUNCTION_FIELDS,
    )


def _parse_class(node: ast.ClassDef) -> ClassInfo:
    bases: list[str] = []
    # Keyword arguments of the class header (metaclass=...) are part of its contract.
    for base in [*node.bases, *node.keywords]:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            bases.append("?")
    methods: list[FunctionInfo] = []
    class_vars: list[str] = []
    attributes: list[ParameterInfo] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_parse_function(item))
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            class_vars.append(item.target.id)
            attributes.append(ParameterInfo(name=item.target.id, annotation=_annotation_str(item.annotation),
                                            default=_default_str(item.value)))
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    class_vars.append(target.id)
                    attributes.append(ParameterInfo(name=target.id, default=_default_str(item.value)))
    return ClassInfo(
        name=node.name,
        bases=bases,
        methods=methods,
        class_variables=class_vars,
        kind="class",
        visibility="private" if node.name.startswith("_") else "public",
        docstring=_extract_docstring(node),
        line_number=node.lineno,
        end_line=getattr(node, "end_lineno", None),
        decorators=_decorator_texts(node),
        attributes=attributes,
        signature_fields=_CLASS_FIELDS,
    )


def _is_likely_internal(module: str) -> bool:
    if not module:
        return False
    top = module.split(".")[0]
    if top.startswith("_"):
        return True
    if top.lower() in _COMMON_EXTERNAL_PREFIXES:
        return False
    if module.startswith("."):
        return True
    return True


def _parse_imports(tree: ast.Module) -> list[ImportInfo]:
    imports: list[ImportInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportInfo(
                        module=alias.name,
                        names=[alias.asname or alias.name],
                        is_from_import=False,
                        is_internal=_is_likely_internal(alias.name),
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            names = [alias.name for alias in node.names]
            imports.append(
                ImportInfo(
                    module=module,
                    names=names,
                    is_from_import=True,
                    is_internal=_is_likely_internal(module),
                )
            )
    return imports


class _CallVisitor(ast.NodeVisitor):
    def __init__(self, lines: list[str]) -> None:
        self.calls: list[ExternalCallInfo] = []
        self.lines = lines

    def _context(self, lineno: int) -> str:
        if 0 < lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()[:100]
        return ""

    def _parts(self, node: ast.Call) -> tuple[str | None, str | None]:
        func = node.func
        if isinstance(func, ast.Attribute):
            method = func.attr
            if isinstance(func.value, ast.Name):
                return func.value.id, method
            if isinstance(func.value, ast.Attribute):
                try:
                    return ast.unparse(func.value), method
                except Exception:
                    return None, method
            return None, method
        if isinstance(func, ast.Name):
            return None, func.id
        return None, None

    def _classify(self, receiver: str | None, method: str) -> str | None:
        if method in _DB_METHODS:
            if receiver and (receiver in _DB_RECEIVERS or receiver.split(".")[0] in _DB_MODULES):
                return "database"
            if receiver is None:
                return None
            return "database" if receiver in _DB_RECEIVERS else None
        if receiver and receiver.split(".")[0] in _DB_MODULES:
            return "database"
        if receiver and receiver.split(".")[0] in _NETWORK_MODULES:
            return "network"
        if method in _NETWORK_CONSTRUCTORS:
            return "network"
        if method in _NETWORK_METHODS and receiver and receiver.split(".")[0] in _NETWORK_MODULES:
            return "network"
        if method in _FS_FUNCTIONS or method in _FS_METHODS:
            return "filesystem"
        if receiver and receiver.split(".")[0] in _FS_MODULES:
            return "filesystem"
        if method in _MSG_METHODS:
            if receiver and receiver.split(".")[0] in _MSG_MODULES:
                return "messaging"
            return (
                "messaging"
                if receiver
                and any(kw in receiver.lower() for kw in ("channel", "queue", "topic", "producer", "consumer"))
                else None
            )
        if receiver and receiver.split(".")[0] in _MSG_MODULES:
            return "messaging"
        if receiver and receiver.split(".")[0] in _IPC_MODULES:
            return "ipc"
        if method in _IPC_CONSTRUCTORS:
            return "ipc"
        return None

    def visit_Call(self, node: ast.Call) -> None:
        receiver, method = self._parts(node)
        if method is not None:
            call_type = self._classify(receiver, method)
            if call_type:
                pattern = f"{receiver}.{method}" if receiver else method
                self.calls.append(
                    ExternalCallInfo(
                        call_type=call_type,  # type: ignore[arg-type]
                        pattern=pattern,
                        line_number=node.lineno,
                        context=self._context(node.lineno),
                    )
                )
        self.generic_visit(node)


def _find_constants(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    out.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper():
                out.append(node.target.id)
    return out


def _find_exported(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            out.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                out.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    out.append(target.id)
    return out


def _walk_definitions(tree: ast.AST) -> list[tuple[list[str], str | None, ast.AST, bool]]:
    """Every definition in `tree` with its enclosing chain, iteratively.

    Each item is `(chain, parent_kind, node, in_block)`: `chain` holds the
    enclosing class/def names outermost first, `parent_kind` is "class", "def" or
    None at module level, and `in_block` says the definition sits inside a
    compound statement (if/try/with/for/while/match) relative to its nearest
    module/class/def container.

    Iterative because a deep expression in third-party code must not crash the
    run. This is the walker the extraction loss was measured with, so what it
    finds is what the measurement says the adapter dropped: 4.8% to 7.2% of the
    projects' definitions and 8.8% to 9.7% of the libraries'.
    """
    found: list[tuple[list[str], str | None, ast.AST, bool]] = []
    stack = [(child, [], None, False) for child in reversed(list(ast.iter_child_nodes(tree)))]
    while stack:
        node, chain, parent_kind, in_block = stack.pop()
        if isinstance(node, _DEF_TYPES):
            kind = "class" if isinstance(node, ast.ClassDef) else "def"
            found.append((chain, parent_kind, node, in_block))
            names = [*chain, node.name]
            stack.extend(reversed([(child, names, kind, False)
                                   for child in ast.iter_child_nodes(node)]))
        elif _TYPE_ALIAS is not None and isinstance(node, _TYPE_ALIAS):
            found.append((chain, parent_kind, node, in_block))
        elif isinstance(node, ast.stmt):
            # A statement that is not a definition holds definitions only when
            # it is compound, and everything inside it is one block deeper.
            stack.extend(reversed([(child, chain, parent_kind, True)
                                   for child in ast.iter_child_nodes(node)]))
        else:
            stack.extend(reversed([(child, chain, parent_kind, in_block)
                                   for child in ast.iter_child_nodes(node)]))
    return found


def _alias_name(node: ast.AST) -> str:
    name = getattr(node, "name", None)
    return name.id if isinstance(name, ast.Name) else "?"


def _nested_definitions(tree: ast.AST) -> list[NestedDefinition]:
    """The definitions the two top-level lists omit, qualified by their chain.

    Two shapes are excluded because `snapshot.symbol_spans` already records them:
    a definition at module level outside any compound statement, and a direct
    method of a top-level class. Everything else is a node a call can arrive at,
    which is what the resolver prerequisite requires: an engine attached before
    this convention widened produced edges with no arrival node.
    """
    # Match exactly what _build_result/_parse_class already emit. Chain depth
    # alone cannot distinguish a top-level class from one inside an `if` block.
    recorded_methods = {id(method) for node in tree.body if isinstance(node, ast.ClassDef)
                        for method in node.body if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))}
    out: list[NestedDefinition] = []
    for chain, parent_kind, node, in_block in _walk_definitions(tree):
        if _TYPE_ALIAS is not None and isinstance(node, _TYPE_ALIAS):
            info: FunctionInfo | ClassInfo = ClassInfo(
                name=_alias_name(node), kind="type-alias", line_number=node.lineno,
                end_line=getattr(node, "end_lineno", None))
            kind = "type-alias"
            name = info.name
        else:
            if not chain and not in_block:
                continue  # a top-level definition, already in functions/classes
            if id(node) in recorded_methods:
                continue  # a direct method of a top-level class, already recorded
            name = node.name
            if isinstance(node, ast.ClassDef):
                info = _parse_class(node)
                kind = info.kind
            else:
                info = _parse_function(node)
                kind = "method" if parent_kind == "class" else "function"
        out.append(NestedDefinition(qualified_name=".".join([*chain, name]), kind=kind, info=info))
    out.sort(key=lambda item: (item.info.line_number, item.qualified_name))
    return out


def _logical_line_ends(source: str, stop_line: int) -> list[int]:
    """Lines on which a logical line ends, strictly before `stop_line`, newest first."""
    ends: list[int] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.NEWLINE:
                if token.end[0] >= stop_line:
                    break
                ends.append(token.end[0])
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        pass  # the tokenizer stops at the damage; the boundaries found so far are usable
    return sorted(set(ends), reverse=True)


def _salvage_closed_prefix(source: str, error_line: int | None) -> tuple[ast.AST | None, int, int]:
    """Longest parseable prefix ending on a logical line, and where it ends.

    Returns `(tree, cut_line, last_statement_end)`, or `(None, 0, 0)` when no
    prefix before the error parses.

    The caller keeps only the definitions the prefix *closes*, those ending before
    `last_statement_end`: a definition the cut leaves open ends where the parse
    stopped, so its span, and therefore its body hash, would be wrong. Dropping
    those is what makes the policy safe rather than merely productive. Measured on
    1,892 broken real files: 50.16% of names recovered at 100% precision, zero
    truncated spans and zero invented symbols, against 58.14% with 2,218 unsafe
    emissions when open definitions are kept (RESULTS.md, section 3).
    """
    lines = source.splitlines(keepends=True)
    stop = error_line if error_line else len(lines) + 1
    for attempt, cut in enumerate(_logical_line_ends(source, stop)):
        if attempt >= MAX_SALVAGE_ATTEMPTS:
            break
        try:
            tree = ast.parse("".join(lines[:cut]))
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            continue
        last = max((getattr(node, "end_lineno", 0) or 0 for node in tree.body), default=0)
        return tree, cut, last
    return None, 0, 0


def _closes(end_line: int | None, closed_before: int) -> bool:
    """True when a definition ends before the prefix's last statement.

    A definition the cut leaves open ends where the parse stopped, so its span,
    and the body hash derived from it, would be wrong. Callers pass an AST node's
    `end_lineno` or a `FunctionInfo`/`ClassInfo` `end_line`; both are the same
    fact, and neither exists on a regex parser's output.
    """
    return bool(end_line) and end_line < closed_before


def _build_result(content: str, file_path: str, tree: ast.AST, notes: list[str],
                  *, closed_before: int = 0) -> ParseResult:
    """One parse result from a whole tree, or from a salvaged prefix of it.

    `closed_before` is non-zero only for a recovered prefix, and then filters
    every definition the cut may have left open.
    """
    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if closed_before and not _closes(getattr(node, "end_lineno", None), closed_before):
                continue
            parsed = _parse_class(node)
            if closed_before:
                parsed.methods = [m for m in parsed.methods
                                 if _closes(getattr(m, "end_line", None), closed_before)]
            classes.append(parsed)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if closed_before and not _closes(getattr(node, "end_lineno", None), closed_before):
                continue
            functions.append(_parse_function(node))

    visitor = _CallVisitor(content.split("\n"))
    visitor.visit(tree)
    nested = [item for item in _nested_definitions(tree)
              if not closed_before
              or _closes(getattr(item.info, "end_line", None), closed_before)]

    # A prefix of a broken file cannot certify complete reference coverage, so no
    # semantic evidence is produced for it; snapshot.py drops it as well because
    # the syntax-error note keeps the entry at `parse-error`.
    semantic = None
    if not closed_before:
        try:
            semantic = python_semantics(tree)
        except (RecursionError, ValueError, TypeError, AttributeError) as exc:
            notes.append(f"semantic unavailable: {type(exc).__name__}: {exc}")

    return ParseResult(
        file_path=file_path,
        language="python",
        classes=classes,
        functions=functions,
        nested=nested,
        imports=_parse_imports(tree),
        constants=_find_constants(tree),
        external_calls=visitor.calls,
        exported_symbols=_find_exported(tree),
        notes=notes,
        semantic=semantic,
    )


class _PythonAdapter:
    language = "python"

    def parse(self, content: str, file_path: str) -> ParseResult:
        try:
            tree = ast.parse(content)
        except SyntaxError as error:
            return self._recover(content, file_path, error)
        return _build_result(content, file_path, tree, ["parser=stdlib-ast"])

    def _recover(self, content: str, file_path: str, error: SyntaxError) -> ParseResult:
        """Salvage the closed definitions before the damage instead of returning nothing.

        The result keeps the `syntax error:` note, so snapshot.py still records
        `parse-error`: recovery widens what a broken file yields, it never claims
        the file parses.
        """
        notes = ["parser=stdlib-ast", f"syntax error: {error.msg} at line {error.lineno}"]
        tree, cut, last = _salvage_closed_prefix(content, error.lineno)
        result = None
        if tree is None:
            notes.append("recovered prefix: none")
        else:
            result = _build_result(content, file_path, tree, notes, closed_before=last)
            count = (len(result.functions) + len(result.classes) + len(result.nested)
                     + sum(len(item.methods) for item in result.classes))
            notes.append(f"recovered prefix: line {cut}, {count} closed definitions")
        if sys.version_info[:2] < MINIMUM_PYTHON:
            notes.append(
                f"interpreter {sys.version_info[0]}.{sys.version_info[1]} is below the declared "
                f"minimum {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}: the stdlib grammar is the "
                f"interpreter's, so syntax newer than it is rejected and this file may parse "
                f"on a newer one")
        if result is None:
            return ParseResult(file_path=file_path, language="python", notes=notes)
        return result

    def count_imports(self, content: str) -> int:
        import re
        return len(re.findall(r"^(?:from\s+\S+\s+)?import\s+", content, re.MULTILINE))

    def strip_comments_and_blanks(self, content: str) -> int:
        # Mirror the original count_lines: count non-empty, non-comment lines,
        # skipping docstrings.
        lines = content.split("\n")
        code = 0
        in_doc = False
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if '"""' in line or "'''" in line:
                td = line.count('"""')
                ts = line.count("'''")
                if td == 2 or ts == 2:
                    continue
                if td == 1 or ts == 1:
                    in_doc = not in_doc
                    continue
            if in_doc:
                continue
            if line.startswith("#"):
                continue
            code += 1
        return code

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_python_comments(content)


adapter = _PythonAdapter()
