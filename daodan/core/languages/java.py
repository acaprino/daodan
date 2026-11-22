"""
Java language adapter, read from the Tree-sitter tree; a file whose grammar does
not load is reported unread (`languages/reading.py`).
"""

from __future__ import annotations

import re
import threading
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
from .semantic import java_semantics

__all__ = ["adapter"]


_JAVA_STDLIB_PREFIXES = (
    "java.", "javax.", "jakarta.", "sun.", "org.w3c.", "org.xml.",
)


def _is_internal_import(module: str) -> bool:
    return not module.startswith(_JAVA_STDLIB_PREFIXES) and not module.startswith("org.")


# Heuristics for external calls, applied to the callee name of a call node of the tree.
_DB_HINTS = re.compile(
    r"\b(?:Connection|PreparedStatement|Statement|ResultSet|EntityManager|JdbcTemplate|MongoClient|Repository|Session|"
    r"executeQuery|executeUpdate|prepareStatement|createStatement|persist|merge|find|findAll|save|delete)\b"
)
_NET_HINTS = re.compile(
    r"\b(?:HttpClient|HttpRequest|HttpURLConnection|OkHttpClient|WebClient|RestTemplate|"
    r"RestClient|Socket|ServerSocket|URL|URI)\b"
)
_FS_HINTS = re.compile(
    r"\b(?:File|FileInputStream|FileOutputStream|FileReader|FileWriter|Files\.|Paths\.|BufferedReader|BufferedWriter)\b"
)
_MSG_HINTS = re.compile(
    r"\b(?:KafkaProducer|KafkaConsumer|JmsTemplate|RabbitTemplate|MessageProducer|MessageConsumer|"
    r"@KafkaListener|@JmsListener|@RabbitListener)\b"
)
_IPC_HINTS = re.compile(
    r"\b(?:Runtime\.getRuntime\(\)|ProcessBuilder|Process|Thread\.start|ExecutorService|ForkJoinPool)\b"
)


def _scan_external_calls(content: str) -> list[ExternalCallInfo]:
    out: list[ExternalCallInfo] = []
    for i, line in enumerate(content.splitlines(), start=1):
        ctx = line.strip()[:100]
        if _DB_HINTS.search(line):
            out.append(ExternalCallInfo("database", "db-api", i, ctx))
        if _NET_HINTS.search(line):
            out.append(ExternalCallInfo("network", "net-api", i, ctx))
        if _FS_HINTS.search(line):
            out.append(ExternalCallInfo("filesystem", "fs-api", i, ctx))
        if _MSG_HINTS.search(line):
            out.append(ExternalCallInfo("messaging", "msg-api", i, ctx))
        if _IPC_HINTS.search(line):
            out.append(ExternalCallInfo("ipc", "ipc-api", i, ctx))
    return out


# ---------------------------------------------------------------------------
# Tree-sitter extraction.
# ---------------------------------------------------------------------------


class _ThreadLocalErrorHolder:
    def __init__(self) -> None:
        self._local = threading.local()

    def __setitem__(self, key: str, value: str) -> None:
        d = getattr(self._local, "data", None)
        if d is None:
            d = {}
            self._local.data = d
        d[key] = value

    def pop(self, key: str, default: str | None = None) -> str | None:
        d = getattr(self._local, "data", None)
        if d is None:
            return default
        return d.pop(key, default)


_TS_ERROR_HOLDER = _ThreadLocalErrorHolder()


