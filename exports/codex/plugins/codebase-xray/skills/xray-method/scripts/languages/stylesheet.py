"""
Stylesheet adapter: CSS, SCSS and LESS.

A stylesheet has no classes and no functions, but it has the unit a claim about
a screen cites: the rule. Every applied rule becomes a symbol with an exact
span, named by the selector it applies as once nesting is flattened and
qualified by the at-rules around it, so `@media (max-width: 600px) { .a .b }`
is one symbol. An edit inside it marks stale the claims about it and about the
symbols enclosing it, as a class encloses its methods, never those about its
siblings. A name repeated in one file keeps one symbol per occurrence (`.a`, `.a (2)`).
Top-level at-rules and Sass or LESS variables are symbols too; mixins and Sass
functions are the stylesheet's functions.

This exists because of an incident, not for completeness. On 2026-09-14 the
global rule `.dark #root > div:first-child { position: relative }` overrode a
consent modal's `position: fixed` and locked users out of an app on mobile,
and the X-ray run that had the modal in its inventory had not recorded the
stylesheet at all, and 4.1.0 recorded stylesheets only as hashes. `cascade_scan.py` reads the tree built here to find that
signature mechanically. The modal's `fixed` was written `@apply fixed`, like
most of that stylesheet, so Tailwind's layout utilities are expanded into the
declarations they inline.

A tokenizer rather than regular expressions, and no tree-sitter: selectors and
declarations are a brace-and-semicolon grammar a small state machine reads
exactly, while strings, comments, `url(...)` bodies and `#{...}` interpolation
are the places a regular expression breaks. The dialect changes what `//`
means and how nesting resolves. In SCSS and LESS `//` starts a line comment
anywhere outside `url(...)` and a custom property's value. In plain CSS it never
does: a browser reads it as an invalid token and drops the declaration, rule or
media block it sits in, and so does this parser. Nesting in plain CSS gives `&`
the meaning of `:is(<parent list>)`, where Sass substitutes each parent in
turn. SCSS alone has nested properties, LESS alone detached rulesets and
guards. Indented Sass (`.sass`) has no braces and is not handled here; it stays
a file-level entry in the manifest.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterator

from .base import ClassInfo, FunctionInfo, ImportInfo, ParameterInfo, ParseResult
from .comments import CommentToken

__all__ = [
    "Declaration",
    "Node",
    "Sheet",
    "adapter",
    "dialect_for",
    "iter_styled_blocks",
    "normalize_selector",
    "parse_sheet",
    "split_top_level",
    "utility_declarations",
]

_LANGUAGE_NAME = "css"

# At-rules whose body is a definition, not styles applied where they stand.
_DEFINITION_AT_RULES = frozenset({"mixin", "function"})
_AT_NAME_RE = re.compile(r"^@([\w-]+)")
_DEFINITION_RE = re.compile(r"^@[\w-]+\s+([\w-]+)\s*(?:\((.*)\))?", re.DOTALL)
_LESS_MIXIN_HEAD_RE = re.compile(r"^([.#][\w-]+)\s*\(")
_LESS_GUARD_RE = re.compile(r"\s+when\s+.*$", re.DOTALL)
_LESS_DETACHED_RE = re.compile(r"^(@[\w-]+)\s*:$")
_LESS_VARIABLE_RE = re.compile(r"^(@[\w-]+)\s*:")
_SCSS_VARIABLE_RE = re.compile(r"^(\$[\w-]+)\s*:")
_NESTED_PROPERTY_RE = re.compile(r"^([A-Za-z-][\w-]*)\s*:(?:\s+(.*))?$", re.DOTALL)
# A pending statement that is a custom property: its value is raw tokens, so a
# `{}` block in it is text and, in SCSS, a `//` in it is not a comment.
_CUSTOM_PROPERTY_HEAD_RE = re.compile(r"^\s*--[\w-]+\s*:")
_PROPERTY_RE = re.compile(r"^(?:--[\w-]+|\*?-?[A-Za-z_][\w-]*)$")
_IMPORTANT_RE = re.compile(r"!\s*important\s*$", re.IGNORECASE)
_IMPORT_OPTIONS_RE = re.compile(r"^\s*\([^)]*\)")
_IMPORT_TARGET_RE = re.compile(
    r"""url\(\s*(['"]?)(?P<url>[^'")\s]*)\1\s*\)|(['"])(?P<str>.*?)\3"""
)
_IMPORT_LAYER_RE = re.compile(r"\blayer(?:\(\s*([^)]*?)\s*\))?(?![\w-])", re.IGNORECASE)
_SCHEME_RE = re.compile(r"^[A-Za-z][\w+.-]*:")
_AT_ROOT_QUERY_RE = re.compile(r"^\(\s*(with|without)\s*:\s*([^)]*)\)$")
_ESCAPE = r"\\(?:[0-9a-fA-F]{1,6}\s?|.)"
# An ident may start with `--`, a letter (any script), an underscore or an escape.
_CLASS_OR_ID_RE = re.compile(
    r"(?<!\\)[.#]((?:--|-?(?:[^\W\d]|" + _ESCAPE + r"))(?:[\w-]|" + _ESCAPE + r")*)"
)
_ESCAPE_RE = re.compile(r"\\([0-9a-fA-F]{1,6})\s?|\\(.)", re.DOTALL)
_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"|' + r"'(?:\\.|[^'\\])*'", re.DOTALL)
_BRACKET_RE = re.compile(r"(?<!\\)\[(?:\\.|[^\]\\])*\]", re.DOTALL)
_URL_RE = re.compile(r"url\([^)]*\)", re.IGNORECASE)


def dialect_for(file_path: str) -> str:
    """"css", "scss" or "less", from a file name."""
    lowered = str(file_path).lower()
    if lowered.endswith(".scss"):
        return "scss"
    if lowered.endswith(".less"):
        return "less"
    return "css"


@dataclass
class Declaration:
    property: str  # lowercased, except a custom property, which is case-sensitive
    value: str  # whitespace collapsed, `!important` removed
    important: bool
    line: int
    # "@apply fixed" when a Tailwind utility produced the declaration.
    origin: str = ""
    # The Tailwind variant chain the utility sits under, such as "dark" or "md:hover".
    condition: str = ""


@dataclass
class Node:
    # "rule", "at-rule", "definition" (@mixin, @function, LESS mixin), "detached"
    # (a LESS detached ruleset), "keyframe" (a selector inside @keyframes) or
    # "property-block" (SCSS nested properties, `font: { family: x; }`).
    kind: str
    prelude: str
    line: int
    end_line: int = 0
    # At-rule name without "@", a definition's name, or a property block's prefix.
    name: str = ""
    # Flattened selectors this block's declarations apply to. A rule has its
    # own; an at-rule nested inside a rule inherits the rule's.
    selectors: list[str] = field(default_factory=list)
    # Preludes of the enclosing at-rules, outermost first. Excludes the node's own.
    context: list[str] = field(default_factory=list)
    # False inside a definition, a detached ruleset or @keyframes, and for a rule
    # or block a browser drops: nothing there styles an element where it stands.
    applied: bool = True
    # The cascade layer, dotted for nested layers, or None when unlayered.
    layer: str | None = None
    declarations: list[Declaration] = field(default_factory=list)
    children: list["Node"] = field(default_factory=list)
    parameters: str = ""


@dataclass
class Sheet:
    nodes: list[Node] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    # Custom properties anywhere, and top-level Sass or LESS variables.
    constants: list[str] = field(default_factory=list)
    # Top-level Sass or LESS variables and detached rulesets: (name, start, end).
    variables: list[tuple[str, int, int]] = field(default_factory=list)
    comments: list[CommentToken] = field(default_factory=list)
    code_lines: set[int] = field(default_factory=set)
    # Cascade layer names in order of first appearance, from statements, blocks
    # and `@import ... layer()`. Declaring `a.b` declares `a` first, as the cascade does.
    layers: list[str] = field(default_factory=list)
    # "v4" when the sheet imports tailwindcss (which declares theme, base,
    # components, utilities before anything else), "v3" for @tailwind directives.
    tailwind: str | None = None
    # True when an unlayered @import or @use other than Tailwind precedes the
    # first layer: the imported sheet may declare layers, so their order is not known here.
    imports_before_layers: bool = False
    _constant_names: set[str] = field(default_factory=set, repr=False)
    _anonymous_layers: int = field(default=0, repr=False)


def split_top_level(text: str, separator: str = ",") -> list[str]:
    """Split on a separator outside parentheses, brackets, braces, strings and escapes."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            current.append(text[i:i + 2])
            i += 2
            continue
        if quote:
            current.append(ch)
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            current.append(ch)
        elif ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            current.append(ch)
        elif ch == separator and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current).strip())
    return [part for part in parts if part]


