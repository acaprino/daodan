"""
C# language adapter. Tree-sitter when available, regex fallback otherwise.
"""

from __future__ import annotations

import re
import threading
from typing import Any

from . import _treesitter
from ._treesitter import (
    check_syntax_errors,
    extract_ast_calls,
    load_failure,
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
from .semantic import csharp_semantics

__all__ = ["adapter"]

_LANGUAGE_NAME = "csharp"

_CSHARP_STDLIB_PREFIXES = (
    "System", "Microsoft.", "Windows.", "Newtonsoft.", "Xunit", "NUnit", "Moq",
)

_DB_HINTS = re.compile(
    r"\b(?:DbContext|DbSet|SqlConnection|SqlCommand|IDbConnection|Dapper|"
    r"ExecuteReader|ExecuteNonQuery|ExecuteScalar|SaveChanges|SaveChangesAsync)\b"
)
_NET_HINTS = re.compile(
    r"\b(?:HttpClient|HttpRequestMessage|WebClient|HttpWebRequest|GrpcChannel|Socket)\b"
)
_FS_HINTS = re.compile(
    r"\b(?:File\.|Directory\.|Path\.|FileStream|StreamReader|StreamWriter)\b"
)
_MSG_HINTS = re.compile(
    r"\b(?:ServiceBusClient|IMessageSession|Channel\.Create|RabbitMQ|Kafka)\b"
)
_IPC_HINTS = re.compile(
    r"\b(?:Process\.Start|ProcessStartInfo|NamedPipeServerStream|Task\.Run)\b"
)


def _is_internal_import(module: str) -> bool:
    return not (module == "System" or module.startswith("System.") or module.startswith(_CSHARP_STDLIB_PREFIXES))


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
    pair = _treesitter.get_parser(_LANGUAGE_NAME)
    if pair is None:
        return None
    parser, _lang = pair
    src = content.encode("utf-8")
    try:
        tree = parser.parse(src)
    except Exception as exc:
        _TS_ERROR_HOLDER["last"] = f"{type(exc).__name__}: {exc}"
        return None

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []

    def text(node: Any) -> str:
        return node_text(node, src)

    def modifiers_info(node: Any, default_vis: str = "private") -> tuple[str, bool, bool, list[str]]:
        vis = default_vis
        is_async = False
        is_static = False
        decos: list[str] = []
        for child in node.named_children:
            if child.type == "attribute_list":
                decos.append(text(child).strip())
            elif child.type == "modifier":
                m = text(child).strip()
                if m in ("public", "private", "protected"):
                    vis = m
                elif m == "internal":
                    vis = "protected"
                elif m == "async":
                    is_async = True
                elif m == "static":
                    is_static = True
        return vis, is_async, is_static, decos

    def extract_params(params_node: Any) -> list[ParameterInfo]:
        out: list[ParameterInfo] = []
        if params_node is None:
            return out
        for child in params_node.named_children:
            if child.type == "parameter":
                pname = child.child_by_field_name("name")
                ptype = child.child_by_field_name("type")
                if pname is not None:
                    out.append(ParameterInfo(
                        name=text(pname).strip(),
                        annotation=text(ptype).strip() if ptype is not None else None,
                    ))
        return out

    def extract_method(node: Any, default_vis: str = "private") -> FunctionInfo:
        vis, is_async, is_static, decos = modifiers_info(node, default_vis=default_vis)
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        ret_node = node.child_by_field_name("returns") or node.child_by_field_name("type")
        body_node = node.child_by_field_name("body")
        if body_node is None:
            body_node = next((c for c in node.named_children if c.type == "arrow_expression_clause"), None)
        return FunctionInfo(
            name=text(name_node).strip() if name_node is not None else "<anonymous>",
            parameters=extract_params(params_node),
            return_annotation=text(ret_node).strip() if ret_node is not None else None,
            is_async=is_async,
            is_staticmethod=is_static,
            visibility=vis,  # type: ignore[arg-type]
            line_number=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            calls_made=extract_ast_calls(body_node, src, _LANGUAGE_NAME),
            decorators=decos,
            signature_fields=("parameters", "annotations", "returns", "async", "decorators"),
        )

    kind_map = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "struct_declaration": "struct",
        "record_declaration": "record",
        "enum_declaration": "enum",
    }

    def walk_declarations(container: Any) -> None:
        for child in container.named_children:
            ct = child.type
            if ct == "using_directive":
                raw = text(child).removeprefix("using").strip().rstrip(";").strip()
                if raw.startswith("static "):
                    raw = raw.removeprefix("static").strip()
                if "=" in raw:
                    alias, target = [p.strip() for p in raw.split("=", 1)]
                    imports.append(ImportInfo(
                        module=target,
                        names=[alias],
                        is_from_import=True,
                        is_internal=_is_internal_import(target),
                    ))
                elif raw:
                    imports.append(ImportInfo(
                        module=raw,
                        names=[raw.rsplit(".", 1)[-1]],
                        is_from_import=False,
                        is_internal=_is_internal_import(raw),
                    ))
            elif ct in ("namespace_declaration", "file_scoped_namespace_declaration"):
                body = child.child_by_field_name("body")
                walk_declarations(body if body is not None else child)
            elif ct in kind_map:
                vis, _, _, decos = modifiers_info(child, default_vis="protected")
                name_node = child.child_by_field_name("name")
                name = text(name_node).strip() if name_node is not None else "<anonymous>"
                bases: list[str] = []
                for sub in child.named_children:
                    if sub.type == "base_list":
                        for b in sub.named_children:
                            bname = text(b).strip()
                            if bname:
                                bases.append(bname)
                methods: list[FunctionInfo] = []
                class_vars: list[str] = []
                attrs: list[ParameterInfo] = []
                default_member_vis = "public" if ct == "interface_declaration" else "private"
                body = child.child_by_field_name("body")
                if body is not None:
                    for member in body.named_children:
                        mt = member.type
                        if mt in ("method_declaration", "constructor_declaration"):
                            methods.append(extract_method(member, default_vis=default_member_vis))
                        elif mt == "property_declaration":
                            pname = member.child_by_field_name("name")
                            ptype = member.child_by_field_name("type")
                            if pname is not None:
                                vname = text(pname).strip()
                                class_vars.append(vname)
                                attrs.append(ParameterInfo(name=vname, annotation=text(ptype).strip() if ptype else None))
                        elif mt == "field_declaration":
                            is_const = any(sc.type == "modifier" and text(sc).strip() == "const" for sc in member.named_children)
                            for sc in member.named_children:
                                if sc.type == "variable_declaration":
                                    ftype = sc.child_by_field_name("type")
                                    for decl in sc.named_children:
                                        if decl.type == "variable_declarator":
                                            vnode = decl.child_by_field_name("name")
                                            if vnode is not None:
                                                vname = text(vnode).strip()
                                                class_vars.append(vname)
                                                attrs.append(ParameterInfo(name=vname, annotation=text(ftype).strip() if ftype else None))
                                                if is_const:
                                                    constants.append(vname)
                        elif mt in kind_map:
                            walk_declarations(body)
                info = ClassInfo(
                    name=name,
                    bases=bases,
                    methods=methods,
                    class_variables=class_vars,
                    kind=kind_map[ct],  # type: ignore[arg-type]
                    visibility=vis,  # type: ignore[arg-type]
                    line_number=child.start_point[0] + 1,
                    end_line=child.end_point[0] + 1,
                    decorators=decos,
                    attributes=attrs,
                    signature_fields=("bases", "decorators", "attributes"),
                )
                classes.append(info)
                if vis == "public":
                    exported.append(name)

    walk_declarations(tree.root_node)

    notes = ["parser=tree-sitter"]
    err = check_syntax_errors(tree.root_node)
    if err:
        notes.append(err)

    return ParseResult(
        file_path="",
        language=_LANGUAGE_NAME,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        exported_symbols=exported,
        external_calls=scan_ast_external_calls(tree.root_node, src, content, _LANGUAGE_NAME, _scan_external_calls),
        notes=notes,
        semantic=csharp_semantics(tree.root_node, src),
    )


