"""
C and C++ adapters. Tree-sitter when available; without the grammar, only the includes.

The outline holds the definitions: functions, structs, unions, enums, typedefs and, in C++, classes with the
methods defined in their body, namespaces qualifying what they hold (`geo.Circle`). A member defined outside
its class is a function named `Circle.area`, as Go names a method by its receiver. A prototype has no body, so
it is no symbol of the outline; the semantic facts declare it, with `contract`.

Which headers are C++ is decided by `languages.detect_language`. Annotation macros (`int ZEXPORT inflate(`,
`class TINYXML2_LIB XMLNode {`) break the grammar, so they are blanked before parsing, positions unchanged.
Any other macro the grammar cannot read leaves a syntax error: the outline keeps what parses and the file gets
no semantic facts, as for every language.
"""

from __future__ import annotations

import re
from typing import Any

from ._treesitter import (
    check_syntax_errors,
    extract_ast_calls,
    get_parser,
    load_failure,
    node_text,
    scan_ast_external_calls,
)
from .base import ClassInfo, ExternalCallInfo, FunctionInfo, ImportInfo, NestedDefinition, ParameterInfo, ParseResult
from .comments import CommentToken, extract_c_style_comments
from .semantic import c_callable_name, c_declarator, c_is_static, c_semantics, cpp_semantics

__all__ = ["blank_annotations", "c_adapter", "cpp_adapter", "decorating", "include_contexts", "macro_definitions",
           "prepare"]

# An upper-case word between `class` and the name, or, on a line that starts a top-level definition, between
# the return type and the name, can only be a macro.
ANNOTATIONS = (
    re.compile(rb"\b(?:class|struct|union)\s+([A-Z][A-Z0-9_]*)\s+(?=[A-Za-z_]\w*\s*(?:final\s*)?[:{])"),
    re.compile(rb"(?m)^[A-Za-z_][\w \t*]*?[\w*][ \t]+([A-Z][A-Z0-9_]*)[ \t]+(?=\**[ \t]*[A-Za-z_]\w*[ \t]*\()"),
)
_RECORD_KINDS = {"struct_specifier": "struct", "union_specifier": "union", "class_specifier": "class",
                 "enum_specifier": "enum"}
_INCLUDE_RE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*([<"])([^>"\n]+)[>"]', re.MULTILINE)

_FS_RE = re.compile(r"\b(?:fopen|freopen|fread|fwrite|fclose|open|openat|creat|unlink|remove|rename|mkdir|"
                    r"rmdir|opendir|readdir|stat|lstat|fstat)\s*\(")
_NET_RE = re.compile(r"\b(?:socket|connect|bind|listen|accept|send|sendto|recv|recvfrom|getaddrinfo|"
                     r"gethostbyname)\s*\(")
_IPC_RE = re.compile(r"\b(?:fork|vfork|execl|execlp|execle|execv|execvp|execve|system|popen|pipe|kill|"
                     r"signal|sigaction|CreateProcess\w*)\s*\(")


def blank_annotations(src: bytes) -> bytes:
    """The source with annotation macros replaced by spaces: same length, same positions."""
    for pattern in ANNOTATIONS:
        src = pattern.sub(lambda m: m.group(0)[:m.start(1) - m.start(0)] + b" " * len(m.group(1))
                          + m.group(0)[m.end(1) - m.start(0):], src)
    return src


# ---------------------------------------------------------------------------
# What tree-sitter reads: the source with what the grammar cannot read and the source states is not code
# replaced by spaces, so every position and line stays where it is.
# ---------------------------------------------------------------------------

_DEFINE_RE = re.compile(r"^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)(\(?)((?:[^\n\\]|\\\n|\\.)*)", re.MULTILINE)
_COMMENT_IN_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)
_SPECIFIERS = frozenset({"static", "extern", "inline", "const", "volatile", "register", "restrict", "far", "near",
                         "huge", "_far", "_near", "_huge", "__far", "__near", "__huge", "__inline", "__inline__",
                         "__restrict", "_Noreturn"})
_GROUPS = frozenset({"__attribute__", "__declspec"})
_TOKEN_RE = re.compile(r"\s*(?:(?P<word>[A-Za-z_]\w*)|(?P<open>\()|(?P<close>\))|(?P<string>\"(?:\\.|[^\"\\])*\")"
                       r"|(?P<other>\S))")