def normalize_selector(selector: str) -> str:
    """Collapse whitespace and put exactly one space around each combinator."""
    text = " ".join(selector.split())
    out: list[str] = []
    depth = 0
    quote = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            out.append(text[i:i + 2])
            i += 2
            continue
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch in "([{":
            depth += 1
            out.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            out.append(ch)
        elif depth == 0 and ch in ">+~":
            while out and out[-1] == " ":
                out.pop()
            out.append(f" {ch} ")
            i += 1
            while i < len(text) and text[i] == " ":
                i += 1
            continue
        else:
            out.append(ch)
        i += 1
    return "".join(out).strip()


def _has_parent_reference(selector: str) -> bool:
    return "&" in _STRING_RE.sub("", selector)


def _nest(child: str, parent: str, prefix: bool = True) -> str:
    """
    A nested selector resolved against one parent. An `&` inside a string is
    text, and `#{&}` interpolates the parent's text. Without an `&` the parent
    becomes the child's ancestor, except under @at-root (`prefix=False`), which
    removes that implicit ancestor and still resolves `&`, as Sass documents.
    """
    child = child.replace("#{&}", parent)
    out: list[str] = []
    found = False
    quote = ""
    i = 0
    while i < len(child):
        ch = child[i]
        if ch == "\\" and i + 1 < len(child):
            out.append(child[i:i + 2])
            i += 2
            continue
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "&":
            out.append(parent)
            found = True
        else:
            out.append(ch)
        i += 1
    if found or not prefix:
        return "".join(out)
    return f"{parent} {child}"


