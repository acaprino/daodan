"""
Go adapter, read from the Tree-sitter tree; a file whose grammar does not load is reported unread.

Covers package-level `func` declarations, methods, `type` declarations (struct,
interface, alias and defined types), `import` specs, `const` names and a few
categories of external calls.

A method is recorded as a function named `Receiver.Method`, not attached to a
class: Go declares it outside the type, often in another file of the package,
so the receiver type may have no declaration in the file that holds the method.

Go imports name packages (directories) that resolve through the module path in
go.mod. This adapter does not read it, so imports are recorded with
`is_internal` False and the snapshot resolves no cross-file import edges for Go
files, while intra-file semantic scopes, declarations and call references are
extracted when the Tree-sitter grammar is available.

Without the grammar the file is read by nothing: no symbol, and a note with the
reason (`languages/reading.py`). Comment extraction uses the shared C-style
lexer, which does not understand raw (backtick) strings.
"""

from __future__ import annotations

import re
from typing import Any

from ._treesitter import (
    check_syntax_errors,
    extract_ast_calls,
    get_parser,
    node_text,
    scan_ast_external_calls,
)
from .base import (
    ClassInfo,
    ExternalCallInfo,
    FunctionInfo,
    ImportInfo,
    ParameterInfo,
    ParseResult,
)
from .comments import CommentToken, extract_c_style_comments
from .reading import code_lines, unread
from .semantic import go_semantics

__all__ = ["adapter"]

_LANGUAGE_NAME = "go"

# External call categories, matched against `package.Function(` call targets.
_DB_RE = re.compile(
    r"\b(?:sql\.(?:Open|OpenDB)|sqlx\.|gorm\.|pgx\.|pgxpool\.|mongo\.|redis\.)"
    r"|\.(?:QueryRowContext|QueryContext|ExecContext|QueryRow|Query|Exec|Prepare|BeginTx)\("
)
_NET_RE = re.compile(
    r"\bhttp\.(?:Get|Post|PostForm|Head|NewRequest|NewRequestWithContext|ListenAndServe|"
    r"ListenAndServeTLS|Serve)\b|\bnet\.(?:Dial|DialTimeout|Listen)\b|\bgrpc\.(?:Dial|NewClient|NewServer)\b"
)
_FS_RE = re.compile(
    r"\bos\.(?:Open|OpenFile|Create|ReadFile|WriteFile|ReadDir|Remove|RemoveAll|Mkdir|MkdirAll|Rename|Stat)\b"
    r"|\bioutil\.|\bfilepath\.(?:Walk|WalkDir)\b"
)
_MSG_RE = re.compile(r"\b(?:kafka|sarama|amqp|nats|pubsub|sqs|sns)\.")
_IPC_RE = re.compile(r"\bexec\.Command(?:Context)?\b|\bsyscall\.|\bsignal\.Notify\b")


def _scan_external_calls(content: str) -> list[ExternalCallInfo]:
    out: list[ExternalCallInfo] = []
    for i, line in enumerate(content.splitlines(), start=1):
        ctx = line.strip()[:100]
        for call_type, pattern, label in (
            ("database", _DB_RE, "db-api"),
            ("network", _NET_RE, "net-api"),
            ("filesystem", _FS_RE, "fs-api"),
            ("messaging", _MSG_RE, "msg-api"),
            ("ipc", _IPC_RE, "ipc-api"),
        ):
            if pattern.search(line):
                out.append(ExternalCallInfo(call_type, label, i, ctx))
    return out


def _visibility(name: str) -> str:
    """Go exports exactly the identifiers that start with an upper-case letter."""
    return "public" if name[:1].isupper() else "private"


def _receiver_type(raw: str) -> str:
    """`*Invoice`, `Box[T]` and `*Box[T]` name the receiver types Invoice and Box."""
    return raw.strip().lstrip("*").split("[", 1)[0].strip()


# ---------------------------------------------------------------------------
# Tree-sitter path.
# ---------------------------------------------------------------------------


