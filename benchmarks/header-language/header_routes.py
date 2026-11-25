"""The routes of the header-language benchmark as decisions over the features of a parse, and the statistics.

A header is parsed by the C, the C++ and the Objective-C grammars (`header_probe.features`); each route is a function
of what those parses found, so one parse of each serves every route and variant, and the cost of a route is the sum of
the parses it needs. Standard library only: `test_header_language.py` runs without tree-sitter.

Features of a header (what `header_probe.features` returns):

    {"size": bytes,
     "c":    {"ms", "err", "missing", "err_bytes"},
     "cpp":  {"ms", "err", "missing", "err_bytes", "q_ms", "kinds": {kind: [total, outside a __cplusplus block]}},
     "objc": {... the same, with the Objective-C kinds}}

`err` counts the ERROR nodes of the tree, `missing` its MISSING nodes, `err_bytes` the bytes the ERROR nodes cover.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from functools import partial
from typing import Iterable

# Named nodes of the C++ grammar that the C grammar has not (tree-sitter-language-pack 1.13.5, `node_kind_count` of the
# two languages, the difference: `test_header_probe.py` computes it again and fails if this list differs).
CPP_ONLY_NAMED = frozenset("""
abstract_reference_declarator access_specifier alias_declaration annotation auto base_class_clause catch_clause
class_specifier co_await_expression co_return_statement co_yield_statement compound_requirement concept_definition
condition_clause consteval_block_declaration constraint_conjunction constraint_disjunction decltype
default_method_clause delete_expression delete_method_clause dependent_name dependent_type destructor_name
expansion_statement explicit_function_specifier explicit_object_parameter_declaration export_declaration
field_initializer field_initializer_list fold_expression for_range_loop friend_declaration
global_module_fragment_declaration import_declaration init_statement lambda_capture_initializer
lambda_capture_specifier lambda_declarator lambda_default_capture lambda_expression lambda_specifier literal_suffix
module_declaration module_name module_partition namespace_alias_definition namespace_definition namespace_identifier
nested_namespace_specifier new_declarator new_expression noexcept operator_cast operator_name
optional_parameter_declaration optional_type_parameter_declaration parameter_pack_expansion
placeholder_type_specifier pointer_type_declarator private_module_fragment_declaration pure_virtual_clause
qualified_identifier raw_string_content raw_string_delimiter raw_string_literal ref_qualifier reference_declarator reflect_expression
requirement_seq requires_clause requires_expression simple_requirement splice_expression splice_specifier
splice_type_specifier static_assert_declaration structured_binding_declarator subscript_argument_list
template_argument_list template_declaration template_function template_instantiation template_method
template_parameter_list template_template_parameter_declaration template_type this throw_specifier throw_statement
trailing_return_type try_statement type_parameter_declaration type_requirement user_defined_literal using_declaration
variadic_declarator variadic_parameter_declaration variadic_type_parameter_declaration virtual_specifier
""".split())

# What a C header cannot hold, at the level of a declaration: the "d" tier. The first four patterns are not node kinds
# of their own: `class_with_body` is a class_specifier with a body (a forward `class A;` is not), `struct_fn_def` and
# `struct_fn_decl` a struct that defines or declares a member function (`field_identifier` names it: a function
# pointer field has a parenthesized declarator instead), `enum_class` an `enum class`.
SYNTHETIC_CPP = frozenset({"class_with_body", "struct_fn_def", "struct_fn_decl", "enum_class"})
CPP_DECL = frozenset(SYNTHETIC_CPP | {
    "namespace_definition", "namespace_alias_definition", "template_declaration", "template_instantiation",
    "access_specifier", "using_declaration", "alias_declaration", "base_class_clause", "friend_declaration",
    "concept_definition",
})
# The "e" tier adds what C++ writes inside a declaration or a body and C does not: a bare class, a `a::b` name, a
# reference, new/delete, a lambda, exceptions, operator and destructor names, the member specifiers, template names.
CPP_EXT = frozenset(CPP_DECL | {
    "class_specifier", "qualified_identifier", "reference_declarator", "abstract_reference_declarator",
    "new_expression", "delete_expression", "lambda_expression", "try_statement", "throw_statement", "catch_clause",
    "operator_name", "operator_cast", "destructor_name", "field_initializer_list", "virtual_specifier",
    "explicit_function_specifier", "noexcept", "throw_specifier", "trailing_return_type", "ref_qualifier",
    "pure_virtual_clause", "default_method_clause", "delete_method_clause", "template_type", "template_function",
    "template_method", "requires_clause", "requires_expression",
})
# The "a" tier is every C++-only node, the weak ones too (`auto`, `this`, `static_assert`: C23 and C11 have them).
CPP_ALL = frozenset(CPP_ONLY_NAMED | SYNTHETIC_CPP)

# Objective-C: the `@` declarations (a class, a protocol, a property, a method, `@import`) and, in the "e" tier, its
# expressions and the `#import` directive (`import_directive`, a synthetic pattern of the probe).
OBJC_DECL = frozenset({
    "class_interface", "class_implementation", "protocol_declaration", "protocol_forward_declaration",
    "class_declaration", "property_declaration", "method_declaration", "method_definition", "module_import",
    "compatibility_alias_declaration", "qualified_protocol_interface_declaration", "implementation_definition",
})
OBJC_EXT = frozenset(OBJC_DECL | {
    "message_expression", "at_expression", "selector_expression", "encode_expression", "array_literal",
    "dictionary_literal", "block_literal", "synchronized_statement", "instance_variables", "generic_arguments",
    "import_directive",
})
GRAMMARS = ("c", "cpp", "objc")
_CPP_TIER = {"d": CPP_DECL, "e": CPP_EXT, "a": CPP_ALL}
_OBJC_TIER = {"d": OBJC_DECL, "e": OBJC_EXT, "a": OBJC_EXT}


def _found(kinds: dict, tier: frozenset, guarded: bool) -> bool:
    column = 1 if guarded else 0  # [total, outside a __cplusplus block]
    return any(kinds.get(kind, (0, 0))[column] for kind in tier)


def _r1(tier: str, guarded: bool, objc: bool, f: dict) -> str:
    if objc and _found(f["objc"]["kinds"], _OBJC_TIER[tier], False):
        return "objc"
    return "cpp" if _found(f["cpp"]["kinds"], _CPP_TIER[tier], guarded) else "c"


def _score(f: dict, grammar: str, weighted: bool) -> int:
    part = f[grammar]
    return (part["err_bytes"] if weighted else part["err"]) + part["missing"]


def _r2(grammars: tuple[str, ...], weighted: bool, f: dict) -> str:
    scores = [(_score(f, g, weighted), i, g) for i, g in enumerate(grammars)]
    return min(scores)[2]  # the fewest errors; a tie goes to the first grammar: C, then C++, then Objective-C


def _r3(tier: str, grammars: tuple[str, ...], f: dict) -> str:
    return "cpp" if _found(f["cpp"]["kinds"], _CPP_TIER[tier], True) else _r2(grammars, False, f)


def _x(inner, f: dict) -> str:
    """Today's Objective-C rule in front, the tree after: `f["r0"]` is the record's answer of today's rule, which the
    scorer adds to the features. A header it calls Objective-C is not parsed at all."""
    return "objc" if f["r0"] == "objc" else inner(f)


ROUTES = {
    **{f"R1{t}{'g' if g else ''}{'o' if o else ''}": partial(_r1, t, g, o)
       for t in "dea" for g in (False, True) for o in (False, True)},
    "R2": partial(_r2, ("c", "cpp"), False),
    "R2b": partial(_r2, ("c", "cpp"), True),
    "R2o": partial(_r2, GRAMMARS, False),
    "R2ob": partial(_r2, GRAMMARS, True),
    "R3": partial(_r3, "e", GRAMMARS),
    "R3d": partial(_r3, "d", GRAMMARS),
    # the routes of the trees with today's Objective-C rule in front and no Objective-C grammar (`x`), and no guard
    "R1dx": partial(_x, partial(_r1, "d", False, False)),
    "R1ex": partial(_x, partial(_r1, "e", False, False)),
    "R3dx": partial(_x, partial(_r3, "d", ("c", "cpp"))),
}
# which grammars' parses a route needs: its cost is the sum of theirs (R0 is timed as it runs)
NEEDS = {name: ("cpp", "objc") if name.endswith("o") and name.startswith("R1") else ("cpp",)
         for name in ROUTES if name.startswith("R1")}
NEEDS.update({"R2": ("c", "cpp"), "R2b": ("c", "cpp"), "R2o": GRAMMARS, "R2ob": GRAMMARS, "R3": GRAMMARS, "R3d": GRAMMARS,
              "R3dx": ("c", "cpp")})


def needs(route: str, f: dict) -> tuple[str, ...]:
    """The grammars a route parses with for this header (`f` holds `r0` for the `x` routes): R3 stops at the C++ parse
    when that parse has a node of its tier, and an `x` route stops before any parse where today's rule says Objective-C."""
    if route.endswith("x") and f["r0"] == "objc":
        return ()
    if route.startswith("R3") and _found(f["cpp"]["kinds"], _CPP_TIER["e" if route == "R3" else "d"], True):
        return ("cpp",)
    return NEEDS[route]


