"""
JavaScript adapter. Tree-sitter when available, regex fallback otherwise.

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
    if not tree.root_node.has_error:
        try:
            semantic = javascript_semantics(tree.root_node, src, language)
        except (RecursionError, ValueError, TypeError, AttributeError) as exc:
            notes.append(f"semantic unavailable: {type(exc).__name__}: {exc}")

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
# Regex fallback.
# ---------------------------------------------------------------------------


_IMPORT_RE = re.compile(
    r"""import\s+(?:(?P<default>\w+)\s*,?\s*)?(?:\{\s*(?P<named>[^}]+)\}\s*)?(?:\*\s*as\s*(?P<ns>\w+)\s*)?(?:from\s+)?['"`](?P<source>[^'"`]+)['"`]""",
    re.MULTILINE | re.DOTALL,
)
_REQUIRE_RE = re.compile(
    r"""(?:const|let|var)\s+(?P<binding>\{[^}]+\}|\w+)\s*=\s*require\(['"`](?P<source>[^'"`]+)['"`]\)""",
    re.MULTILINE,
)
_CLASS_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:abstract\s+)?class\s+(?P<name>\w+)(?:\s+extends\s+(?P<ext>[\w.<>]+))?(?:\s+implements\s+(?P<impl>[\w.,\s<>]+))?\s*\{",
    re.MULTILINE,
)
_FUNC_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?P<async>async\s+)?function\s*\*?\s*(?P<name>\w+)\s*\(",
    re.MULTILINE,
)
_ARROW_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(?P<name>\w+)\s*=\s*(?P<async>async\s+)?\([^)]*\)\s*=>",
    re.MULTILINE,
)
_CONSTANT_RE = re.compile(
    r"^\s*(?:export\s+)?const\s+(?P<name>[A-Z][A-Z0-9_]*)\s*=",
    re.MULTILINE,
)
# Class members. Two forms: the shorthand method `name(args) {`, with the
# modifiers and TypeScript annotations one may carry, and the arrow property
# `name = (args) =>`. Indentation is required, which is what keeps a top-level
# call or statement out: a class member is never at column 0 in either form.
_METHOD_RE = re.compile(
    r"^[ \t]+(?:(?:public|private|protected)\s+)?"
    r"(?:(?:static|readonly|abstract|override|async|declare|get|set)\s+|\*\s*)*"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*"
    r"(?:"
    r"(?:<[^>(]*>)?\((?P<params>[^)]*)\)\s*(?::[^{;=]+)?\{"
    r"|=\s*(?:async\s+)?\((?P<aparams>[^)]*)\)\s*(?::[^=]+)?=>"
    r")",
    re.MULTILINE,
)
# Words that reach _METHOD_RE's shape without being a member: `if (x) {` and its
# relatives read as a call followed by a block.
_NOT_A_METHOD = frozenset({
    "if", "for", "while", "switch", "catch", "do", "else", "try", "finally",
    "with", "return", "function", "typeof", "instanceof", "new", "delete",
    "void", "await", "yield", "case", "throw", "class", "import", "export",
})
_EXPORT_RE = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(?P<name>\w+)",
    re.MULTILINE,
)
_DEFAULT_DECL_RE = re.compile(
    r"^\s*export\s+default\s+(?:(?:abstract\s+)?class|(?:async\s+)?function\s*\*?)\s+(?P<name>[A-Za-z_$][\w$]*)\b",
    re.MULTILINE,
)
_DEFAULT_IDENTIFIER_RE = re.compile(
    r"^\s*export\s+default\s+(?P<name>[A-Za-z_$][\w$]*)\s*(?=;|$)", re.MULTILINE,
)
_EXPORT_CLAUSE_RE = re.compile(
    r"^\s*export\s*\{(?P<names>[^}]*)\}\s*"
    r"(?:(?P<from>from)\s+['\"`](?P<source>[^'\"`]+)['\"`])?", re.MULTILINE,
)


