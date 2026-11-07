"""
Kotlin language adapter. Tree-sitter when available, regex fallback otherwise.
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
from .semantic import kotlin_semantics

__all__ = ["adapter"]

_LANGUAGE_NAME = "kotlin"

_KOTLIN_STDLIB_PREFIXES = (
    "kotlin.", "kotlinx.", "java.", "javax.", "jakarta.", "android.", "androidx.", "org.jetbrains.",
)

_DB_HINTS = re.compile(
    r"\b(?:Connection|PreparedStatement|ResultSet|EntityManager|JdbcTemplate|RoomDatabase|"
    r"SqlDriver|Exposed|TransactionManager|executeQuery|executeUpdate|transaction)\b"
)
_NET_HINTS = re.compile(
    r"\b(?:HttpClient|OkHttpClient|Retrofit|WebClient|HttpURLConnection|Socket|URL|URI)\b"
)
_FS_HINTS = re.compile(
    r"\b(?:File|FileInputStream|FileOutputStream|Files\.|Paths\.|Path\(|readText|writeText)\b"
)
_MSG_HINTS = re.compile(
    r"\b(?:KafkaProducer|KafkaConsumer|RabbitTemplate|Channel|BroadcastChannel|SharedFlow)\b"
)
_IPC_HINTS = re.compile(
    r"\b(?:ProcessBuilder|Runtime\.getRuntime|CoroutineScope|Dispatchers\.IO)\b"
)


def _is_internal_import(module: str) -> bool:
    return not module.startswith(_KOTLIN_STDLIB_PREFIXES)


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

    def modifiers_info(node: Any) -> tuple[str, bool, list[str]]:
        vis = "public"
        is_suspend = False
        decos: list[str] = []
        for child in node.named_children:
            if child.type == "modifiers":
                for mod in child.named_children:
                    raw = text(mod).strip()
                    if mod.type == "annotation":
                        decos.append(raw)
                    elif raw in ("private", "protected"):
                        vis = raw
                    elif raw == "internal":
                        vis = "protected"
                    elif raw == "suspend":
                        is_suspend = True
        return vis, is_suspend, decos

    def extract_params(params_node: Any) -> list[ParameterInfo]:
        out: list[ParameterInfo] = []
        if params_node is None:
            return out
        for child in params_node.named_children:
            if child.type in ("parameter", "class_parameter", "function_value_parameter"):
                pname_node = next((c for c in child.named_children if c.type == "simple_identifier"), None)
                ptype_node = next((c for c in child.named_children if c.type in ("user_type", "nullable_type", "function_type")), None)
                if pname_node is None and child.type == "function_value_parameter":
                    inner = next((c for c in child.named_children if c.type == "parameter"), None)
                    if inner is not None:
                        pname_node = next((c for c in inner.named_children if c.type == "simple_identifier"), None)
                        ptype_node = next((c for c in inner.named_children if c.type in ("user_type", "nullable_type", "function_type")), None)
                if pname_node is not None:
                    out.append(ParameterInfo(
                        name=text(pname_node).strip(),
                        annotation=text(ptype_node).strip() if ptype_node is not None else None,
                    ))
        return out

    def extract_function(fn_node: Any) -> FunctionInfo:
        vis, is_suspend, decos = modifiers_info(fn_node)
        name_node = next((c for c in fn_node.named_children if c.type == "simple_identifier"), None)
        params_node = next((c for c in fn_node.named_children if c.type == "function_value_parameters"), None)
        body_node = next((c for c in fn_node.named_children if c.type == "function_body"), None)
        ret_node = None
        for c in fn_node.named_children:
            if c.type in ("user_type", "nullable_type", "function_type"):
                if params_node is None or c.start_byte > params_node.end_byte:
                    ret_node = c
                    break
        return FunctionInfo(
            name=text(name_node).strip() if name_node is not None else "<anonymous>",
            parameters=extract_params(params_node),
            return_annotation=text(ret_node).strip() if ret_node is not None else None,
            is_async=is_suspend,
            visibility=vis,  # type: ignore[arg-type]
            line_number=fn_node.start_point[0] + 1,
            end_line=fn_node.end_point[0] + 1,
            calls_made=extract_ast_calls(body_node, src, _LANGUAGE_NAME),
            decorators=decos,
            signature_fields=("parameters", "annotations", "returns", "async", "decorators"),
        )

    def extract_class(cls_node: Any) -> ClassInfo:
        vis, _, decos = modifiers_info(cls_node)
        header_head = src[cls_node.start_byte: min(cls_node.end_byte, cls_node.start_byte + 160)].decode("utf-8", errors="ignore")
        kind = "class"
        if re.search(r"\binterface\b", header_head):
            kind = "interface"
        elif re.search(r"\benum\s+class\b", header_head):
            kind = "enum"
        elif re.search(r"\bannotation\s+class\b", header_head):
            kind = "annotation"
        name_node = next((c for c in cls_node.named_children if c.type in ("type_identifier", "simple_identifier")), None)
        name = text(name_node).strip() if name_node is not None else "<anonymous>"

        bases: list[str] = []
        class_vars: list[str] = []
        attrs: list[ParameterInfo] = []
        methods: list[FunctionInfo] = []

        for child in cls_node.named_children:
            if child.type == "primary_constructor":
                for p in child.named_children:
                    if p.type == "class_parameter":
                        has_val_var = any(sc.type == "binding_pattern_kind" for sc in p.named_children)
                        pname_node = next((sc for sc in p.named_children if sc.type == "simple_identifier"), None)
                        ptype_node = next((sc for sc in p.named_children if sc.type in ("user_type", "nullable_type")), None)
                        if has_val_var and pname_node is not None:
                            vname = text(pname_node).strip()
                            class_vars.append(vname)
                            attrs.append(ParameterInfo(name=vname, annotation=text(ptype_node).strip() if ptype_node else None))
            elif child.type == "delegation_specifier":
                btext = text(child).split("(", 1)[0].strip()
                if btext:
                    bases.append(btext)
            elif child.type in ("class_body", "enum_class_body"):
                for member in child.named_children:
                    if member.type == "function_declaration":
                        methods.append(extract_function(member))
                    elif member.type == "property_declaration":
                        vdecl = next((sc for sc in member.named_children if sc.type == "variable_declaration"), None)
                        if vdecl is not None:
                            vname_node = next((sc for sc in vdecl.named_children if sc.type == "simple_identifier"), None)
                            vtype_node = next((sc for sc in vdecl.named_children if sc.type in ("user_type", "nullable_type")), None)
                            if vname_node is not None:
                                vname = text(vname_node).strip()
                                class_vars.append(vname)
                                attrs.append(ParameterInfo(name=vname, annotation=text(vtype_node).strip() if vtype_node else None))
                    elif member.type in ("class_declaration", "object_declaration"):
                        classes.append(extract_class(member))

        return ClassInfo(
            name=name,
            bases=bases,
            methods=methods,
            class_variables=class_vars,
            kind=kind,  # type: ignore[arg-type]
            visibility=vis,  # type: ignore[arg-type]
            line_number=cls_node.start_point[0] + 1,
            end_line=cls_node.end_point[0] + 1,
            decorators=decos,
            attributes=attrs,
            signature_fields=("bases", "decorators", "attributes"),
        )

    for child in tree.root_node.named_children:
        ct = child.type
        if ct == "import_list":
            for imp in child.named_children:
                if imp.type == "import_header":
                    ident = next((c for c in imp.named_children if c.type == "identifier"), None)
                    alias_node = next((c for c in imp.named_children if c.type == "import_alias"), None)
                    raw_imp = text(imp).removeprefix("import").strip()
                    if ident is not None:
                        mod_path = text(ident).strip()
                        is_wildcard = ".*" in raw_imp
                        sym_name = "*" if is_wildcard else mod_path.rsplit(".", 1)[-1]
                        if alias_node is not None:
                            alias_ident = next((c for c in alias_node.named_children if c.type in ("type_identifier", "simple_identifier")), None)
                            if alias_ident is not None:
                                sym_name = text(alias_ident).strip()
                        imports.append(ImportInfo(
                            module=mod_path,
                            names=[sym_name],
                            is_from_import=True,
                            is_internal=_is_internal_import(mod_path),
                        ))
        elif ct in ("class_declaration", "object_declaration"):
            info = extract_class(child)
            classes.append(info)
            if info.visibility == "public":
                exported.append(info.name)
        elif ct == "type_alias":
            name_node = next((c for c in child.named_children if c.type in ("type_identifier", "simple_identifier")), None)
            if name_node is not None:
                vis, _, _ = modifiers_info(child)
                tname = text(name_node).strip()
                classes.append(ClassInfo(
                    name=tname,
                    kind="type-alias",
                    visibility=vis,  # type: ignore[arg-type]
                    line_number=child.start_point[0] + 1,
                    end_line=child.end_point[0] + 1,
                ))
                if vis == "public":
                    exported.append(tname)
        elif ct == "function_declaration":
            fn = extract_function(child)
            functions.append(fn)
            if fn.visibility == "public":
                exported.append(fn.name)
        elif ct == "property_declaration":
            vis, _, _ = modifiers_info(child)
            vdecl = next((c for c in child.named_children if c.type == "variable_declaration"), None)
            if vdecl is not None:
                vname_node = next((c for c in vdecl.named_children if c.type == "simple_identifier"), None)
                if vname_node is not None:
                    cname = text(vname_node).strip()
                    constants.append(cname)
                    if vis == "public":
                        exported.append(cname)

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
        semantic=kotlin_semantics(tree.root_node, src),
    )


_KT_IMPORT_RE = re.compile(r"^\s*import\s+([\w.]+(?:\.\*)?)", re.MULTILINE)
_KT_CLASS_RE = re.compile(
    r"^\s*(?:(?P<vis>public|private|protected|internal)\s+)?(?:data\s+|sealed\s+|open\s+|abstract\s+|value\s+)?"
    r"(?P<kind>class|interface|object|enum\s+class|annotation\s+class)\s+(?P<name>\w+)"
    r"(?:\s*\([^)]*\))?(?:\s*:\s*(?P<bases>[^{]+))?",
    re.MULTILINE,
)
_KT_FUN_RE = re.compile(
    r"^\s*(?:(?P<vis>public|private|protected|internal)\s+)?(?:override\s+)?(?P<suspend>suspend\s+)?"
    r"fun\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)(?:\s*:\s*(?P<ret>[^\s{=]+))?",
    re.MULTILINE,
)


def _regex_parse(content: str) -> ParseResult:
    imports: list[ImportInfo] = []
    for m in _KT_IMPORT_RE.finditer(content):
        mod = m.group(1)
        imports.append(ImportInfo(
            module=mod.removesuffix(".*"),
            names=["*"] if mod.endswith(".*") else [mod.rsplit(".", 1)[-1]],
            is_from_import=True,
            is_internal=_is_internal_import(mod),
        ))

    classes: list[ClassInfo] = []
    exported: list[str] = []
    for m in _KT_CLASS_RE.finditer(content):
        vis_raw = m.group("vis") or "public"
        vis = "protected" if vis_raw == "internal" else vis_raw
        raw_kind = " ".join(m.group("kind").split())
        kind = "interface" if raw_kind == "interface" else ("enum" if "enum" in raw_kind else ("annotation" if "annotation" in raw_kind else "class"))
        bases = [b.split("(", 1)[0].strip() for b in (m.group("bases") or "").split(",") if b.strip()]
        name = m.group("name")
        classes.append(ClassInfo(
            name=name,
            bases=bases,
            kind=kind,  # type: ignore[arg-type]
            visibility=vis,  # type: ignore[arg-type]
            line_number=content[:m.start()].count("\n") + 1,
        ))
        if vis == "public":
            exported.append(name)

    functions: list[FunctionInfo] = []
    for m in _KT_FUN_RE.finditer(content):
        vis_raw = m.group("vis") or "public"
        vis = "protected" if vis_raw == "internal" else vis_raw
        name = m.group("name")
        functions.append(FunctionInfo(
            name=name,
            return_annotation=m.group("ret"),
            is_async=bool(m.group("suspend")),
            visibility=vis,  # type: ignore[arg-type]
            line_number=content[:m.start()].count("\n") + 1,
        ))
        if vis == "public":
            exported.append(name)

    return ParseResult(
        file_path="",
        language=_LANGUAGE_NAME,
        classes=classes,
        functions=functions,
        imports=imports,
        exported_symbols=exported,
        external_calls=_scan_external_calls(content),
        notes=["parser=regex-fallback (tree-sitter unavailable)"],
    )


class _KotlinAdapter:
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
        return len(_KT_IMPORT_RE.findall(content))

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter: _KotlinAdapter = _KotlinAdapter()