def _flatten(prelude: str, parents: list[str] | None, dialect: str, prefix: bool = True) -> list[str]:
    children = [normalize_selector(child) for child in split_top_level(prelude)]
    if not parents:
        return children
    if dialect == "css" and len(parents) > 1:
        return [_nest(child, f":is({', '.join(parents)})", prefix) for child in children]
    return [_nest(child, parent, prefix) for parent in parents for child in children]


def _at_root_query(prelude: str):
    """(whether parent selectors survive, which enclosing at-rules survive) for an @at-root."""
    match = _AT_ROOT_QUERY_RE.match(prelude[len("@at-root"):].strip())
    if not match:
        return False, lambda name: True
    mode = match.group(1).lower()
    names = {name.lower() for name in match.group(2).split()}
    if mode == "without":
        if "all" in names:
            return False, lambda name: False
        return "rule" not in names, lambda name: name not in names
    if "all" in names:
        return True, lambda name: True
    return "rule" in names, lambda name: name in names


def _context(stack: list[Node]) -> list[str]:
    kept: list[Node] = []
    for node in stack:
        if node.kind != "at-rule":
            continue
        if node.name == "at-root":
            _, keeps = _at_root_query(node.prelude)
            kept = [at_rule for at_rule in kept if keeps(at_rule.name)]
        else:
            kept.append(node)
    return [node.prelude for node in kept]


def _layer_of(stack: list[Node]) -> str | None:
    """The layer a new node sits in: the innermost @layer, unless an @at-root query dropped it."""
    layer = None
    for node in stack:
        if node.kind != "at-rule":
            continue
        if node.name == "at-root":
            _, keeps = _at_root_query(node.prelude)
            if not keeps("layer"):
                layer = None
        elif node.name == "layer":
            layer = node.layer
    return layer


def _parent_selectors(stack: list[Node]) -> list[str] | None:
    for node in reversed(stack):
        if node.kind == "at-rule" and node.name == "at-root":
            keeps_rule, _ = _at_root_query(node.prelude)
            if not keeps_rule:
                return None
            continue
        if node.kind == "rule":
            return node.selectors
    return None


def _nearest_rule_selectors(stack: list[Node]) -> list[str] | None:
    """What `&` refers to: the nearest rule's selectors, whatever @at-root sits between."""
    for node in reversed(stack):
        if node.kind == "rule":
            return node.selectors
    return None


def _owner(stack: list[Node]) -> Node | None:
    """The block a nested property block's declarations belong to."""
    for node in reversed(stack):
        if node.kind == "property-block":
            continue
        return node if node.kind in ("rule", "at-rule") else None
    return None


def _without_strings_and_brackets(selector: str) -> str:
    return _BRACKET_RE.sub("", _STRING_RE.sub("", selector))


def _less_mixin(prelude: str) -> tuple[str, str] | None:
    """(name, parameters) for a LESS mixin definition, reading to the parenthesis that balances."""
    head = _LESS_MIXIN_HEAD_RE.match(prelude)
    if not head:
        return None
    depth = 0
    quote = ""
    for index in range(head.end() - 1, len(prelude)):
        ch = prelude[index]
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                rest = prelude[index + 1:].strip()
                if rest and not rest.startswith("when") and rest != "!important":
                    return None
                return head.group(1), prelude[head.end():index]
    return None


def _register_layer(sheet: Sheet, full: str) -> None:
    """Record a layer and, before it, every ancestor its dotted name declares."""
    parts = full.split(".")
    for end in range(1, len(parts) + 1):
        name = ".".join(parts[:end])
        if name not in sheet.layers:
            sheet.layers.append(name)


def _anonymous_layer(sheet: Sheet) -> str:
    # Every anonymous layer is a distinct layer.
    sheet._anonymous_layers += 1
    return f"(anonymous layer {sheet._anonymous_layers})"