_STRING_OR_COMMENT_RE = re.compile(rb"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|(?P<c>/\*.*?\*/|//[^\n]*)",
                                   re.DOTALL)
_DIRECTIVE_RE = re.compile(rb"[ \t]*#[ \t]*(\w*)")
_CPLUSPLUS_RE = re.compile(rb"[ \t]*#[ \t]*(?:(?P<pos>ifdef[ \t]+__cplusplus|if[ \t]+(?:defined[ \t]*\(?[ \t]*)?"
                           rb"__cplusplus[ \t]*\)?)|(?P<neg>ifndef[ \t]+__cplusplus"
                           rb"|if[ \t]+![ \t]*defined[ \t]*\(?[ \t]*__cplusplus[ \t]*\)?))[ \t]*(?:/[/*].*)?$")
_EXTERN_C_BRACE_RE = re.compile(rb'[ \t]*(?:extern[ \t]+"C"[ \t]*\{|\})[ \t]*$')


def macro_definitions(content: str) -> dict[str, list[str | None]]:
    """Every `#define` of a source: the name to each body, comments left out, None for a function-like one."""
    out: dict[str, list[str | None]] = {}
    for m in _DEFINE_RE.finditer(content):
        body = None if m.group(2) else _COMMENT_IN_RE.sub(" ", m.group(3).replace("\\\n", " ")).strip()
        out.setdefault(m.group(1), []).append(body)
    return out


def _shape(body: str) -> str:
    """`empty`, `specifiers` (storage classes, qualifiers, `__attribute__((...))`, `__declspec(...)`), `words` (names
    as well) or `expression` (a number, a string, an operator: never a decoration)."""
    if not body:
        return "empty"
    kinds, depth, position, group = set(), 0, 0, False
    while position < len(body):
        m = _TOKEN_RE.match(body, position)
        if m is None or m.end() == position:
            break
        position = m.end()
        if depth:
            depth += 1 if m.group("open") else -1 if m.group("close") else 0
            continue
        if m.group("word"):
            word = m.group("word")
            kinds.add("specifier" if word in _SPECIFIERS or word in _GROUPS else "word")
            group = word in _GROUPS
        elif m.group("open") and group:
            depth, group = 1, False
        else:
            return "expression"
    return "specifiers" if kinds == {"specifier"} else "words"


def decorating(definitions: dict[str, list[str | None]]) -> tuple[set[str], set[str]]:
    """The macros that only decorate a declaration, and those of them that can make it `static`.

    A macro decorates when no definition is function-like or an expression and at least one expands to nothing
    or to specifiers only: `#define local static`, `#define FAR` beside `#define FAR far`, `#define ZEXTERN extern`.
    A macro that names a type (`#define word unsigned`) or a value (`#define LIMIT 15`) is never one.
    """
    names, statics = set(), set()
    for name, bodies in definitions.items():
        if any(body is None for body in bodies):
            continue
        shapes = {_shape(body) for body in bodies}
        if "expression" in shapes or not shapes & {"empty", "specifiers"}:
            continue
        names.add(name)
        if any(re.search(r"\bstatic\b", body) for body in bodies):
            statics.add(name)
    return names, statics


def include_contexts(files: dict[str, str], resolve) -> dict[str, dict[str, list[str | None]]]:
    """For each file, the macro definitions of the project headers it includes, directly or not.

    `files` maps project paths to their text; `resolve(module, importer)` maps an `#include "module"` to a
    project path or None, as the snapshot resolves includes.
    """
    definitions = {rel: macro_definitions(text) for rel, text in files.items()}
    includes = {rel: [target for target in (resolve(m.group(2), rel) for m in _INCLUDE_RE.finditer(text)
                                            if m.group(1) == '"') if target in files]
                for rel, text in files.items()}
    out = {}
    for rel in files:
        seen, stack = [], list(includes[rel])
        while stack:
            item = stack.pop()
            if item in seen or item == rel:
                continue
            seen.append(item)
            stack.extend(includes[item])
        context: dict[str, list[str | None]] = {}
        for item in sorted(seen):
            for name, bodies in definitions[item].items():
                context.setdefault(name, []).extend(bodies)
        out[rel] = context
    return out


def _spaces(chunk: bytes) -> bytes:
    return bytes(32 if b != 10 else 10 for b in chunk)