def _regex_parse(content: str, language: str = _LANGUAGE_NAME) -> ParseResult:
    imports: list[ImportInfo] = []
    for m in _IMPORT_RE.finditer(content):
        source = m.group("source")
        names: list[str] = []
        default_import = m.group("default")
        if m.group("default"):
            names.append(m.group("default"))
        if m.group("named"):
            names.extend(n.strip().split(" as ")[0].strip() for n in m.group("named").split(",") if n.strip())
        if m.group("ns"):
            names.append("* as " + m.group("ns"))
        imports.append(
            ImportInfo(
                module=source,
                names=names,
                is_from_import=True,
                is_internal=_is_internal_module(source),
                default_import=default_import,
            )
        )
    for m in _REQUIRE_RE.finditer(content):
        source = m.group("source")
        binding = m.group("binding")
        names: list[str] = []
        if binding.startswith("{"):
            # Preserve destructuring and aliases, as the native adapter does.
            # The resolver distinguishes a named binding from the whole module.
            names = [binding]
        else:
            names = [binding]
        imports.append(
            ImportInfo(
                module=source,
                names=names,
                is_from_import=False,
                is_internal=_is_internal_module(source),
            )
        )

    classes: list[ClassInfo] = []
    for m in _CLASS_RE.finditer(content):
        bases: list[str] = []
        if m.group("ext"):
            bases.append(m.group("ext"))
        if m.group("impl"):
            bases.extend(b.strip() for b in m.group("impl").split(",") if b.strip())
        classes.append(
            ClassInfo(
                name=m.group("name"),
                bases=bases,
                kind="class",
                line_number=content[: m.start()].count("\n") + 1,
            )
        )

    functions: list[FunctionInfo] = []
    for m in _FUNC_RE.finditer(content):
        functions.append(
            FunctionInfo(
                name=m.group("name"),
                is_async=bool(m.group("async")),
                line_number=content[: m.start()].count("\n") + 1,
            )
        )
    for m in _ARROW_RE.finditer(content):
        functions.append(
            FunctionInfo(
                name=m.group("name"),
                is_async=bool(m.group("async")),
                line_number=content[: m.start()].count("\n") + 1,
            )
        )

    # Methods, associated to the nearest preceding class: the same rough
    # association the Java adapter makes. Without this pass a class parsed by
    # the fallback carries no members at all, so snapshot.py records one span
    # for the whole class and an edit to a single method is indistinguishable
    # from an edit to any other.
    if classes:
        by_line = sorted(classes, key=lambda c: c.line_number)
        for m in _METHOD_RE.finditer(content):
            name = m.group("name")
            if name in _NOT_A_METHOD:
                continue
            line_no = content[: m.start()].count("\n") + 1
            owner = None
            for cls in by_line:
                if cls.line_number <= line_no:
                    owner = cls
                else:
                    break
            if owner is None:
                continue
            params_raw = m.group("params")
            if params_raw is None:
                params_raw = m.group("aparams") or ""
            params = [
                ParameterInfo(name=piece.strip().split(":")[0].strip().lstrip("."))
                for piece in params_raw.split(",")
                if piece.strip()
            ]
            owner.methods.append(
                FunctionInfo(
                    name=name,
                    parameters=params,
                    is_async=re.search(r"\basync\b", m.group(0)) is not None,
                    line_number=line_no,
                )
            )

    constants = list({m.group("name") for m in _CONSTANT_RE.finditer(content)})
    exported = list(dict.fromkeys(m.group("name") for m in _EXPORT_RE.finditer(content)))
    default_export = None
    default_match = _DEFAULT_DECL_RE.search(content) or _DEFAULT_IDENTIFIER_RE.search(content)
    if default_match is not None and default_match.group("name") not in ("extends", "function", "class"):
        default_export = default_match.group("name")
    for clause in _EXPORT_CLAUSE_RE.finditer(content):
        if clause.group("from"):
            names = []
            for spec in clause.group("names").split(","):
                parts = re.split(r"\s+as\s+", spec.strip())
                if parts[0]:
                    names.append(parts[0])
                    exported.append(parts[-1])
            source = clause.group("source")
            imports.append(ImportInfo(module=source, names=names, is_from_import=True,
                                      is_internal=_is_internal_module(source)))
            continue
        for spec in clause.group("names").split(","):
            parts = re.split(r"\s+as\s+", spec.strip())
            if len(parts) == 2 and parts[1] == "default" and parts[0].isidentifier():
                default_export = parts[0]
    if default_export is not None and default_export not in exported:
        exported.append(default_export)

    return ParseResult(
        file_path="",
        language=language,
        classes=classes,
        functions=functions,
        imports=imports,
        constants=constants,
        external_calls=_scan_external_calls(content),
        exported_symbols=exported,
        notes=["parser=regex-fallback"],
        default_export=default_export,
    )


# ---------------------------------------------------------------------------


class _JavaScriptAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        _TS_ERROR_HOLDER.pop("last", None)
        result = _ts_parse(content, self.language)
        if result is None:
            result = _regex_parse(content, self.language)
            err = _TS_ERROR_HOLDER.pop("last", None)
            if err is not None:
                result.notes.append(f"tree-sitter raised: {err}")
            reason = load_failure(self.language)
            if reason is not None:
                result.notes.append(f"tree-sitter unavailable: {reason}")
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        return len(_IMPORT_RE.findall(content)) + len(_REQUIRE_RE.findall(content))

    def strip_comments_and_blanks(self, content: str) -> int:
        no_blocks = re.sub(r"/\*[\s\S]*?\*/", "", content)
        code = 0
        for line in no_blocks.split("\n"):
            s = line.strip()
            if not s:
                continue
            if s.startswith("//"):
                continue
            code += 1
        return code

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


adapter = _JavaScriptAdapter()