def _make_node(prelude: str, line: int, stack: list[Node], dialect: str, sheet: Sheet) -> Node:
    parent = stack[-1] if stack else None
    applied = parent.applied if parent else True
    layer = _layer_of(stack)
    context = _context(stack)
    at = _AT_NAME_RE.match(prelude)
    if at:
        name = at.group(1).lower()
        if name in _DEFINITION_AT_RULES:
            match = _DEFINITION_RE.match(prelude)
            return Node(
                "definition", prelude, line,
                name=match.group(1) if match else name,
                parameters=(match.group(2) or "") if match else "",
                context=context, applied=False, layer=layer,
            )
        if dialect == "less":
            detached = _LESS_DETACHED_RE.match(prelude)
            if detached:
                if parent is None:
                    _add_constant(sheet, detached.group(1))
                return Node("detached", prelude, line, name=detached.group(1), context=context,
                            applied=False, layer=layer)
        if name == "at-root":
            rest = prelude[at.end():].strip()
            if rest and not rest.startswith("("):
                parents = _nearest_rule_selectors(stack) if _has_parent_reference(rest) else None
                return Node("rule", prelude, line, name=name,
                            selectors=_flatten(rest, parents, dialect, prefix=False),
                            context=context, applied=applied, layer=layer)
        if name == "layer":
            segment = prelude[at.end():].strip() or _anonymous_layer(sheet)
            layer = f"{layer}.{segment}" if layer else segment
            _register_layer(sheet, layer)
        if dialect == "css" and "//" in _STRING_RE.sub("", prelude):
            applied = False  # an invalid prelude: the browser drops the whole block
        return Node("at-rule", prelude, line, name=name, selectors=list(_parent_selectors(stack) or []),
                    context=context, applied=applied and not name.endswith("keyframes"), layer=layer)
    if any(node.kind == "at-rule" and node.name.endswith("keyframes") for node in stack):
        return Node("keyframe", prelude, line, context=context, applied=False, layer=layer)
    nested = _NESTED_PROPERTY_RE.match(prelude) if dialect == "scss" else None
    owner = _owner(stack)
    if prelude.endswith(":") or (nested and owner is not None):
        base = prelude[:-1].strip() if prelude.endswith(":") else nested.group(1)
        prefix = f"{parent.name}-{base}" if parent is not None and parent.kind == "property-block" else base
        value = "" if prelude.endswith(":") else (nested.group(2) or "").strip()
        if owner is not None and value:
            important = bool(_IMPORTANT_RE.search(value))
            owner.declarations.append(Declaration(
                prefix.lower(), _IMPORTANT_RE.sub("", value).strip(), important, line,
            ))
        return Node("property-block", prelude, line, name=prefix.lower(), context=context,
                    applied=False, layer=layer)
    less_mixin = _less_mixin(prelude)
    if less_mixin:
        return Node("definition", prelude, line, name=less_mixin[0], parameters=less_mixin[1],
                    context=context, applied=False, layer=layer)
    selector_text = _LESS_GUARD_RE.sub("", prelude) if dialect == "less" else prelude
    if dialect == "css" and "//" in _without_strings_and_brackets(selector_text):
        applied = False  # an invalid selector: the browser drops the whole rule
    parents = _parent_selectors(stack)
    prefix = True
    if parents is None and _has_parent_reference(selector_text):
        # Under @at-root, `&` still names the parent; only the implicit ancestor goes.
        parents = _nearest_rule_selectors(stack)
        prefix = False
    return Node("rule", selector_text, line, selectors=_flatten(selector_text, parents, dialect, prefix),
                context=context, applied=applied, layer=layer)


# ---------------------------------------------------------------------------
# Tailwind `@apply`: the layout utilities, expanded into what they inline.
# ---------------------------------------------------------------------------

_TW_POSITION = frozenset({"static", "fixed", "absolute", "relative", "sticky"})
_TW_DISPLAY = {
    "block": "block", "inline-block": "inline-block", "inline": "inline", "flex": "flex",
    "inline-flex": "inline-flex", "grid": "grid", "inline-grid": "inline-grid", "contents": "contents",
    "hidden": "none", "table": "table", "flow-root": "flow-root", "list-item": "list-item",
}
_TW_KEYWORDS = {
    "full": "100%", "screen": "100vh", "dvh": "100dvh", "svh": "100svh", "lvh": "100lvh",
    "auto": "auto", "px": "1px", "0": "0", "min": "min-content", "max": "max-content",
    "fit": "fit-content", "none": "none",
}
_TW_OVERFLOW = frozenset({"auto", "hidden", "clip", "visible", "scroll"})
_TW_OVERSCROLL = frozenset({"auto", "contain", "none"})
_TW_FILTER_RE = re.compile(
    r"(?:blur|brightness|contrast|drop-shadow|grayscale|hue-rotate|invert|saturate|sepia)(?:-.+)?"
)
_TW_BACKDROP_RE = re.compile(
    r"backdrop-(?:blur|brightness|contrast|grayscale|hue-rotate|invert|opacity|saturate|sepia)(?:-.+)?"
)
_TW_TRANSFORM_RE = re.compile(r"(?:translate|rotate|scale|skew)(?:-[xyz])?-.+")
# Utilities whose names begin like a layout utility's but set something else.
_TW_NOT_LAYOUT = ("perspective-origin-", "inset-shadow-", "inset-ring-")


