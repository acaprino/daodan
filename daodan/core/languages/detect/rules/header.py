"""`.h`: Objective-C, C++ or C, read from the syntax tree (route R3dx of `benchmarks/header-language`).

In order: Objective-C by its directives; C++ when its grammar finds a declaration C lacks outside a `__cplusplus` block;
else the grammar that errs less, C on a tie. The text read is bounded by a count, never a clock: `detect.MAX_CHARS`
bytes of it, cut before a comment that never closes (the grammars are quadratic on `/* /* /*`). A header whose first C++
declaration lies further reads as C, the suffix's answer, as it does with no grammar. (`benchmarks/header-language`
measures the bound: `results/product.json`.)

Tool: the tree-sitter grammars of C and C++ (`languages._treesitter`), the official parsers of those languages. The few
expressions left read text with no tree: comments and strings, and the directives of Objective-C, which the pack's
Objective-C grammar takes C and C++ headers for.
"""
from __future__ import annotations

import re
from collections import deque


# The only expressions left, on text with no tree to read: comments and strings, and the directives of Objective-C,
# which the pack's Objective-C grammar takes C and C++ headers for (R2o and R3 of the benchmark lose 525 symbols to it).
# No pattern has a way back (possessive `*+`, a comment never closed runs to the end), so each costs in line with the text.
_C_NOISE_RE = re.compile(r'//[^\n]*|/\*.*?(?:\*/|\Z)|(?<!\\)"(?:\\.|[^"\\\n])*+"|(?<!\\)\'(?:\\.|[^\'\\\n])*+\'', re.DOTALL)
_OBJC_HEADER_RE = re.compile(r"^[ \t]*@(?:interface|implementation|protocol|class|property|end)\b", re.MULTILINE)

# What C cannot declare: the nodes of the C++ grammar that C has not, at the level of a declaration, and three that need a look
# at the node (a class with a body, an `enum class`, a struct with a method). Found by walking the tree, not by a query: a query
# over a root with thousands of children of error is quadratic in their number, the walk is not.
_CPP_DECLARATIONS = frozenset({
    "namespace_definition", "namespace_alias_definition", "template_declaration", "template_instantiation", "access_specifier",
    "using_declaration", "alias_declaration", "base_class_clause", "friend_declaration", "concept_definition"})
_BLOCK_HEAD = {"preproc_if": "condition", "preproc_ifdef": "name"}  # where an `#if` block says what it is for


def _method(member) -> bool:
    """A function a struct defines, or a method it declares (a function pointer field has a parenthesized declarator)."""
    return member.type == "function_definition" or member.type == "field_declaration" and any(
        d.type == "function_declarator" and any(n.type == "field_identifier" for n in d.children_by_field_name("declarator"))
        for d in member.children_by_field_name("declarator"))


def _cpp_declaration(node) -> bool:
    kind = node.type
    if kind == "struct_specifier":
        body = node.child_by_field_name("body")
        return body is not None and any(_method(member) for member in body.children)
    return (kind in _CPP_DECLARATIONS or kind == "class_specifier" and node.child_by_field_name("body") is not None
            or kind == "enum_specifier" and any(child.type == "class" for child in node.children))


def _cpp_declared(root) -> bool:
    """Whether the tree has a declaration only C++ makes, outside the `#if` blocks whose head names `__cplusplus` (where a
    C header keeps its C++ for a C++ compiler): one walk, which leaves those blocks out and stops at the first one found."""
    cursor = root.walk()
    while True:
        node = cursor.node
        if _cpp_declaration(node):
            return True
        field = _BLOCK_HEAD.get(node.type)
        head = node.child_by_field_name(field) if field else None
        if not (head is not None and b"__cplusplus" in head.text) and cursor.goto_first_child():
            continue
        while not cursor.goto_next_sibling():
            if not cursor.goto_parent():
                return False


def _head(content: str) -> str:
    """The text the grammars read, without the comment that runs to its end (`/*` with no `*/`: the grammars read the
    rest of the text again at each one, and `detect` can cut a comment open at its bound)."""
    head = content
    last = deque(_C_NOISE_RE.finditer(head), maxlen=1)
    return head[:last[0].start()] if last and last[0].end() == len(head) and last[0].group().startswith("/*") else head


def _parse(language: str, source: bytes):
    from ..._treesitter import get_parser  # imported here: a rule class stays independent of the parser until it asks
    loaded = get_parser(language)
    return loaded[0].parse(source).root_node if loaded else None


def _errors(root) -> int:
    """The ERROR and MISSING nodes of a tree, found where `has_error` says one lies below: a query for them is quadratic on a
    tree that is a flat run of errors (a text of `{`), this is not."""
    count, stack = 0, [root]
    while stack:
        node = stack.pop()
        count += node.type == "ERROR" or node.is_missing
        stack.extend(child for child in node.children if child.has_error)
    return count


class HeaderLanguage:
    """`.h`: C++ or Objective-C by Linguist's name; None for C, which the extension already answers."""
    id = "h.syntax-tree"
    extensions = (".h",)
    languages = ("C++", "Objective-C")
    why = ("A header is C, C++ or Objective-C and its suffix cannot say which: the directives of Objective-C, then a "
           "declaration only C++ has, then the grammar that errs less, C on a tie.")
    source = "Daodan, `languages/header.py` before T1.A.1 (route R3dx of `benchmarks/header-language`)."
    yes = (("namespace a { int x; }\n", "C++"), ("@interface X\n@end\n", "Objective-C"))
    no = ("int a;\n", "struct S { int a; int (*cb)(int); };\n", "")

    def decide(self, text: str) -> str | None:
        if _OBJC_HEADER_RE.search(_C_NOISE_RE.sub(" ", text)):
            return "Objective-C"
        source = _head(text).encode("utf-8", "replace")
        cpp = _parse("cpp", source)
        if cpp is None:
            return None
        if _cpp_declared(cpp):
            return "C++"
        c = _parse("c", source)
        if c is None or not c.has_error:  # no error to count in C: C++ cannot have fewer, and a tie is C
            return None
        return "C++" if _errors(cpp) < _errors(c) else None