def _directives(lines: list[bytes]) -> list[tuple[int, int]]:
    """`(first, last)` line of each preprocessor directive, a continued one included."""
    out, index = [], 0
    while index < len(lines):
        if _DIRECTIVE_RE.match(lines[index]) and lines[index].lstrip().startswith(b"#"):
            first = index
            while lines[index].rstrip().endswith(b"\\") and index + 1 < len(lines):
                index += 1
            out.append((first, index))
        index += 1
    return out


def prepare(src: bytes, language: str, macros: dict | None = None) -> tuple[bytes, list[int]]:
    """The bytes tree-sitter reads, and where a blanked macro could have made a declaration `static`.

    Each change keeps lengths and line breaks: annotation macros of the shape `int ZEXPORT f(`; comments inside
    a continued `#define`; a null directive (`#` alone); in C the `#ifdef __cplusplus` branches, which a C
    compiler never reads, and in C++ the `extern "C" {` and `}` those branches open and close; every macro the
    file or its included headers (`macros`) define as a decoration (see `decorating`).
    """
    src = blank_annotations(src)
    lines = src.split(b"\n")
    directives = _directives(lines)
    in_directive = set()
    for first, last in directives:
        in_directive.update(range(first, last + 1))
        if last > first:  # a continued directive: its comments break the grammar
            block = b"\n".join(lines[first:last + 1])
            block = _STRING_OR_COMMENT_RE.sub(lambda m: _spaces(m.group(0)) if m.group("c") else m.group(0), block)
            lines[first:last + 1] = block.split(b"\n")
        elif re.fullmatch(rb"[ \t]*#[ \t]*(?:/\*.*?\*/[ \t]*|//.*)?", lines[first]):
            lines[first] = _spaces(lines[first])
    # Conditional regions: each `#if`, its `#elif`/`#else` lines and its `#endif`.
    stack, regions = [], []
    for first, _last in directives:
        found = _DIRECTIVE_RE.match(lines[first])
        word = found.group(1) if found else b""  # a null directive, already blanked
        if word in (b"if", b"ifdef", b"ifndef"):
            stack.append([first])
        elif word in (b"elif", b"else") and stack:
            stack[-1].append(first)
        elif word == b"endif" and stack:
            regions.append(stack.pop() + [first])
    blanked = set()
    for region in regions:
        guard = _CPLUSPLUS_RE.match(lines[region[0]])
        if guard is None:
            continue
        branches = list(zip(region[:-1], region[1:]))
        if language == "c":
            chosen = branches[:1] if guard.group("pos") else branches[1:]
        else:
            body = [lines[i] for i in range(region[0] + 1, region[1]) if lines[i].strip()]
            chosen = branches[:1] if guard.group("pos") and len(region) == 2 and len(body) == 1 \
                and _EXTERN_C_BRACE_RE.fullmatch(body[0]) else []
        for start, end in chosen:
            blanked.update(range(start + 1, end))
    for index in blanked:
        lines[index] = _spaces(lines[index])
    names, statics = decorating({**(macros or {}), **{k: (macros or {}).get(k, []) + v for k, v in
                                                     macro_definitions(src.decode("utf-8", "replace")).items()}})
    offsets: list[int] = []
    if names:
        pattern = re.compile(rb"(?<![\w#])(?:" + b"|".join(re.escape(n.encode()) for n in sorted(names)) + rb")(?!\w)")
        position = 0
        for index, line in enumerate(lines):
            if index not in in_directive and index not in blanked:
                def blank(m, base=position):
                    if m.group(0).decode() in statics:
                        offsets.append(base + m.start())
                    return b" " * len(m.group(0))
                lines[index] = pattern.sub(blank, line)
            position += len(line) + 1
    return b"\n".join(lines), offsets


def _scan_external_calls(content: str) -> list[ExternalCallInfo]:
    out: list[ExternalCallInfo] = []
    for i, line in enumerate(content.splitlines(), start=1):
        for call_type, pattern, label in (("filesystem", _FS_RE, "fs-api"), ("network", _NET_RE, "net-api"),
                                          ("ipc", _IPC_RE, "ipc-api")):
            if pattern.search(line):
                out.append(ExternalCallInfo(call_type, label, i, line.strip()[:100]))
    return out


def _include(module: str, quoted: bool) -> ImportInfo:
    return ImportInfo(module=module, names=["*"], is_internal=quoted)