def _tw_value(suffix: str, negative: bool = False) -> str:
    if suffix.startswith("[") and suffix.endswith("]"):
        value = suffix[1:-1].replace("_", " ")
    elif suffix.startswith("(") and suffix.endswith(")"):
        value = f"var({suffix[1:-1]})"  # Tailwind v4 shorthand: `h-(--x)` is `height: var(--x)`
    else:
        value = _TW_KEYWORDS.get(suffix, suffix)
    return f"-{value}" if negative and value not in ("auto", "none", "0") else value


def _utility_declarations(utility: str) -> list[tuple[str, str]]:
    """The layout declarations a Tailwind utility inlines, or [] for any other utility."""
    negative = utility.startswith("-")
    bare = utility[1:] if negative else utility
    if bare.startswith(_TW_NOT_LAYOUT):
        return []
    if bare in _TW_POSITION:
        return [("position", bare)]
    if bare in _TW_DISPLAY:
        return [("display", _TW_DISPLAY[bare])]
    match = re.fullmatch(r"inset-([xy])-(.+)", bare)
    if match:
        sides = ("left", "right") if match.group(1) == "x" else ("top", "bottom")
        return [(side, _tw_value(match.group(2), negative)) for side in sides]
    match = re.fullmatch(r"inset-(.+)", bare)
    if match:
        return [("inset", _tw_value(match.group(1), negative))]
    match = re.fullmatch(r"(top|right|bottom|left)-(.+)", bare)
    if match:
        return [(match.group(1), _tw_value(match.group(2), negative))]
    match = re.fullmatch(r"overflow-([xy])-(\w+)", bare)
    if match and match.group(2) in _TW_OVERFLOW:
        return [(f"overflow-{match.group(1)}", match.group(2))]
    match = re.fullmatch(r"overflow-(\w+)", bare)
    if match and match.group(1) in _TW_OVERFLOW:
        return [("overflow", match.group(1))]
    match = re.fullmatch(r"overscroll-([xy])-(\w+)", bare)
    if match and match.group(2) in _TW_OVERSCROLL:
        return [(f"overscroll-behavior-{match.group(1)}", match.group(2))]
    match = re.fullmatch(r"overscroll-(\w+)", bare)
    if match and match.group(1) in _TW_OVERSCROLL:
        return [("overscroll-behavior", match.group(1))]
    match = re.fullmatch(r"touch-(.+)", bare)
    if match:
        return [("touch-action", _tw_value(match.group(1)))]
    match = re.fullmatch(r"(min-h|max-h|h)-(.+)", bare)
    if match:
        prop = {"min-h": "min-height", "max-h": "max-height", "h": "height"}[match.group(1)]
        return [(prop, _tw_value(match.group(2)))]
    match = re.fullmatch(r"(translate|rotate|scale)-none", bare)
    if match:
        return [(match.group(1), "none")]
    if bare in ("transform", "transform-gpu", "transform-cpu"):
        return [("transform", "var(--tw-transform)")]
    if bare == "transform-none":
        return [("transform", "none")]
    if _TW_TRANSFORM_RE.fullmatch(bare):
        return [("transform", utility)]
    if bare == "filter":
        return [("filter", "var(--tw-filter)")]
    if bare == "filter-none":
        return [("filter", "none")]
    if _TW_FILTER_RE.fullmatch(bare):
        return [("filter", utility)]
    if bare == "backdrop-filter":
        return [("backdrop-filter", "var(--tw-backdrop-filter)")]
    if bare in ("backdrop-filter-none", "backdrop-none"):
        return [("backdrop-filter", "none")]
    if _TW_BACKDROP_RE.fullmatch(bare):
        return [("backdrop-filter", utility)]
    for prefix, prop in (("will-change-", "will-change"), ("contain-", "contain"), ("perspective-", "perspective")):
        if bare.startswith(prefix) and len(bare) > len(prefix):
            return [(prop, _tw_value(bare[len(prefix):]))]
    return []


def _split_variant(token: str) -> tuple[str, str]:
    depth = 0
    last = -1
    for index, ch in enumerate(token):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif ch == ":" and depth == 0:
            last = index
    return (token[:last], token[last + 1:]) if last >= 0 else ("", token)


def utility_declarations(token: str) -> list[tuple[str, str, bool, str]]:
    """
    The layout declarations one Tailwind class inlines, as (property, value,
    important, variant chain). `!` counts in either position, and every other
    utility yields nothing.
    """
    important = False
    if token.startswith("!"):
        token, important = token[1:], True
    condition, utility = _split_variant(token)
    if utility.startswith("!"):
        utility, important = utility[1:], True
    if utility.endswith("!"):
        utility, important = utility[:-1], True
    return [(prop, value, important, condition) for prop, value in _utility_declarations(utility)]


def _apply(target: Node, rest: str, line: int) -> None:
    rest = rest.strip()
    all_important = bool(_IMPORTANT_RE.search(rest))
    if all_important:
        rest = _IMPORTANT_RE.sub("", rest)
    for token in rest.split():
        for prop, value, important, condition in utility_declarations(token):
            target.declarations.append(Declaration(
                prop, value, important or all_important, line, origin=f"@apply {token}", condition=condition,
            ))