def decide(route: str, features: dict) -> str:
    return ROUTES[route](features)


# ---- statistics ---------------------------------------------------------------------------------------------

def correct(truth: str, answer: str) -> bool:
    """`either` (nothing in the header tells C from C++) takes any answer; the others take their own."""
    return truth == "either" or truth == answer


def matrix(pairs: Iterable[tuple[str, str]]) -> dict[str, dict[str, int]]:
    out: dict[str, Counter] = defaultdict(Counter)
    for truth, answer in pairs:
        out[truth][answer] += 1
    return {truth: dict(row) for truth, row in out.items()}


def accuracy(m: dict[str, dict[str, int]]) -> dict[str, tuple[int, int]]:
    return {truth: (sum(n for answer, n in row.items() if correct(truth, answer)), sum(row.values()))
            for truth, row in m.items()}


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("no values")
    ordered = sorted(values)
    k = (len(ordered) - 1) * p / 100
    low, high = math.floor(k), math.ceil(k)
    return ordered[low] + (ordered[high] - ordered[low]) * (k - low)


def growth(times: dict[int, float]) -> list[tuple[int, float]]:
    """t(2n)/t(n) for every size whose double was timed too: 2.0 is linear, 4.0 quadratic, 8.0 cubic."""
    return [(n, times[2 * n] / times[n]) for n in sorted(times) if 2 * n in times and times[n] > 0]