def _ts_parse(content: str) -> ParseResult | None:
    pair = get_parser("java")
    if pair is None:
        return None
    parser, lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as e:
        # Tree-sitter MAY raise on extreme input (deep recursion, encoding).
        # parse() is contractually non-raising; return None to say no tree was
        # read, and record the error so _JavaAdapter can annotate the result's
        # `notes`.
        _TS_ERROR_HOLDER["last"] = f"{type(e).__name__}: {e}"
        return None

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []  # Java methods only exist inside types.
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def text(node: Any) -> str:
        return node_text(node, src)

    def modifiers_of(method_or_field: Any) -> Any:
        mods = method_or_field.child_by_field_name("modifiers")
        if mods is None:
            for child in method_or_field.children:
                if child.type == "modifiers":
                    return child
        return mods

    def parse_modifiers(method_or_field: Any) -> tuple[str | None, bool, bool, bool]:
        # Returns (visibility, is_static, is_final, is_abstract).
        visibility = None
        is_static = is_final = is_abstract = False
        mods = modifiers_of(method_or_field)
        if mods is not None:
            for child in mods.children:
                t = child.type
                if t in ("public", "protected", "private"):
                    visibility = t
                elif t == "static":
                    is_static = True
                elif t == "final":
                    is_final = True
                elif t == "abstract":
                    is_abstract = True
        return visibility, is_static, is_final, is_abstract

    def annotations_of(declaration: Any) -> list[str]:
        mods = modifiers_of(declaration)
        return [text(child) for child in mods.children
                if child.type in ("marker_annotation", "annotation")] if mods is not None else []

    def parse_parameters(params_node: Any) -> list[ParameterInfo]:
        params: list[ParameterInfo] = []
        if params_node is None:
            return params
        for child in params_node.children:
            if child.type == "formal_parameter":
                ann_node = child.child_by_field_name("type")
                name_node = child.child_by_field_name("name")
                params.append(
                    ParameterInfo(
                        name=text(name_node) if name_node else "?",
                        annotation=text(ann_node) if ann_node else None,
                        default=None,
                    )
                )
            elif child.type == "spread_parameter":
                # `String... rest` has no type or name field: a type node, the
                # ellipsis and a variable_declarator holding the name.
                declarator = next((c for c in child.named_children if c.type == "variable_declarator"), None)
                type_node = next((c for c in child.named_children
                                  if c.type not in ("modifiers", "variable_declarator")), None)
                name_node = declarator.child_by_field_name("name") if declarator is not None else None
                params.append(ParameterInfo(
                    name=text(name_node) if name_node else "?",
                    annotation=text(type_node) + "..." if type_node is not None else None,
                    kind="var_positional",
                ))
        return params

    def parse_method(node: Any) -> FunctionInfo:
        name_node = node.child_by_field_name("name")
        ret_node = node.child_by_field_name("type")
        params_node = node.child_by_field_name("parameters")
        visibility, is_static, _is_final, _is_abstract = parse_modifiers(node)
        return FunctionInfo(
            name=text(name_node) if name_node else "?",
            parameters=parse_parameters(params_node),
            return_annotation=text(ret_node) if ret_node else None,
            is_async=False,  # Java has no async keyword - reactive code is by API.
            is_classmethod=False,
            is_staticmethod=is_static,
            is_property=False,
            visibility=visibility,
            docstring=None,
            line_number=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            calls_made=extract_ast_calls(node.child_by_field_name("body"), src, "java"),
            decorators=annotations_of(node),
        )

    def parse_class_like(node: Any, kind: str) -> ClassInfo:
        name_node = node.child_by_field_name("name")
        bases: list[str] = []
        superclass = node.child_by_field_name("superclass")
        if superclass is not None:
            bases.append(text(superclass).removeprefix("extends").strip())
        interfaces = node.child_by_field_name("interfaces")
        if interfaces is not None:
            txt = text(interfaces).removeprefix("implements").strip()
            for piece in txt.split(","):
                piece = piece.strip()
                if piece:
                    bases.append(piece)
        # Methods + class variables come from the body.
        methods: list[FunctionInfo] = []
        class_vars: list[str] = []
        body = node.child_by_field_name("body")

        def collect_body_members(container: Any) -> None:
            for child in container.children:
                if child.type == "method_declaration":
                    methods.append(parse_method(child))
                elif child.type in ("constructor_declaration", "compact_constructor_declaration"):
                    m = parse_method(child)
                    m.name = m.name or text(name_node)
                    methods.append(m)
                elif child.type == "enum_constant":
                    cn = child.child_by_field_name("name") or (child.children[0] if child.children else None)
                    if cn is not None:
                        cname = text(cn)
                        class_vars.append(cname)
                        if cname.isupper():
                            constants.append(cname)
                elif child.type == "enum_body_declarations":
                    collect_body_members(child)
                elif child.type == "field_declaration":
                    for sub in child.children:
                        if sub.type == "variable_declarator":
                            n = sub.child_by_field_name("name")
                            if n is not None:
                                fname = text(n)
                                class_vars.append(fname)
                                if fname.isupper():
                                    constants.append(fname)
                elif child.type in (
                    "class_declaration",
                    "interface_declaration",
                    "enum_declaration",
                    "record_declaration",
                    "annotation_type_declaration",
                ):
                    # Nested types are types: a listener interface or a builder
                    # class declared inside its owner is part of the surface.
                    sub_kind = "annotation" if child.type == "annotation_type_declaration" else child.type.removesuffix("_declaration")
                    nested = parse_class_like(child, sub_kind)
                    if name_node is not None:
                        nested.name = f"{text(name_node)}.{nested.name}"
                    classes.append(nested)

        if body is not None:
            collect_body_members(body)
        # Java records also declare component fields in `parameters` (formal_parameters).
        if kind == "record":
            rec_params = node.child_by_field_name("parameters")
            if rec_params is not None:
                for p in rec_params.children:
                    if p.type == "formal_parameter":
                        pn = p.child_by_field_name("name")
                        if pn is not None:
                            fname = text(pn)
                            if fname not in class_vars:
                                class_vars.append(fname)
        visibility, _is_static, _is_final, _is_abstract = parse_modifiers(node)
        return ClassInfo(
            name=text(name_node) if name_node else "?",
            bases=bases,
            methods=methods,
            class_variables=class_vars,
            kind=kind,
            visibility=visibility,
            docstring=None,
            line_number=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            decorators=annotations_of(node),
        )

    # Walk top-level only for declarations.
    root = tree.root_node
    for child in root.children:
        if child.type == "import_declaration":
            full = text(child).removeprefix("import").strip().rstrip(";").strip()
            is_static = full.startswith("static ")
            if is_static:
                full = full.removeprefix("static").strip()
            module = full.rsplit(".", 1)[0] if "." in full else full
            name = full.rsplit(".", 1)[-1]
            imports.append(
                ImportInfo(
                    module=module,
                    names=[name],
                    is_from_import=True,
                    is_internal=_is_internal_import(module),
                )
            )
        elif child.type == "class_declaration":
            c = parse_class_like(child, "class")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "interface_declaration":
            c = parse_class_like(child, "interface")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "enum_declaration":
            c = parse_class_like(child, "enum")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "record_declaration":
            c = parse_class_like(child, "record")
            classes.append(c)
            if c.visibility == "public" or c.visibility is None:
                exported.append(c.name)
        elif child.type == "annotation_type_declaration":
            c = parse_class_like(child, "annotation")
            classes.append(c)

    notes = ["parser=tree-sitter"]
    syn_err = check_syntax_errors(root)
    if syn_err is not None:
        notes.append(syn_err)

    semantic = None
    try:  # a syntax error is read around (`semantic._around`)
        semantic = java_semantics(root, src)
    except (RecursionError, ValueError, TypeError, AttributeError) as exc:
        notes.append(f"semantic unavailable: {type(exc).__name__}: {exc}")

    return ParseResult(
        file_path="",
        language="java",
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=scan_ast_external_calls(root, src, content, "java", _scan_external_calls),
        exported_symbols=exported,
        notes=notes,
        semantic=semantic,
    )


# ---------------------------------------------------------------------------


class _JavaAdapter:
    language = "java"

    def parse(self, content: str, file_path: str) -> ParseResult:
        _TS_ERROR_HOLDER.pop("last", None)
        result = _ts_parse(content)
        if result is None:
            result = unread("java", "java", _TS_ERROR_HOLDER.pop("last", None))
        result.file_path = file_path
        return result

    def strip_comments_and_blanks(self, content: str) -> int | None:
        return code_lines(content, "java")

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter = _JavaAdapter()