_CS_USING_RE = re.compile(r"^\s*using\s+(?:static\s+)?([\w.= ]+)\s*;", re.MULTILINE)
_CS_CLASS_RE = re.compile(
    r"^\s*(?:(?P<vis>public|private|protected|internal)\s+)?(?:sealed\s+|abstract\s+|partial\s+|static\s+)*"
    r"(?P<kind>class|interface|struct|record|enum)\s+(?P<name>\w+)"
    r"(?:\s*\([^)]*\))?(?:\s*:\s*(?P<bases>[^{;]+))?",
    re.MULTILINE,
)


def _regex_parse(content: str) -> ParseResult:
    imports: list[ImportInfo] = []
    for m in _CS_USING_RE.finditer(content):
        raw = m.group(1).strip()
        if "=" in raw:
            alias, target = [p.strip() for p in raw.split("=", 1)]
            imports.append(ImportInfo(module=target, names=[alias], is_from_import=True, is_internal=_is_internal_import(target)))
        else:
            imports.append(ImportInfo(module=raw, names=[raw.rsplit(".", 1)[-1]], is_from_import=False, is_internal=_is_internal_import(raw)))

    classes: list[ClassInfo] = []
    exported: list[str] = []
    for m in _CS_CLASS_RE.finditer(content):
        vis_raw = m.group("vis") or "protected"
        vis = "protected" if vis_raw == "internal" else vis_raw
        name = m.group("name")
        bases = [b.strip() for b in (m.group("bases") or "").split(",") if b.strip()]
        classes.append(ClassInfo(
            name=name,
            bases=bases,
            kind=m.group("kind"),  # type: ignore[arg-type]
            visibility=vis,  # type: ignore[arg-type]
            line_number=content[:m.start()].count("\n") + 1,
        ))
        if vis == "public":
            exported.append(name)

    return ParseResult(
        file_path="",
        language=_LANGUAGE_NAME,
        classes=classes,
        imports=imports,
        exported_symbols=exported,
        external_calls=_scan_external_calls(content),
        notes=["parser=regex-fallback (tree-sitter unavailable)"],
    )


class _CSharpAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        _TS_ERROR_HOLDER.pop("last", None)
        result = _ts_parse(content)
        if result is None:
            result = _regex_parse(content)
            err = _TS_ERROR_HOLDER.pop("last", None)
            if err is not None:
                result.notes.append(f"tree-sitter raised: {err}")
            reason = load_failure(_LANGUAGE_NAME)
            if reason is not None:
                result.notes.append(f"tree-sitter unavailable: {reason}")
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        return len(_CS_USING_RE.findall(content))

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter: _CSharpAdapter = _CSharpAdapter()