def _ts_parse(content: str, language: str, macros: dict | None) -> tuple[ParseResult | None, str | None]:
    """The parse, or (None, error) when the grammar raised, or (None, None) when absent."""
    pair = get_parser(language)
    if pair is None:
        return None, None
    parser, _lang = pair
    src, statics = prepare(content.encode("utf-8"), language, macros)
    try:
        tree = parser.parse(src)
    except Exception as e:  # parse() is contractually non-raising; degrade to the fallback
        return None, f"{type(e).__name__}: {e}"

    def text(n: Any) -> str:
        return node_text(n, src) if n is not None else ""

    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []
    nested: list[NestedDefinition] = []
    imports: list[ImportInfo] = []
    exported: list[str] = []

    def parameters(declarator: Any) -> list[ParameterInfo]:
        out: list[ParameterInfo] = []
        found = declarator.child_by_field_name("parameters") if declarator is not None else None
        for param in found.named_children if found is not None else ():
            if param.type == "identifier":
                out.append(ParameterInfo(name=text(param)))
            elif param.type == "variadic_parameter":
                out.append(ParameterInfo(name="...", kind="var_positional"))
            elif param.type in ("parameter_declaration", "optional_parameter_declaration",
                                "variadic_parameter_declaration"):
                name, _ = c_declarator(param.child_by_field_name("declarator"))
                kind = param.child_by_field_name("type")
                default = param.child_by_field_name("default_value")
                out.append(ParameterInfo(name=text(name) if name is not None else "_",
                                         annotation=" ".join(text(kind).split()) or None,
                                         default=text(default) if default is not None else None))
        return out

    def function(node: Any) -> FunctionInfo | None:
        name_node, declarator = c_declarator(node.child_by_field_name("declarator"))
        if name_node is None or declarator is None:
            return None
        kind = node.child_by_field_name("type")
        return FunctionInfo(
            name=c_callable_name(name_node, text),
            parameters=parameters(declarator),
            return_annotation=" ".join(text(kind).split()) or None,
            visibility="private" if c_is_static(node, text, statics) else "public",
            line_number=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            calls_made=extract_ast_calls(node.child_by_field_name("body"), src, language),
        )

    def place(qualified: str, kind: str, info: Any, top: list) -> None:
        if "." in qualified and qualified != info.name:
            nested.append(NestedDefinition(qualified_name=qualified, kind=kind, info=info))
        else:
            top.append(info)

    def record(node: Any, prefix: list[str]) -> None:
        """A struct, union, class or enum with a body, and in C++ what its body defines."""
        name_node = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        if node.type not in _RECORD_KINDS or body is None:
            return
        if name_node is None:
            if language == "c":
                members(body, prefix, None, None)
            return
        name = c_callable_name(name_node, text)
        info = ClassInfo(name=name, kind=_RECORD_KINDS[node.type], line_number=node.start_point[0] + 1,
                         end_line=node.end_point[0] + 1,
                         bases=[" ".join(text(c).split()) for clause in node.named_children
                                if clause.type == "base_class_clause" for c in clause.named_children
                                if c.type != "access_specifier"])
        if node.type == "enum_specifier":
            info.class_variables = [text(item.child_by_field_name("name")) for item in body.named_children
                                    if item.type == "enumerator"]
        qualified = ".".join(prefix + [name])
        place(qualified, info.kind, info, classes)
        if not prefix and language == "cpp":
            exported.append(name)
        if node.type != "enum_specifier":
            members(body, prefix, qualified, info)

    def members(body: Any, prefix: list[str], qualified: str | None, info: ClassInfo | None) -> None:
        for member in body.named_children:
            t = member.type
            if t in ("template_declaration", "preproc_if", "preproc_ifdef", "preproc_else", "preproc_elif",
                     "declaration_list"):
                members(member, prefix, qualified, info)
            elif language == "c":  # a tag declared inside a C struct is a file-scope tag
                if t == "field_declaration":
                    record_in(member.child_by_field_name("type"), prefix)
            elif t == "function_definition":
                method = function(member)
                if method is None:
                    continue
                if prefix or "." in (qualified or ""):
                    nested.append(NestedDefinition(f"{qualified}.{method.name}", "method", method))
                else:
                    info.methods.append(method)
            elif t in _RECORD_KINDS:
                record(member, qualified.split("."))
            elif t == "field_declaration":
                record_in(member.child_by_field_name("type"), qualified.split("."))
                for declarator in member.children_by_field_name("declarator"):
                    name, is_function = c_declarator(declarator)
                    if name is not None and is_function is None:
                        info.class_variables.append(text(name))

    def record_in(node: Any, prefix: list[str]) -> None:
        if node is not None and node.type in _RECORD_KINDS:
            record(node, prefix)

    def alias(node: Any, name_node: Any, prefix: list[str]) -> None:
        name = text(name_node)
        info = ClassInfo(name=name, kind="type-alias", line_number=node.start_point[0] + 1,
                         end_line=node.end_point[0] + 1)
        place(".".join(prefix + [name]), "type-alias", info, classes)
        if not prefix:
            exported.append(name)

    def walk(node: Any, prefix: list[str]) -> None:
        for child in node.named_children:
            t = child.type
            if t == "namespace_definition":
                name = child.child_by_field_name("name")
                body = child.child_by_field_name("body")
                if body is not None:
                    walk(body, prefix + text(name).replace("::", " ").split() if name is not None else prefix)
            elif t in ("declaration_list", "linkage_specification", "template_declaration",
                       "template_instantiation") or t.startswith("preproc_") and t != "preproc_include":
                walk(child, prefix)
            elif t == "preproc_include":
                path = child.child_by_field_name("path")
                if path is not None and path.type == "system_lib_string":
                    imports.append(_include(text(path), False))
                elif path is not None and path.type == "string_literal":
                    imports.append(_include(text(path)[1:-1], True))
            elif t == "function_definition":
                info = function(child)
                if info is not None:
                    place(".".join(prefix + [info.name]), "function", info, functions)
                    if not prefix and "." not in info.name and info.visibility == "public":
                        exported.append(info.name)
            elif t in _RECORD_KINDS:
                record(child, prefix)
            elif t in ("declaration", "type_definition", "field_declaration"):
                record_in(child.child_by_field_name("type"), prefix)
                if t == "type_definition":
                    for declarator in child.children_by_field_name("declarator"):
                        name, _ = c_declarator(declarator)
                        if name is not None:
                            alias(child, name, prefix)
            elif t == "alias_declaration" and child.child_by_field_name("name") is not None:
                alias(child, child.child_by_field_name("name"), prefix)

    walk(tree.root_node, [])
    notes = ["parser=tree-sitter"]
    syntax_error = check_syntax_errors(tree.root_node)
    if syntax_error is not None:
        notes.append(syntax_error)
    semantic = None
    if not tree.root_node.has_error:
        try:
            semantic = (c_semantics if language == "c" else cpp_semantics)(tree.root_node, src, statics)
        except (RecursionError, ValueError, TypeError, AttributeError) as exc:
            notes.append(f"semantic unavailable: {type(exc).__name__}: {exc}")
    return ParseResult(
        file_path="",
        language=language,
        classes=classes,
        functions=functions,
        nested=nested,
        imports=imports,
        external_calls=scan_ast_external_calls(tree.root_node, src, content, language, _scan_external_calls),
        exported_symbols=list(dict.fromkeys(exported)),
        notes=notes,
        semantic=semantic,
    ), None