def _ts_parse(content: str) -> tuple[ParseResult | None, str | None]:
    """The parse, or (None, error) when the grammar raised, or (None, None) when absent."""
    pair = get_parser(_LANGUAGE_NAME)
    if pair is None:
        return None, None
    parser, _lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as e:  # parse() is contractually non-raising; report the file unread
        return None, f"{type(e).__name__}: {e}"

    def text(n: Any) -> str:
        return node_text(n, src)

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def parse_params(params_node: Any) -> list[ParameterInfo]:
        out: list[ParameterInfo] = []
        if params_node is None:
            return out
        for child in params_node.children:
            if child.type not in ("parameter_declaration", "variadic_parameter_declaration"):
                continue
            annotation = child.child_by_field_name("type")
            note = text(annotation) if annotation is not None else None
            if child.type == "variadic_parameter_declaration" and note:
                note = "..." + note
            names = child.children_by_field_name("name")
            if names:
                out.extend(ParameterInfo(name=text(n), annotation=note) for n in names)
            else:
                out.append(ParameterInfo(name="_", annotation=note))
        return out

    def parse_function(node: Any, name: str) -> FunctionInfo:
        result = node.child_by_field_name("result")
        return FunctionInfo(
            name=name,
            parameters=parse_params(node.child_by_field_name("parameters")),
            return_annotation=text(result) if result is not None else None,
            visibility=_visibility(name.split(".")[-1]),
            line_number=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            calls_made=extract_ast_calls(node.child_by_field_name("body"), src, _LANGUAGE_NAME),
        )

    def parse_method_name(node: Any) -> str:
        receiver = node.child_by_field_name("receiver")
        declared = next((c for c in receiver.children if c.type == "parameter_declaration"), None) if receiver else None
        type_node = declared.child_by_field_name("type") if declared is not None else None
        name = text(node.child_by_field_name("name"))
        return f"{_receiver_type(text(type_node))}.{name}" if type_node is not None else name

    def parse_struct_fields(struct_node: Any) -> list[str]:
        fields: list[str] = []
        for lst in struct_node.children:
            if lst.type != "field_declaration_list":
                continue
            for field in lst.children:
                if field.type != "field_declaration":
                    continue
                names = field.children_by_field_name("name")
                if names:
                    fields.extend(text(n) for n in names)
                elif field.child_by_field_name("type") is not None:
                    fields.append(text(field.child_by_field_name("type")))  # embedded type
        return fields

    def parse_interface(interface_node: Any) -> tuple[list[str], list[str]]:
        """Method names and embedded interfaces of an interface.

        The methods are signatures without a body, so they are not recorded as
        callables: a one-line signature would be read as an elidable body and
        would push the source reader back to the whole file.
        """
        method_names: list[str] = []
        embedded: list[str] = []
        for child in interface_node.children:
            if child.type == "method_elem" and child.child_by_field_name("name") is not None:
                method_names.append(text(child.child_by_field_name("name")))
            elif child.type == "type_elem":
                embedded.append(text(child))
        return method_names, embedded

    def parse_type_spec(spec: Any) -> None:
        name_node = spec.child_by_field_name("name")
        name = text(name_node) if name_node is not None else "?"
        body = spec.child_by_field_name("type")
        kind, bases, fields = "type", [], []
        if spec.type == "type_alias":
            kind = "type-alias"
        elif body is not None and body.type == "struct_type":
            kind, fields = "struct", parse_struct_fields(body)
        elif body is not None and body.type == "interface_type":
            kind = "interface"
            fields, bases = parse_interface(body)
        classes.append(
            ClassInfo(
                name=name,
                bases=bases,
                class_variables=fields,
                kind=kind,
                visibility=_visibility(name),
                line_number=spec.start_point[0] + 1,
                end_line=spec.end_point[0] + 1,
            )
        )
        if _visibility(name) == "public":
            exported.append(name)

    def parse_import_spec(spec: Any) -> None:
        path = spec.child_by_field_name("path")
        if path is None:
            return
        module = text(path).strip('"`')
        alias = spec.child_by_field_name("name")
        imports.append(
            ImportInfo(
                module=module,
                names=[text(alias) if alias is not None else module.rsplit("/", 1)[-1]],
            )
        )

    for child in tree.root_node.children:
        t = child.type
        if t == "function_declaration":
            fn = parse_function(child, text(child.child_by_field_name("name")))
            functions.append(fn)
            if fn.visibility == "public":
                exported.append(fn.name)
        elif t == "method_declaration":
            fn = parse_function(child, parse_method_name(child))
            functions.append(fn)
            if fn.visibility == "public":
                exported.append(fn.name)
        elif t == "type_declaration":
            for spec in child.children:
                if spec.type in ("type_spec", "type_alias"):
                    parse_type_spec(spec)
        elif t == "import_declaration":
            for node in child.children:
                if node.type == "import_spec":
                    parse_import_spec(node)
                elif node.type == "import_spec_list":
                    for spec in node.children:
                        if spec.type == "import_spec":
                            parse_import_spec(spec)
        elif t == "const_declaration":
            for spec in child.children:
                if spec.type == "const_spec":
                    for n in spec.children_by_field_name("name"):
                        constants.append(text(n))
                        if _visibility(text(n)) == "public":
                            exported.append(text(n))

    notes = ["parser=tree-sitter"]
    syntax_error = check_syntax_errors(tree.root_node)
    if syntax_error is not None:
        notes.append(syntax_error)
    semantic = None
    try:  # a syntax error is read around (`semantic._around`)
        semantic = go_semantics(tree.root_node, src)
    except (RecursionError, ValueError, TypeError, AttributeError) as exc:
        notes.append(f"semantic unavailable: {type(exc).__name__}: {exc}")
    return ParseResult(
        file_path="",
        language=_LANGUAGE_NAME,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=scan_ast_external_calls(tree.root_node, src, content, _LANGUAGE_NAME, _scan_external_calls),
        exported_symbols=list(dict.fromkeys(exported)),
        notes=notes,
        semantic=semantic,
    ), None


# ---------------------------------------------------------------------------


class _GoAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        result, error = _ts_parse(content)
        if result is None:
            result = unread(_LANGUAGE_NAME, _LANGUAGE_NAME, error)
        result.file_path = file_path
        return result

    def strip_comments_and_blanks(self, content: str) -> int | None:
        return code_lines(content, _LANGUAGE_NAME)

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter = _GoAdapter()