def _import_info(spec: str) -> ImportInfo:
    spec = spec.strip()
    if not spec or _SCHEME_RE.match(spec) or spec.startswith(("//", "~", "@")):
        return ImportInfo(module=spec, is_internal=False)
    # A stylesheet import is a URL relative to the importing file, and a Sass
    # load resolves against the importing file first, so a bare "variables"
    # means "./variables". Written that way, snapshot.py resolves it relatively.
    if not spec.startswith((".", "/")):
        spec = "./" + spec
    return ImportInfo(module=spec, is_internal=True)


def _import_specs(rest: str, name: str) -> list[str]:
    rest = _IMPORT_OPTIONS_RE.sub("", rest)  # LESS: @import (reference) "x";
    specs = []
    for match in _IMPORT_TARGET_RE.finditer(rest):
        specs.append(match.group("str") if match.group("str") is not None else match.group("url"))
    # @use and @forward load one module; only @import takes a list.
    return specs if name == "import" else specs[:1]


def _add_constant(sheet: Sheet, name: str) -> None:
    if name not in sheet._constant_names:
        sheet._constant_names.add(name)
        sheet.constants.append(name)


def _add_variable(sheet: Sheet, name: str, start: int, end: int) -> None:
    _add_constant(sheet, name)
    sheet.variables.append((name, start, end))


def _statement(sheet: Sheet, text: str, start: int, end: int, stack: list[Node], dialect: str) -> None:
    parent = stack[-1] if stack else None
    at = _AT_NAME_RE.match(text)
    if at:
        variable = _LESS_VARIABLE_RE.match(text)
        if variable:
            if parent is None:
                _add_variable(sheet, variable.group(1), start, end)
            return
        name = at.group(1).lower()
        if name in ("import", "use", "forward"):
            rest = text[at.end():]
            layered = None
            if name == "import":
                without_targets = _IMPORT_TARGET_RE.sub(" ", rest)
                layered = _IMPORT_LAYER_RE.search(without_targets)
            for spec in _import_specs(rest, name):
                if spec == "tailwindcss" or spec.startswith("tailwindcss/"):
                    sheet.tailwind = "v4"
                    sheet.imports.append(ImportInfo(module=spec, is_internal=False))
                    continue
                if layered is None and not sheet.layers:
                    sheet.imports_before_layers = True
                sheet.imports.append(_import_info(spec))
            if layered is not None:
                _register_layer(sheet, (layered.group(1) or "").strip() or _anonymous_layer(sheet))
        elif name == "tailwind":
            sheet.tailwind = sheet.tailwind or "v3"
        elif name == "apply" and parent is not None:
            target = parent if parent.kind != "property-block" else (_owner(stack) or parent)
            _apply(target, text[at.end():], start)
        elif name == "layer":
            for segment in split_top_level(text[at.end():]):
                full = f"{parent.layer}.{segment}" if parent is not None and parent.layer else segment
                _register_layer(sheet, full)
        return
    variable = _SCSS_VARIABLE_RE.match(text)
    if variable:
        if parent is None:
            _add_variable(sheet, variable.group(1), start, end)
        return
    if parent is None or ":" not in text:
        return
    prop, value = text.split(":", 1)
    prop = prop.strip()
    if not _PROPERTY_RE.match(prop):
        return
    value = value.strip()
    if dialect == "css" and not prop.startswith("--") and "//" in _URL_RE.sub("", _STRING_RE.sub("", value)):
        return  # an invalid value: the browser drops the declaration
    important = bool(_IMPORTANT_RE.search(value))
    if important:
        value = _IMPORTANT_RE.sub("", value).strip()
    if prop.startswith("--"):
        _add_constant(sheet, prop)
    else:
        prop = prop.lower()
    target = parent
    if parent.kind == "property-block":
        prop = f"{parent.name}-{prop}"
        target = _owner(stack) or parent
    target.declarations.append(Declaration(prop, value, important, start))


def _balanced_end(content: str, start: int) -> int:
    """The index just after the brace block that opens at `start`; strings and comments hold no braces."""
    depth = 0
    quote = ""
    j = start
    n = len(content)
    while j < n:
        ch = content[j]
        if ch == "\\":
            j += 2
            continue
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif content.startswith("/*", j):
            stop = content.find("*/", j + 2)
            j = n if stop < 0 else stop + 2
            continue
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return n