class _CFamilyAdapter:
    def __init__(self, language: str):
        self.language = language

    def parse(self, content: str, file_path: str, macros: dict | None = None) -> ParseResult:
        """`macros`: the definitions of the project headers the file includes (`include_contexts`)."""
        result, error = _ts_parse(content, self.language, macros)
        if result is None:
            result = ParseResult(file_path="", language=self.language, notes=["parser=regex-fallback"],
                                 imports=[_include(m.group(2), m.group(1) == '"') for m in _INCLUDE_RE.finditer(content)],
                                 external_calls=_scan_external_calls(content))
            if error is not None:
                result.notes.append(f"tree-sitter raised: {error}")
            reason = load_failure(self.language)
            if reason is not None:
                result.notes.append(f"tree-sitter unavailable: {reason}")
        result.file_path = file_path
        return result

    def count_imports(self, content: str) -> int:
        return len(_INCLUDE_RE.findall(content))

    def strip_comments_and_blanks(self, content: str) -> int:
        no_blocks = re.sub(r"/\*[\s\S]*?\*/", "", content)
        return sum(1 for line in no_blocks.split("\n") if line.strip() and not line.strip().startswith("//"))

    def extract_comments(self, content: str) -> list[CommentToken]:
        return extract_c_style_comments(content)


c_adapter = _CFamilyAdapter("c")
cpp_adapter = _CFamilyAdapter("cpp")
