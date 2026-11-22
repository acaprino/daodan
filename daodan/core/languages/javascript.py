"""
JavaScript adapter, read from the Tree-sitter tree; a file whose grammar does not load is reported unread.

Covers: classes, functions (declarations, expressions, arrow), imports (ES6,
CommonJS require), exported symbols, common external API calls (fetch, fs.*,
http.*, mysql/pg/mongoose/sequelize, kafkajs/amqplib/redis, child_process).
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
from .semantic import javascript_semantics

__all__ = ["adapter"]

_LANGUAGE_NAME = "javascript"


_RELATIVE_IMPORT_PREFIXES = ("./", "../", "/", "@/", "~/", "#")


def _is_internal_module(module: str) -> bool:
    """
    Classify a JS/TS import specifier as internal-to-the-project or external.

    Internal: relative path imports (`./foo`, `../bar`, `/baz`) and standard
    project path-alias prefixes (`@/foo`, `~/bar`, `#internal`).
    External: `node:` builtins, scoped npm packages (`@scope/name`), and bare
    npm specifiers (`react`, `lodash/get`).
    """
    if not module:
        return False
    if module.startswith(_RELATIVE_IMPORT_PREFIXES):
        return True
    return False


_DB_RE = re.compile(
    r"\b(?:mysql|pg|pg-promise|mongoose|sequelize|prisma|knex|typeorm|"
    r"mongodb|MongoClient|createConnection|createPool|\.query\(|\.execute\(|"
    r"\.findOne\(|\.findMany\(|\.findAll\(|\.insertOne\(|\.updateOne\(|\.deleteOne\(|"
    r"\.save\(|\.aggregate\()"
)
_NET_RE = re.compile(
    r"\b(?:fetch\(|axios|got\(|node-fetch|http\.(?:get|request)\(|https\.(?:get|request)\(|"
    r"new\s+XMLHttpRequest|new\s+WebSocket|new\s+EventSource|grpc)\b"
)
_FS_RE = re.compile(
    r"\bfs\.(?:readFile|readFileSync|writeFile|writeFileSync|appendFile|unlink|mkdir|rmdir|stat|"
    r"createReadStream|createWriteStream|promises\.)\b"
)
_MSG_RE = re.compile(
    r"\b(?:kafkajs|amqplib|redis|ioredis|bull|bullmq|nats|mqtt|socket\.io|"
    r"\.publish\(|\.subscribe\(|\.consume\(|\.sendMessage\()"
)
_IPC_RE = re.compile(
    r"\b(?:child_process|spawn\(|exec\(|fork\(|cluster\.|worker_threads|"
    r"process\.send\()"
)


def _scan_external_calls(content: str) -> list[ExternalCallInfo]:
    out: list[ExternalCallInfo] = []
    for i, line in enumerate(content.splitlines(), start=1):
        ctx = line.strip()[:100]
        if _DB_RE.search(line):
            out.append(ExternalCallInfo("database", "db-api", i, ctx))
        if _NET_RE.search(line):
            out.append(ExternalCallInfo("network", "net-api", i, ctx))
        if _FS_RE.search(line):
            out.append(ExternalCallInfo("filesystem", "fs-api", i, ctx))
        if _MSG_RE.search(line):
            out.append(ExternalCallInfo("messaging", "msg-api", i, ctx))
        if _IPC_RE.search(line):
            out.append(ExternalCallInfo("ipc", "ipc-api", i, ctx))
    return out


# ---------------------------------------------------------------------------
# Tree-sitter path.
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


def _ts_parse(
    content: str,
    language: str = _LANGUAGE_NAME,
    *,
    pre_parsed: tuple[Any, bytes] | None = None,
) -> ParseResult | None:
    if pre_parsed is not None:
        tree, src = pre_parsed
    else:
        pair = get_parser(language)
        if pair is None:
            return None
        parser, _lang = pair
        src = content.encode("utf-8")
        try:
            tree = parser.parse(src)
        except Exception as e:
            # Tree-sitter MAY raise on extreme input. Signal caller via None.
            _TS_ERROR_HOLDER["last"] = f"{type(e).__name__}: {e}"
            return None

    def text(n: Any) -> str:
        return node_text(n, src)

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    imports: list[ImportInfo] = []
    constants: list[str] = []
    exported: list[str] = []
    default_export: str | None = None

    def parse_params(node: Any) -> list[ParameterInfo]:
        out: list[ParameterInfo] = []
        if node is None:
            return out
        for child in node.children:
            if child.type in ("identifier", "required_parameter", "optional_parameter"):
                # JS typically uses identifier; TS uses required/optional_parameter.
                name_node = child if child.type == "identifier" else child.child_by_field_name("pattern") or child.children[0]
                ann_node = child.child_by_field_name("type") if child.type != "identifier" else None
                default_node = child.child_by_field_name("value") if child.type != "identifier" else None
                out.append(
                    ParameterInfo(
                        name=text(name_node).lstrip(":?"),
                        annotation=text(ann_node).lstrip(":").strip() if ann_node else None,
                        default=text(default_node) if default_node else None,
                        kind="optional" if child.type == "optional_parameter" else None,
                    )
                )
            elif child.type == "rest_pattern":
                out.append(ParameterInfo(name="..." + text(child.children[-1])))
            elif child.type == "assignment_pattern":
                left = child.child_by_field_name("left")
                right = child.child_by_field_name("right")
                out.append(
                    ParameterInfo(
                        name=text(left) if left else "?",
                        default=text(right) if right else None,
                    )
                )
            elif child.type == "object_pattern":
                out.append(ParameterInfo(name="{...}"))
            elif child.type == "array_pattern":
                out.append(ParameterInfo(name="[...]"))
        return out

    def parse_function_like(node: Any, kind: str, default_name: str | None = None) -> FunctionInfo:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        is_async = any(c.type == "async" for c in node.children) or any(
            text(c).strip() == "async" for c in node.children if c.type == "keyword"
        )
        ret_ann = node.child_by_field_name("return_type")
        return FunctionInfo(
            name=default_name or (text(name_node) if name_node else "(anonymous)"),
            parameters=parse_params(params_node),
            return_annotation=text(ret_ann).lstrip(":").strip() if ret_ann else None,
            is_async=is_async,
            line_number=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            calls_made=extract_ast_calls(node.child_by_field_name("body"), src, language),
        )

    def parse_class(node: Any, kind: str = "class") -> ClassInfo:
        name_node = node.child_by_field_name("name")
        bases: list[str] = []
        heritage = node.child_by_field_name("heritage") or None
        if heritage is None:
            # In some grammars heritage clauses are children, not a named field.
            for c in node.children:
                if c.type in ("class_heritage", "extends_clause", "extends_type_clause"):
                    heritage = c
                    break
        if heritage is not None:
            clauses = heritage.named_children if heritage.type == "class_heritage" else [heritage]
            for clause in clauses:
                if clause.type == "extends_clause":
                    # The generic arguments can be a sibling of the base name.
                    bases.append(text(clause).removeprefix("extends").strip())
                elif clause.type in ("implements_clause", "extends_type_clause"):
                    bases.extend(text(c).strip() for c in clause.named_children)
                elif clause.type not in ("extends", "implements"):
                    bases.append(text(clause).strip())
        body = node.child_by_field_name("body")
        methods: list[FunctionInfo] = []
        class_vars: list[str] = []
        if body is not None:
            for child in body.children:
                if child.type in ("method_definition", "method_signature", "abstract_method_signature", "call_signature", "construct_signature"):
                    methods.append(parse_function_like(child, "method"))
                elif child.type in ("field_definition", "public_field_definition", "property_definition", "property_signature"):
                    n = child.child_by_field_name("name") or (child.children[0] if child.children else None)
                    value = child.child_by_field_name("value")
                    if value is not None and value.type in ("arrow_function", "function_expression", "function"):
                        # `handler = (x) => {...}` is a method in everything but syntax.
                        method = parse_function_like(value, "method", default_name=text(n) if n else None)
                        method.line_number = child.start_point[0] + 1
                        methods.append(method)
                    elif n is not None:
                        class_vars.append(text(n))
                elif kind == "enum" and child.type in ("enum_assignment", "property_identifier", "identifier", "string"):
                    n = child.child_by_field_name("name") or child
                    class_vars.append(text(n).strip("'\""))
        return ClassInfo(
            name=text(name_node) if name_node else "?",
            bases=bases,
            methods=methods,
            class_variables=class_vars,
            kind=kind,
            line_number=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
        )

    def wrapped_callable(node: Any) -> Any:
        if node.type in ("arrow_function", "function_expression", "function", "generator_function"):
            return node
        if node.type in ("parenthesized_expression", "as_expression", "satisfies_expression", "non_null_expression"):
            return wrapped_callable(node.named_children[0]) if node.named_children else None
        if node.type == "call_expression":
            callee = node.child_by_field_name("function")
            if callee is None or text(callee) not in ("memo", "forwardRef", "React.memo", "React.forwardRef"):
                return None
            args = node.child_by_field_name("arguments")
            if args is not None and args.named_children:
                return wrapped_callable(args.named_children[0])
        return None

    def qualify(name: str, namespace: str) -> str:
        return f"{namespace}.{name}" if namespace else name

    def walk_for_decls(node: Any, depth: int = 0, in_export: bool = False, namespace: str = "") -> None:
        nonlocal default_export
        for child in node.children:
            t = child.type
            if t == "import_statement":
                source_node = child.child_by_field_name("source")
                if source_node is not None:
                    raw = text(source_node).strip().strip("'\"`")
                    # Collect bound names.
                    names: list[str] = []
                    default_import = None
                    for c in child.children:
                        if c.type == "import_clause":
                            for sub in c.children:
                                if sub.type == "identifier":
                                    names.append(text(sub))
                                    default_import = text(sub)
                                elif sub.type == "named_imports":
                                    for spec in sub.children:
                                        if spec.type == "import_specifier":
                                            id_node = spec.child_by_field_name("name") or spec.children[0]
                                            names.append(text(id_node))
                                elif sub.type == "namespace_import":
                                    id_node = sub.children[-1]
                                    names.append("*" + " as " + text(id_node))
                    imports.append(
                        ImportInfo(
                            module=raw,
                            names=names,
                            is_from_import=True,
                            is_internal=_is_internal_module(raw),
                            default_import=default_import,
                        )
                    )
            elif t == "lexical_declaration" or t == "variable_declaration":
                # Detect CommonJS require: const X = require('mod').
                for sub in child.children:
                    if sub.type == "variable_declarator":
                        val = sub.child_by_field_name("value")
                        if val is not None and val.type == "call_expression":
                            callee = val.child_by_field_name("function")
                            if callee is not None and text(callee) == "require":
                                args = val.child_by_field_name("arguments")
                                if args is not None and len(args.children) >= 2:
                                    arg = args.children[1]
                                    if arg.type == "string":
                                        raw = text(arg).strip("'\"`")
                                        n = sub.child_by_field_name("name")
                                        names_list = [text(n)] if n else []
                                        imports.append(
                                            ImportInfo(
                                                module=raw,
                                                names=names_list,
                                                is_from_import=False,
                                                is_internal=_is_internal_module(raw),
                                            )
                                        )
                # Top-level lexical decls produce constants if UPPER_CASE, and
                # functions when their value is a function: `const f = () => ...`
                # is how most module-level functions are written now.
                if depth == 0 or in_export:
                    for sub in child.children:
                        if sub.type == "variable_declarator":
                            n = sub.child_by_field_name("name")
                            if n is None:
                                continue
                            name = text(n)
                            val = sub.child_by_field_name("value")
                            fn_node = wrapped_callable(val) if val is not None else None
                            if fn_node is not None:
                                fn = parse_function_like(fn_node, "function", default_name=qualify(name, namespace))
                                fn.line_number = sub.start_point[0] + 1
                                fn.end_line = sub.end_point[0] + 1
                                functions.append(fn)
                            elif depth == 0 and name.isidentifier() and name.isupper():
                                constants.append(qualify(name, namespace))
            elif t in ("class_declaration", "abstract_class_declaration", "class", "interface_declaration", "enum_declaration", "type_alias_declaration"):
                kind = {"interface_declaration": "interface", "enum_declaration": "enum", "type_alias_declaration": "type-alias"}.get(t, "class")
                cls = parse_class(child, kind)
                if cls.name == "?" and in_export:
                    cls.name = "default"
                cls.name = qualify(cls.name, namespace)
                classes.append(cls)
                if in_export or (depth == 0 and not namespace and kind == "class"):
                    exported.append(cls.name)
            elif t in ("function_declaration", "generator_function_declaration"):
                fn = parse_function_like(child, "function", default_name="default" if in_export else None)
                # Named export declarations retain their declared identifier.
                name_node = child.child_by_field_name("name")
                if name_node is not None:
                    fn.name = text(name_node)
                fn.name = qualify(fn.name, namespace)
                functions.append(fn)
                if in_export or (depth == 0 and not namespace):
                    exported.append(fn.name)
            elif t == "export_statement":
                # Re-exports: `export { a, b as c } from './mod'` or `export * from './mod'`
                source_node = child.child_by_field_name("source")
                if not namespace and source_node is None and any(c.type == "default" for c in child.children):
                    value = child.child_by_field_name("declaration") or child.child_by_field_name("value")
                    if value is not None:
                        name = value if value.type == "identifier" else value.child_by_field_name("name")
                        if name is not None:
                            default_export = text(name)
                            exported.append(default_export)
                reexport_names: list[str] = []
                for sub in child.children:
                    if sub.type in ("lexical_declaration", "variable_declaration"):
                        for d in sub.children:
                            if d.type == "variable_declarator":
                                n = d.child_by_field_name("name")
                                if n is not None:
                                    exported.append(qualify(text(n), namespace))
                    elif sub.type == "export_clause":
                        for spec in sub.children:
                            if spec.type == "export_specifier":
                                alias_node = spec.child_by_field_name("alias")
                                orig_node = spec.child_by_field_name("name") or (spec.children[0] if spec.children else None)
                                exp_name = text(alias_node) if alias_node is not None else (text(orig_node) if orig_node is not None else "")
                                orig_name = text(orig_node) if orig_node is not None else exp_name
                                if exp_name:
                                    exported.append(qualify(exp_name, namespace))
                                if exp_name == "default" and source_node is None and not namespace:
                                    default_export = orig_name
                                    exported.append(orig_name)
                                if orig_name:
                                    reexport_names.append(orig_name)
                    elif sub.type == "namespace_export":
                        id_node = sub.children[-1] if sub.children else None
                        ns_name = text(id_node) if id_node is not None else "*"
                        exported.append(ns_name)
                        reexport_names.append("* as " + ns_name)
                if source_node is not None:
                    raw = text(source_node).strip().strip("'\"`")
                    if not reexport_names and any(c.type == "*" for c in child.children):
                        reexport_names.append("*")
                    imports.append(
                        ImportInfo(
                            module=raw,
                            names=reexport_names,
                            is_from_import=True,
                            is_internal=_is_internal_module(raw),
                        )
                    )
                walk_for_decls(child, depth + 1, in_export=True, namespace=namespace)
                continue
            elif t in ("internal_module", "module"):
                n = child.child_by_field_name("name")
                body = child.child_by_field_name("body")
                if n is not None and body is not None:
                    name = qualify(text(n).strip("'\""), namespace)
                    classes.append(ClassInfo(name=name, kind="namespace", line_number=child.start_point[0] + 1,
                                             end_line=child.end_point[0] + 1))
                    if in_export:
                        exported.append(name)
                    walk_for_decls(body, depth=0, namespace=name)
                continue
            # Recurse into program-level structures to find functions inside.
            if t == "statement_block":
                walk_for_decls(child, depth + 1, in_export=in_export, namespace=namespace)
            elif t in ("expression_statement", "ambient_declaration"):
                walk_for_decls(child, depth, in_export=in_export, namespace=namespace)

    walk_for_decls(tree.root_node, depth=0)

    notes = ["parser=tree-sitter"]
    syn_err = check_syntax_errors(tree.root_node)
    if syn_err is not None:
        notes.append(syn_err)

    semantic = None
    try:  # a syntax error is read around (`semantic._around`)
        semantic = javascript_semantics(tree.root_node, src, language)
    except (RecursionError, ValueError, TypeError, AttributeError) as exc:
        notes.append(f"semantic unavailable: {type(exc).__name__}: {exc}")
    if semantic is not None:
        existing_mods = {imp.module for imp in imports}
        for item in semantic.get("imports", ()):
            mod = item.get("module") or ""
            if mod.startswith("tauri::command::") and mod not in existing_mods:
                existing_mods.add(mod)
                imports.append(
                    ImportInfo(
                        module=mod,
                        names=[item.get("imported") or mod.removeprefix("tauri::command::")],
                        is_from_import=True,
                        is_internal=True,
                    )
                )

    return ParseResult(
        file_path="",
        language=language,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=scan_ast_external_calls(tree.root_node, src, content, language, _scan_external_calls),
        exported_symbols=list(dict.fromkeys(exported)),
        notes=notes,
        default_export=default_export,
        semantic=semantic,
    )


# ---------------------------------------------------------------------------


class _JavaScriptAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        _TS_ERROR_HOLDER.pop("last", None)
        result = _ts_parse(content, self.language)
        if result is None:
            result = unread(self.language, self.language, _TS_ERROR_HOLDER.pop("last", None))
        result.file_path = file_path
        return result

    def strip_comments_and_blanks(self, content: str) -> int | None:
        return code_lines(content, self.language)

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter = _JavaScriptAdapter()