def parse_sheet(content: str, dialect: str = "scss") -> Sheet:
    """Tokenize a stylesheet into its block tree, imports, constants, layers and comments."""
    if content.startswith("\ufeff"):
        content = content[1:]
    sheet = Sheet()
    stack: list[Node] = []
    buf: list[str] = []
    buf_line = 0
    # Open parentheses and brackets, innermost last: "url", "paren" or "bracket".
    frames: list[str] = []
    line = 1
    line_start = 0
    line_has_code = False
    line_comments = dialect != "css"
    i = 0
    n = len(content)

    def take(segment: str, index: int) -> None:
        nonlocal buf_line, line, line_start, line_has_code
        if segment.strip():
            if not buf_line:
                buf_line = line
            newlines = segment.count("\n")
            sheet.code_lines.update(range(line, line + newlines + 1))
            if newlines:
                line += newlines
                line_start = index + segment.rfind("\n") + 1
            line_has_code = True
        buf.append(segment)

    def pending() -> tuple[str, int]:
        nonlocal buf_line
        text = " ".join("".join(buf).split())
        start = buf_line or line
        buf.clear()
        buf_line = 0
        return text, start

    def end_statement() -> None:
        text, start = pending()
        if text:
            _statement(sheet, text, start, line, stack, dialect)

    def close(node: Node, end: int) -> None:
        node.end_line = end
        if node.kind == "detached" and not stack:
            sheet.variables.append((node.name, node.line, end))

    def close_frame(kinds: tuple[str, ...]) -> None:
        # Pop through to the nearest frame of a matching kind; a stray closer
        # with no such frame open changes nothing.
        for depth in range(len(frames) - 1, -1, -1):
            if frames[depth] in kinds:
                del frames[depth:]
                return

    while i < n:
        ch = content[i]
        if ch == "\n":
            line += 1
            i += 1
            line_start = i
            line_has_code = False
            if buf:
                buf.append(" ")
            continue
        if ch == "\\" and i + 1 < n:
            take(content[i:i + 2], i)
            i += 2
            continue
        in_url = bool(frames) and frames[-1] == "url"
        if not in_url and content.startswith("/*", i):
            stop = content.find("*/", i + 2)
            stop = n if stop < 0 else stop + 2
            raw = content[i:stop]
            sheet.comments.append(_comment(raw, line, i - line_start, line_has_code, block=True))
            if "\n" in raw:
                line += raw.count("\n")
                line_start = i + raw.rfind("\n") + 1
                line_has_code = False
            i = stop
            if buf:
                buf.append(" ")
            continue
        if (line_comments and not in_url and content.startswith("//", i)
                and not _CUSTOM_PROPERTY_HEAD_RE.match("".join(buf))):
            stop = content.find("\n", i)
            stop = n if stop < 0 else stop
            sheet.comments.append(_comment(content[i:stop], line, i - line_start, line_has_code, block=False))
            i = stop
            continue
        if (content.startswith(("<!--", "-->"), i) and not stack and not frames
                and not "".join(buf).strip()):
            i += 4 if content.startswith("<!--", i) else 3
            continue
        if ch in "\"'":
            j = i + 1
            while j < n and content[j] != ch and content[j] != "\n":
                j += 2 if content[j] == "\\" else 1
            if j < n and content[j] == ch:
                j += 1
            j = min(j, n)
            take(content[i:j], i)
            i = j
            continue
        if ch in "#@" and content.startswith("{", i + 1):
            j = i + 2
            level = 1
            while j < n and level:
                if content[j] == "{":
                    level += 1
                elif content[j] == "}":
                    level -= 1
                j += 1
            take(content[i:j], i)
            i = j
            continue
        if ch == "(":
            frames.append("url" if content[max(0, i - 3):i].lower() == "url" else "paren")
        elif ch == "[":
            frames.append("bracket")
        elif ch == ")":
            close_frame(("paren", "url"))
        elif ch == "]":
            close_frame(("bracket",))
        elif not frames and ch == "{":
            if _CUSTOM_PROPERTY_HEAD_RE.match("".join(buf)):
                j = _balanced_end(content, i)
                take(content[i:j], i)
                i = j
                continue
            sheet.code_lines.add(line)
            line_has_code = True
            prelude, start = pending()
            node = _make_node(prelude, start, stack, dialect, sheet)
            (stack[-1].children if stack else sheet.nodes).append(node)
            stack.append(node)
            i += 1
            continue
        elif not frames and ch == ";":
            sheet.code_lines.add(line)
            line_has_code = True
            end_statement()
            i += 1
            continue
        elif not frames and ch == "}":
            sheet.code_lines.add(line)
            line_has_code = True
            end_statement()
            if stack:
                close(stack.pop(), line)
            i += 1
            continue
        take(ch, i)
        i += 1

    end_statement()
    last = max(sheet.code_lines) if sheet.code_lines else line
    while stack:
        node = stack.pop()
        close(node, max(node.line, last))
    return sheet


def _comment(raw: str, line: int, column: int, inline: bool, block: bool) -> CommentToken:
    if not block:
        return CommentToken(line_number=line, column=column, text=raw[2:].strip(), raw_text=raw,
                            is_inline=inline, is_block=False)
    doc = raw.startswith("/**") and not raw.startswith("/**/")
    body = raw[3 if doc else 2:]
    if body.endswith("*/"):
        body = body[:-2]
    return CommentToken(line_number=line, column=column, text=body.strip(), raw_text=raw,
                        is_inline=inline, is_block=True, is_doc_block=doc)