def union_length(spans: Iterable[tuple[int, int]]) -> int:
    """The bytes covered by a set of (start, end) spans, nested and overlapping ones counted once."""
    total, end = 0, -1
    for start, stop in sorted(spans):
        if stop <= end:
            continue
        total += stop - max(start, end)
        end = stop
    return total


def symbol_loss(counts: dict[str, int], truth: str, answer: str) -> int:
    """The symbols the true reading extracts and the answered one does not (counts of each reading, same header).
    An `objc` answer is a header the snapshot does not read: all of the true reading's symbols are lost."""
    if truth not in ("c", "cpp") or truth == answer:
        return 0
    if answer == "objc":
        return counts[truth]
    return max(0, counts[truth] - counts[answer])


def exponent(times: dict[int, float]) -> float | None:
    """The slope of log(time) over log(size) between the smallest and the biggest size timed: 1 is linear, 2 quadratic.
    None when fewer than two sizes were timed or the smallest took no time."""
    sizes = sorted(times)
    if len(sizes) < 2 or times[sizes[0]] <= 0 or times[sizes[-1]] <= 0:
        return None
    return math.log(times[sizes[-1]] / times[sizes[0]]) / math.log(sizes[-1] / sizes[0])


# ---- bad texts, and the linear check of an open comment --------------------------------------------------

BAD_KINDS = ("blank_lines", "open_comment", "open_comment_repeat", "open_comment_lines", "class_repeat",
             "nested_brace", "open_string", "escaped_dq", "escaped_sq")
_FILLER = " some words of a text that never closes its comment or its string\n"
_BAD = {
    "blank_lines": ("", "  \n"),
    "open_comment": ("/*", _FILLER),  # one `/*` never closed: linear
    "open_comment_repeat": ("", "/* "),  # `/*` over and over, none closed: what makes the grammars quadratic
    "open_comment_lines": ("int a;\n", "/* x\n"),  # one a line, after code
    "class_repeat": ("", "class a "),
    "nested_brace": ("", "{"),
    "open_string": ('"', _FILLER),
    "escaped_dq": ('"', '\\"'),  # a `"` and then `\"` over and over: a string that starts at every quote
    "escaped_sq": ("'", "\\'"),  # the same with `'`
}


def bad_text(kind: str, size: int) -> str:
    """A text of exactly `size` bytes (ASCII) that is hard to read: blank lines, a `/*` never closed (once, over and
    over, one a line), `class a ` over and over, `{` nested, a string never closed."""
    head, unit = _BAD[kind]
    return (head + unit * (size // len(unit) + 1))[:size]


def _skip_quoted(text: str, i: int) -> int:
    """The index after the string or character literal that opens at `i`; an unescaped newline ends it."""
    quote, n, j = text[i], len(text), i + 1
    while j < n:
        if text[j] == "\\":
            j += 2
        elif text[j] == quote:
            return j + 1
        elif text[j] == "\n":
            return j
        else:
            j += 1
    return n


def open_comment_start(text: str) -> int | None:
    """Where the first `/*` that is never closed begins, or None. One linear pass: line comments, closed block
    comments and string and character literals are stepped over. A hand-written scan, which AGENTS asks the product not
    to write: here it measures what a check before the parser would buy."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and text.startswith("//", i):
            j = text.find("\n", i)
            if j < 0:
                return None
            i = j + 1
        elif c == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                return i
            i = j + 2
        elif c in "\"'":
            i = _skip_quoted(text, i)
        else:
            i += 1
    return None


def safe_prefix(text: str, cap: int) -> str:
    """At most `cap` characters, cut at a line end, and cut back to the line before a `/*` left open."""
    if len(text) > cap:
        cut = text.rfind("\n", 0, cap)
        text = text[:cut + 1] if cut >= 0 else ""
    start = open_comment_start(text)
    if start is not None:
        text = text[:text.rfind("\n", 0, start) + 1]
    return text