def iter_styled_blocks(sheet: Sheet) -> Iterator[Node]:
    """Every block whose declarations style elements, in document order."""
    pending_nodes = list(reversed(sheet.nodes))
    while pending_nodes:
        node = pending_nodes.pop()
        if node.applied and node.selectors and node.kind in ("rule", "at-rule"):
            yield node
        pending_nodes.extend(reversed(node.children))


def _parameters(raw: str) -> list[ParameterInfo]:
    params = []
    for part in split_top_level(raw.replace(";", ",")):
        name, _, default = part.partition(":")
        if name.strip():
            params.append(ParameterInfo(name=name.strip(), default=default.strip() or None))
    return params


def _decode_escapes(name: str) -> str:
    def replace(match: re.Match) -> str:
        if match.group(1):
            code = int(match.group(1), 16)
            # CSS Syntax: zero, a surrogate or a value past the last code point is U+FFFD.
            return chr(code) if 0 < code <= 0x10FFFF and not 0xD800 <= code <= 0xDFFF else "\ufffd"
        return match.group(2)

    return _ESCAPE_RE.sub(replace, name)


class _StylesheetAdapter:
    language = _LANGUAGE_NAME

    def parse(self, content: str, file_path: str) -> ParseResult:
        dialect = dialect_for(file_path)
        sheet = parse_sheet(content, dialect)
        result = ParseResult(
            file_path=file_path,
            language=self.language,
            notes=[f"parser=stylesheet ({dialect})"],
        )
        entries: list[tuple[int, int, ClassInfo]] = []
        exported: dict[str, None] = {}

        def add(info: ClassInfo) -> None:
            entries.append((info.line_number, len(entries), info))

        for name, start, end in sorted(sheet.variables, key=lambda item: item[1]):
            add(ClassInfo(name=name, kind="variable", line_number=start, end_line=end))

        # Iterative, so a generated stylesheet nested a thousand levels deep does
        # not exhaust the interpreter's recursion limit.
        pending_nodes = [(node, True) for node in reversed(sheet.nodes)]
        while pending_nodes:
            node, top = pending_nodes.pop()
            if node.kind == "definition":
                result.functions.append(FunctionInfo(
                    name=node.name,
                    parameters=_parameters(node.parameters),
                    line_number=node.line,
                    end_line=node.end_line,
                ))
                continue
            if node.kind in ("keyframe", "property-block", "detached"):
                continue
            if node.kind == "at-rule" and top:
                add(ClassInfo(name=node.prelude, kind="at-rule", line_number=node.line, end_line=node.end_line))
            if node.kind == "rule" and node.applied:
                name = ", ".join(node.selectors)
                for prelude in reversed(node.context):
                    name = f"{prelude} {{ {name} }}"
                add(ClassInfo(name=name, kind="rule", line_number=node.line, end_line=node.end_line))
                for selector in node.selectors:
                    text = _without_strings_and_brackets(selector)
                    for match in _CLASS_OR_ID_RE.finditer(text):
                        if text.startswith(("#{", "@{"), match.end()):
                            continue  # an interpolated name: the prefix alone names nothing
                        exported.setdefault(_decode_escapes(match.group(1)))
            pending_nodes.extend((child, False) for child in reversed(node.children))

        ordered = [info for _, _, info in sorted(entries, key=lambda entry: entry[:2])]
        # A repeated name keeps its own span: snapshot.symbol_spans widens a
        # repeated name over everything between its occurrences. The suffix skips
        # any number whose name the file already uses, `@include columns (2)` included.
        raw_names = {info.name for info in ordered}
        seen: Counter[str] = Counter()
        assigned: set[str] = set()
        for info in ordered:
            raw = info.name
            seen[raw] += 1
            if seen[raw] > 1:
                number = seen[raw]
                while f"{raw} ({number})" in raw_names or f"{raw} ({number})" in assigned:
                    number += 1
                info.name = f"{raw} ({number})"
            assigned.add(info.name)
        result.classes = ordered
        result.imports = sheet.imports
        result.constants = sheet.constants
        result.exported_symbols = list(exported)
        return result

    # The three methods below serve callers that count lines and comments. With
    # no path they read plain CSS, where `//` is never a comment; a caller that
    # knows the file passes it, so SCSS and LESS comments are read as comments.

    def count_imports(self, content: str, file_path: str | None = None) -> int:
        return len(parse_sheet(content, dialect_for(file_path) if file_path else "css").imports)

    def strip_comments_and_blanks(self, content: str, file_path: str | None = None) -> int:
        return len(parse_sheet(content, dialect_for(file_path) if file_path else "css").code_lines)

    def extract_comments(self, content: str, file_path: str | None = None) -> list[CommentToken]:
        return parse_sheet(content, dialect_for(file_path) if file_path else "css").comments


adapter = _StylesheetAdapter()
