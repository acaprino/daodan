#!/usr/bin/env python3
"""
Cascade scan: stylesheet rules with global reach that can break a screen.

A rule is a candidate when a selector of it reaches the document root, every
element, or the root's untargeted children, descendants or siblings (a type
selector, a universal selector or a structural pseudo-class, never a class, an
id or an attribute), and it sets a property that decides positioning, scrolling,
sizing, display, or the containing block of fixed elements. For each candidate
the scan lists the class, id and attribute rules it can beat on the same
property, and what decides it, in cascade order: `!important`, cascade layer,
specificity, then source order. For a candidate that creates a containing
block, it also lists every `position: fixed` rule, which would stop being fixed
to the viewport under it.

The signature comes from an incident. On 2026-09-14 the rule
`.dark #root > div:first-child { position: relative }` matched a consent modal
mounted as the first child of the React root, beat the modal's own
`.terms-acceptance-modal { @apply fixed ... }` on specificity (1,2,1 against
0,1,0), and left the modal unable to scroll on mobile in dark theme. Both rules
were valid, and nothing that runs at build time compares them.

This is static evidence. Whether a candidate and a conflicting rule match the
same element depends on the rendered tree, which the scan does not have: the
X-ray's Phase 5 confirms it against the component tree, and `usage_finder.py`
finds where a scope class such as `dark` is applied. Two pairs are ruled out
mechanically because no element can match both: a pseudo-element rule is never
overridden by an element selector, and two subjects with different ids or
different type selectors never share an element. A rule on the root or mount
element itself lists no overrides at all, to limit noise rather than because no
element could match both: a class set on `body` or `html` is compared by hand,
and the report says so. Layer order across files depends on how the files load,
and so does source order, so both are reported as undetermined rather than
guessed, except for the layers Tailwind declares.

Tailwind utilities count in two places. Inside a stylesheet, `@apply` inlines
their declarations into the rule. In markup, a string-literal `class` or
`className` attribute applies them from Tailwind's own `utilities` layer; those
are read when a stylesheet uses Tailwind, and only the screen-level ones. A
class list built at runtime is not read.

Conflicts that define a screen come first and carry `screen_level`: a fixed or
sticky position, a scroll container, a viewport height. A global rule breaks a
screen through exactly those, and they are few.

Usage:
    python cascade_scan.py <path> [--json]
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from languages import SUPPORTED_EXTENSIONS  # noqa: E402
from languages.stylesheet import (  # noqa: E402
    dialect_for,
    iter_styled_blocks,
    parse_sheet,
    split_top_level,
    utility_declarations,
)
from snapshot import MAX_PARSE_BYTES, iter_files, read_text  # noqa: E402

__all__ = [
    "LAYOUT_GROUPS",
    "MARKUP_SUFFIXES",
    "STYLESHEET_EXTENSIONS",
    "TAILWIND_LAYERS",
    "compounds",
    "format_markdown",
    "reach",
    "scan",
    "simple_selectors",
    "specificity",
]

STYLESHEET_EXTENSIONS = frozenset(suffix for suffix, lang in SUPPORTED_EXTENSIONS.items() if lang == "css")
# Files whose string-literal class attributes are read for Tailwind utilities.
MARKUP_SUFFIXES = (".tsx", ".jsx", ".vue", ".svelte", ".html", ".htm")
# The layer order `@import "tailwindcss"` declares before anything in the importing file.
TAILWIND_LAYERS = ("theme", "base", "components", "utilities")

# What counts as the document root. The ids are the mount points the common
# client frameworks render into, the places a global rule meets an app's
# top-level screens.
ROOT_TYPES = frozenset({"html", "body"})
ROOT_IDS = frozenset({"root", "app", "__next", "__nuxt", "___gatsby"})

# Properties that decide whether a screen can be laid out, scrolled and
# reached, grouped by the way they break it.
LAYOUT_GROUPS = {
    "position": "positioning",
    "inset": "positioning",
    "top": "positioning",
    "right": "positioning",
    "bottom": "positioning",
    "left": "positioning",
    "overflow": "scroll",
    "overflow-x": "scroll",
    "overflow-y": "scroll",
    "overflow-block": "scroll",
    "overflow-inline": "scroll",
    "overscroll-behavior": "scroll",
    "overscroll-behavior-x": "scroll",
    "overscroll-behavior-y": "scroll",
    "overscroll-behavior-block": "scroll",
    "overscroll-behavior-inline": "scroll",
    "touch-action": "scroll",
    "height": "sizing",
    "max-height": "sizing",
    "min-height": "sizing",
    "block-size": "sizing",
    "max-block-size": "sizing",
    "min-block-size": "sizing",
    "display": "display",
    # Each of these, with a value that is not its initial one, makes the
    # element the containing block of its `position: fixed` descendants, which
    # then stop being fixed to the viewport. `container-type` is absent on
    # purpose: size containment does not create one.
    "transform": "containing-block",
    "translate": "containing-block",
    "rotate": "containing-block",
    "scale": "containing-block",
    "transform-style": "containing-block",
    "filter": "containing-block",
    "backdrop-filter": "containing-block",
    "perspective": "containing-block",
    "will-change": "containing-block",
    "contain": "containing-block",
    "content-visibility": "containing-block",
}

# A longhand and the shorthand that sets it: a rule declaring one overrides a
# rule declaring the other.
SHORTHAND = {
    "overflow-x": "overflow",
    "overflow-y": "overflow",
    "overflow-block": "overflow",
    "overflow-inline": "overflow",
    "overscroll-behavior-x": "overscroll-behavior",
    "overscroll-behavior-y": "overscroll-behavior",
    "overscroll-behavior-block": "overscroll-behavior",
    "overscroll-behavior-inline": "overscroll-behavior",
    "top": "inset",
    "right": "inset",
    "bottom": "inset",
    "left": "inset",
}

STRUCTURAL_PSEUDO_CLASSES = frozenset({
    "first-child", "last-child", "only-child", "nth-child", "nth-last-child",
    "first-of-type", "last-of-type", "only-of-type", "nth-of-type", "nth-last-of-type",
    "empty",
})
LEGACY_PSEUDO_ELEMENTS = frozenset({"before", "after", "first-line", "first-letter"})
_TAKES_MOST_SPECIFIC_ARGUMENT = frozenset({"is", "not", "has", "matches", "-webkit-any", "-moz-any"})
# Pseudo-classes that match whatever their argument list matches.
_WRAPPERS = frozenset({"is", "where", "matches", "-webkit-any", "-moz-any"})
_NO_CONTAINING_BLOCK = frozenset({"none", "initial", "unset", "revert", "revert-layer", "inherit"})
# Tailwind variants that style a pseudo-element, which an element selector never overrides.
_PSEUDO_ELEMENT_VARIANTS = frozenset({
    "before", "after", "placeholder", "file", "marker", "selection", "first-line", "first-letter", "backdrop",
    "details-content",
})
# An arbitrary variant naming a legacy single-colon pseudo-element, `[&:before]`.
_LEGACY_PSEUDO_VARIANT_RE = re.compile(r"\[&[^\]]*?:(?:before|after|first-line|first-letter)\b")
_ESCAPE_RE = re.compile(r"\\[0-9a-fA-F]{1,6}\s?|\\.", re.DOTALL)
_IDENT_RE = re.compile(r"(?:[\w-]|\\[0-9a-fA-F]{1,6}\s?|\\.)+", re.DOTALL)
_OF_RE = re.compile(r"\s+of\s+", re.IGNORECASE)
_VIEWPORT_LENGTH_RE = re.compile(r"\d(?:\.\d+)?(?:vh|dvh|svh|lvh)\b")
# An element tag and its string-literal class attribute: class="...", className="...",
# className={'...'} or className={`...`} without interpolation.
_CLASS_ATTRIBUTE_RE = re.compile(
    r"<([A-Za-z][\w.:-]*)\b[^<>]*?\bclass(?:Name)?\s*=\s*"
    r"(?:\"([^\"]*)\"|'([^']*)'|\{\s*(?:\"([^\"]*)\"|'([^']*)'|`([^`$]*)`)\s*\})",
    re.DOTALL,
)


def _group_at(text: str, start: int, open_ch: str, close_ch: str) -> tuple[str, int]:
    """The inside of a bracketed group starting at `start`, and the index after it."""
    depth = 0
    quote = ""
    j = start
    while j < len(text):
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start + 1:j], j + 1
        j += 1
    return text[start + 1:], len(text)


def compounds(selector: str) -> list[tuple[str, str]]:
    """A complex selector as (combinator before it, compound) pairs. The first combinator is ""."""
    out: list[tuple[str, str]] = []
    current: list[str] = []
    combinator = ""
    pending_space = False
    depth = 0
    quote = ""
    text = selector.strip()
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            current.append(ch)
            if ch == "\\" and i + 1 < len(text):
                current.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if depth == 0:
            if ch.isspace():
                pending_space = bool(current)
                i += 1
                continue
            if ch in ">+~":
                if current:
                    out.append((combinator, "".join(current)))
                    current = []
                combinator = ch
                pending_space = False
                i += 1
                continue
            if pending_space:
                out.append((combinator, "".join(current)))
                current = []
                combinator = " "
                pending_space = False
        if ch == "\\":
            # A hex escape consumes one whitespace after it: `#\31 23` is one id.
            escape = _ESCAPE_RE.match(text, i)
            if escape:
                current.append(escape.group(0))
                i = escape.end()
                continue
        if ch in "\"'":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        current.append(ch)
        i += 1
    if current:
        out.append((combinator, "".join(current)))
    return out


def simple_selectors(compound: str) -> list[tuple[str, str, str | None, str]]:
    """
    The simple selectors of one compound, as (kind, name, argument, text).

    Kinds: id, class, attr, pseudo-class, pseudo-element, type, universal,
    nesting. Sass and LESS interpolation contributes nothing.
    """
    out: list[tuple[str, str, str | None, str]] = []
    n = len(compound)
    i = 0
    while i < n:
        ch = compound[i]
        if ch in "#@" and i + 1 < n and compound[i + 1] == "{":
            _, i = _group_at(compound, i + 1, "{", "}")
            continue
        if ch in "#.%":
            match = _IDENT_RE.match(compound, i + 1)
            if match:
                kind = "id" if ch == "#" else "class"
                out.append((kind, match.group(0), None, compound[i:match.end()]))
                i = match.end()
                continue
            i += 1
            continue
        if ch == "[":
            inner, j = _group_at(compound, i, "[", "]")
            out.append(("attr", inner, None, compound[i:j]))
            i = j
            continue
        if ch == ":":
            element = compound.startswith("::", i)
            match = _IDENT_RE.match(compound, i + (2 if element else 1))
            j = match.end() if match else i + (2 if element else 1)
            name = match.group(0).lower() if match else ""
            argument = None
            if j < n and compound[j] == "(":
                argument, j = _group_at(compound, j, "(", ")")
            kind = "pseudo-element" if element or name in LEGACY_PSEUDO_ELEMENTS else "pseudo-class"
            out.append((kind, name, argument, compound[i:j]))
            i = j
            continue
        if ch == "*":
            out.append(("universal", "*", None, "*"))
            i += 1
            continue
        if ch == "&":
            out.append(("nesting", "&", None, "&"))
            i += 1
            continue
        match = _IDENT_RE.match(compound, i)
        if match:
            if match.end() < n and compound[match.end()] == "|":
                i = match.end() + 1  # a namespace prefix, `svg|rect`
                continue
            out.append(("type", match.group(0).lower(), None, match.group(0)))
            i = match.end()
            continue
        i += 1
    return out


def _add(left: tuple[int, int, int], right: tuple[int, int, int]) -> tuple[int, int, int]:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def _complex_specificity(selector: str) -> tuple[int, int, int]:
    total = (0, 0, 0)
    for _, compound in compounds(selector):
        for kind, name, argument, _ in simple_selectors(compound):
            if kind == "id":
                total = _add(total, (1, 0, 0))
            elif kind in ("class", "attr"):
                total = _add(total, (0, 1, 0))
            elif kind == "type":
                total = _add(total, (0, 0, 1))
            elif kind == "pseudo-element":
                total = _add(total, (0, 0, 1))
                if name == "slotted" and argument:
                    total = _add(total, specificity(argument))
            elif kind == "pseudo-class":
                if name == "where":
                    continue
                if name in _TAKES_MOST_SPECIFIC_ARGUMENT:
                    total = _add(total, specificity(argument or ""))
                elif name in ("nth-child", "nth-last-child") and argument and _OF_RE.search(argument):
                    total = _add(total, (0, 1, 0))
                    total = _add(total, specificity(_OF_RE.split(argument, maxsplit=1)[1]))
                elif name in ("host", "host-context") and argument:
                    total = _add(total, (0, 1, 0))
                    total = _add(total, specificity(argument))
                else:
                    total = _add(total, (0, 1, 0))
    return total


def specificity(selector: str) -> tuple[int, int, int]:
    """(ids, classes and attributes and pseudo-classes, types and pseudo-elements), highest of a list."""
    best = (0, 0, 0)
    for complex_selector in split_top_level(selector):
        best = max(best, _complex_specificity(complex_selector))
    return best


def _subject(selector: str) -> list[tuple[str, str, str | None, str]]:
    parts = compounds(selector)
    return simple_selectors(parts[-1][1]) if parts else []


def _untargeted(simples: list[tuple[str, str, str | None, str]]) -> bool:
    if not simples:
        return False
    for kind, name, argument, _ in simples:
        if kind in ("type", "universal"):
            continue
        if kind == "pseudo-class" and name == "not":
            continue
        if kind == "pseudo-class" and name in STRUCTURAL_PSEUDO_CLASSES and not (argument and _OF_RE.search(argument)):
            continue
        return False
    return True


def _targeted(simples: list[tuple[str, str, str | None, str]]) -> bool:
    for kind, name, argument, _ in simples:
        if kind in ("id", "class", "attr"):
            return True
        if kind == "pseudo-class" and name in _WRAPPERS and argument:
            options = split_top_level(argument)
            if options and all(_targeted(_subject(option)) for option in options):
                return True
    return False


def _anchor(simples: list[tuple[str, str, str | None, str]]) -> str | None:
    for kind, name, argument, text in simples:
        if kind == "type" and name in ROOT_TYPES:
            return name
        if kind == "pseudo-class" and name == "root" and argument is None:
            return ":root"
        if kind == "id" and name in ROOT_IDS:
            return f"#{name}"
        if kind == "pseudo-class" and name in _WRAPPERS and argument:
            options = split_top_level(argument)
            if options and any(
                len(compounds(option)) == 1 and _anchor(simple_selectors(compounds(option)[0][1]))
                for option in options
            ):
                return text
    return None


def reach(selector: str) -> dict | None:
    """How far a complex selector reaches beyond what it names, or None when it targets."""
    parts = [(combinator, simple_selectors(compound)) for combinator, compound in compounds(selector)]
    if not parts or any(kind == "pseudo-element" for kind, *_ in parts[-1][1]):
        return None
    anchor_index = None
    anchor = None
    for index, (_, simples) in enumerate(parts):
        found = _anchor(simples)
        if found:
            anchor_index, anchor = index, found
    if anchor_index is None:
        if len(parts) == 1 and parts[0][1] and all(kind == "universal" for kind, *_ in parts[0][1]):
            return {"reach": "universal", "anchor": "*", "combinator": None, "combinators": [],
                    "relation": "all", "scope": []}
        return None
    tail = parts[anchor_index + 1:]
    combinators = [combinator for combinator, _ in tail]
    if not tail:
        kind, relation = "root", "self"
    else:
        if not all(_untargeted(simples) for _, simples in tail):
            return None
        if combinators[0] in ("+", "~"):
            kind = "sibling"
            relation = "siblings" if all(c in ("+", "~") for c in combinators) else "descendants of siblings"
        elif combinators == [">"]:
            kind, relation = "descendant", "children"
        else:
            kind, relation = "descendant", "descendants"
    scope = [
        text
        for _, simples in parts[:anchor_index + 1]
        for simple_kind, _, _, text in simples
        if simple_kind in ("class", "attr")
    ]
    return {
        "reach": kind,
        "anchor": anchor,
        "combinator": combinators[0] if combinators else None,
        "combinators": combinators,
        "relation": relation,
        "scope": scope,
    }


def _identity(simples) -> tuple[set[str], set[str]]:
    ids = {name for kind, name, _, _ in simples if kind == "id"}
    types = {name for kind, name, _, _ in simples if kind == "type"}
    return ids, types


def _cannot_share_an_element(left, right) -> bool:
    """True when two subjects name different ids or different element types."""
    left_ids, left_types = left
    right_ids, right_types = right
    if left_ids and right_ids and left_ids != right_ids:
        return True
    return bool(left_types and right_types and left_types != right_types)


def _creates_containing_block(prop: str, value: str) -> bool:
    lowered = " ".join(value.lower().split())
    if prop in ("transform", "translate", "rotate", "scale", "filter", "backdrop-filter", "perspective"):
        return lowered not in _NO_CONTAINING_BLOCK
    if prop == "transform-style":
        return lowered == "preserve-3d"
    if prop == "content-visibility":
        return lowered in ("auto", "hidden")
    if prop == "will-change":
        return bool(re.search(
            r"\b(?:transform|translate|rotate|scale|perspective|filter|backdrop-filter|contain|transform-style|offset-path)\b",
            lowered,
        ))
    if prop == "contain":
        return bool(re.search(r"\b(?:layout|paint|strict|content)\b", lowered))
    return False


def _pseudo_variant(condition: str) -> bool:
    """True for a Tailwind variant chain that targets a pseudo-element, `before:` or `[&::x]:`."""
    if not condition:
        return False
    if "::" in condition or _LEGACY_PSEUDO_VARIANT_RE.search(condition):
        return True
    return any(part in _PSEUDO_ELEMENT_VARIANTS for part in condition.split(":"))


def _effective(declarations) -> list:
    """
    The declarations of one rule that win inside it: per property, the last
    `!important` one, else the last; and a longhand is dropped when its own
    shorthand follows it, unless only the longhand is `!important`.
    """
    chosen: dict[tuple[str, str], tuple[int, object]] = {}
    for index, declaration in enumerate(declarations):
        key = (declaration.property, declaration.condition)
        current = chosen.get(key)
        if current is None or declaration.important or not current[1].important:
            chosen[key] = (index, declaration)
    kept = []
    for index, declaration in chosen.values():
        shorthand = SHORTHAND.get(declaration.property)
        later = chosen.get((shorthand, declaration.condition)) if shorthand else None
        if later is not None and later[0] > index and (later[1].important or not declaration.important):
            continue
        kept.append((index, declaration))
    return [declaration for _, declaration in sorted(kept, key=lambda item: item[0])]


def _layout_declarations(declarations, found: dict) -> list[dict]:
    out = []
    for declaration in _effective(declarations):
        group = LAYOUT_GROUPS.get(declaration.property)
        if not group:
            continue
        if _pseudo_variant(declaration.condition):
            continue  # `before:absolute` styles the ::before box, never the element
        if group == "containing-block":
            if not _creates_containing_block(declaration.property, declaration.value):
                continue
            # Filter Effects: a filter on the document root element creates no containing block.
            if (declaration.property in ("filter", "backdrop-filter") and found["reach"] == "root"
                    and found["anchor"] in ("html", ":root")):
                continue
        out.append({
            "property": declaration.property,
            "value": declaration.value,
            "important": declaration.important,
            "line": declaration.line,
            "group": group,
            "origin": declaration.origin,
            "condition": declaration.condition,
        })
    return out


def _normalized(value: str) -> str:
    return " ".join(value.lower().split())


def _components(value: str) -> list[str]:
    """Component values split on top-level whitespace: `calc(50% - 10px)` stays one."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in _normalized(value):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == " " and depth == 0:
            if current:
                parts.append("".join(current))
                current = []
            continue
        current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _value_for(prop: str, value: str, target: str) -> str:
    """The value `prop: value` gives the longhand `target`."""
    parts = _components(value)
    if prop in ("overflow", "overscroll-behavior") and target.endswith(("-x", "-y")) and len(parts) in (1, 2):
        return parts[0] if target.endswith("-x") or len(parts) == 1 else parts[1]
    if prop == "inset" and target in ("top", "right", "bottom", "left") and 1 <= len(parts) <= 4:
        top = parts[0]
        right = parts[1] if len(parts) > 1 else top
        bottom = parts[2] if len(parts) > 2 else top
        left = parts[3] if len(parts) > 3 else right
        return {"top": top, "right": right, "bottom": bottom, "left": left}[target]
    return _normalized(value)


def _differs(candidate_prop: str, candidate_value: str, other_prop: str, other_value: str) -> bool | None:
    """None when the two properties are unrelated; otherwise whether their values differ."""
    if candidate_prop == other_prop:
        return _normalized(candidate_value) != _normalized(other_value)
    if SHORTHAND.get(other_prop) == candidate_prop:
        return _value_for(candidate_prop, candidate_value, other_prop) != _normalized(other_value)
    if SHORTHAND.get(candidate_prop) == other_prop:
        return _normalized(candidate_value) != _value_for(other_prop, other_value, candidate_prop)
    return None


def _screen_level(prop: str, value: str) -> bool:
    """A declaration that defines a screen: a fixed or sticky position, a scroll container, a viewport height."""
    lowered = _normalized(value)
    if prop == "position":
        return lowered in ("fixed", "sticky")
    if prop in ("overflow", "overflow-x", "overflow-y", "overflow-block", "overflow-inline"):
        return any(part in ("auto", "scroll") for part in lowered.split())
    if prop in ("height", "max-height", "min-height", "block-size", "max-block-size", "min-block-size"):
        return bool(_VIEWPORT_LENGTH_RE.search(lowered))
    return False


def _cascade_layer(layer: str | None, sheet) -> str | None:
    """A node's layer as the browser sees it."""
    if layer and sheet.tailwind == "v3" and layer.split(".")[0] in ("base", "components", "utilities"):
        return None  # Tailwind v3 hoists these blocks into its directives: the output is unlayered
    return layer


def _layer_later(left: str, right: str, order: list[str]) -> bool | None:
    """Whether layer `left` comes later in the cascade than `right`, or None when unknown."""
    if right.startswith(left + "."):
        return True  # a layer's own declarations follow its sub-layers
    if left.startswith(right + "."):
        return False
    left_path, right_path = left.split("."), right.split(".")
    shared = 0
    while shared < min(len(left_path), len(right_path)) and left_path[shared] == right_path[shared]:
        shared += 1
    left_name = ".".join(left_path[:shared + 1])
    right_name = ".".join(right_path[:shared + 1])
    if left_name in order and right_name in order:
        return order.index(left_name) > order.index(right_name)
    return None


def _decide(candidate: dict, other: dict, orders: dict) -> str | None:
    """What makes the candidate win, in cascade order, or None when the other rule wins."""
    if candidate["important"] != other["important"]:
        return "important" if candidate["important"] else None
    candidate_layer, other_layer = candidate["layer"], other["layer"]
    anonymous_apart = candidate["file"] != other["file"] and "(anonymous" in f"{candidate_layer}{other_layer}"
    if candidate_layer != other_layer or anonymous_apart:
        if candidate_layer is None or other_layer is None:
            # Unlayered beats every layer for normal declarations; the order reverses for !important.
            candidate_wins = (candidate_layer is None) != candidate["important"]
            return "layer" if candidate_wins else None
        later = None
        if orders["tailwind"] and candidate_layer in TAILWIND_LAYERS and other_layer in TAILWIND_LAYERS:
            later = TAILWIND_LAYERS.index(candidate_layer) > TAILWIND_LAYERS.index(other_layer)
        elif candidate["file"] == other["file"] and not orders["unknown"].get(candidate["file"]):
            later = _layer_later(candidate_layer, other_layer, orders["layers"].get(candidate["file"], []))
        if later is None:
            return "layer-order-unknown"
        return "layer" if later != candidate["important"] else None
    if candidate["specificity"] > other["specificity"]:
        return "specificity"
    if candidate["specificity"] < other["specificity"]:
        return None
    if candidate["file"] == other["file"]:
        return "source-order" if candidate["line"] > other["line"] else None
    return "source-order-unknown"


def _stylesheets(target: Path) -> list[tuple[str, Path]]:
    if target.is_file():
        return [(target.name, target)]
    return [
        (path.relative_to(target).as_posix(), path)
        for path in iter_files(target)
        if path.suffix.lower() in STYLESHEET_EXTENSIONS
    ]


def _markup_utilities(text: str, rel: str, layer: str | None) -> list[dict]:
    """Screen-level Tailwind utilities applied by string-literal class attributes in one markup file."""
    found: list[dict] = []
    newlines = [index for index, ch in enumerate(text) if ch == "\n"]
    for match in _CLASS_ATTRIBUTE_RE.finditer(text):
        group = next(number for number in range(2, 7) if match.group(number) is not None)
        line = bisect.bisect_left(newlines, match.start(group)) + 1
        tag = match.group(1)
        # A lowercase tag is a DOM element and names its type; a component or a
        # member expression (`Dialog`, `motion.div`) names none.
        types = {tag.lower()} if tag[:1].islower() and "." not in tag and ":" not in tag else set()
        for token in match.group(group).split():
            for prop, value, important, condition in utility_declarations(token):
                if _pseudo_variant(condition) or not _screen_level(prop, value):
                    continue
                found.append({
                    "file": rel,
                    "line": line,
                    "selector": f".{token}",
                    "property": prop,
                    "value": value,
                    "important": important,
                    "origin": f"class {token}",
                    "condition": condition,
                    "specificity": (0, 1, 0),
                    "layer": layer,
                    "context": [],
                    "pseudo_element": False,
                    "identity": (set(), types),
                })
    return found


def scan(target: Path) -> dict:
    """Every global-reach candidate under a file or directory, with its conflicts."""
    target = Path(target)
    files = _stylesheets(target)
    candidates: list[dict] = []
    others: list[dict] = []
    orders: dict = {"layers": {}, "unknown": {}, "tailwind": False}
    tailwind_versions: set[str] = set()
    applied_rules = 0
    markup_files = 0
    notes: list[str] = []

    for rel, path in files:
        try:
            if path.stat().st_size > MAX_PARSE_BYTES:
                notes.append(f"skipped {rel}: larger than {MAX_PARSE_BYTES} bytes")
                continue
            sheet = parse_sheet(read_text(path), dialect_for(path.name))
        except OSError as err:
            notes.append(f"skipped {rel}: {err}")
            continue
        orders["layers"][rel] = sheet.layers
        orders["unknown"][rel] = sheet.imports_before_layers
        if sheet.tailwind:
            tailwind_versions.add(sheet.tailwind)
        for node in iter_styled_blocks(sheet):
            if node.kind == "rule":
                applied_rules += 1
            context = node.context + ([node.prelude] if node.kind == "at-rule" else [])
            layer = _cascade_layer(node.layer, sheet)
            effective = _effective(node.declarations)
            for selector in node.selectors:
                spec = specificity(selector)
                found = reach(selector)
                if found:
                    layout = _layout_declarations(node.declarations, found)
                    if layout:
                        candidates.append({
                            "file": rel,
                            "line": node.line,
                            "end_line": node.end_line,
                            "selector": selector,
                            **found,
                            "context": context,
                            "layer": layer,
                            "specificity": list(spec),
                            "identity": _identity(_subject(selector)),
                            "declarations": layout,
                            "conflicts": [],
                        })
                    continue
                subject = _subject(selector)
                if not _targeted(subject):
                    continue
                pseudo = any(kind == "pseudo-element" for kind, *_ in subject)
                for declaration in effective:
                    others.append({
                        "file": rel,
                        "line": declaration.line,
                        "selector": selector,
                        "property": declaration.property,
                        "value": declaration.value,
                        "important": declaration.important,
                        "origin": declaration.origin,
                        "condition": declaration.condition,
                        "specificity": spec,
                        "layer": layer,
                        "context": context,
                        "pseudo_element": pseudo or _pseudo_variant(declaration.condition),
                        "identity": _identity(subject),
                    })

    tailwind = "v4" if "v4" in tailwind_versions else ("v3" if "v3" in tailwind_versions else None)
    orders["tailwind"] = tailwind == "v4"
    if tailwind and not target.is_file():
        for path in iter_files(target):
            if path.suffix.lower() not in MARKUP_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_PARSE_BYTES:
                    continue
                text = read_text(path)
            except OSError:
                continue
            markup_files += 1
            others.extend(_markup_utilities(
                text, path.relative_to(target).as_posix(), "utilities" if tailwind == "v4" else None,
            ))

    for candidate in candidates:
        seen: set[tuple] = set()
        for declaration in candidate["declarations"]:
            for other in others:
                if declaration["group"] == "containing-block":
                    if other["property"] != "position" or _normalized(other["value"]) != "fixed":
                        continue
                    relation, decided_by = "containing-block", None
                else:
                    if candidate["reach"] == "root" or other["pseudo_element"]:
                        continue
                    if _cannot_share_an_element(candidate["identity"], other["identity"]):
                        continue
                    if not _differs(declaration["property"], declaration["value"], other["property"], other["value"]):
                        continue
                    decided_by = _decide(
                        {
                            "important": declaration["important"],
                            "layer": candidate["layer"],
                            "specificity": tuple(candidate["specificity"]),
                            "file": candidate["file"],
                            "line": declaration["line"],
                        },
                        other,
                        orders,
                    )
                    if decided_by is None:
                        continue
                    relation = "overrides"
                key = (other["file"], other["line"], other["selector"], other["property"], relation)
                if key in seen:
                    continue
                seen.add(key)
                candidate["conflicts"].append({
                    "file": other["file"],
                    "line": other["line"],
                    "selector": other["selector"],
                    "property": other["property"],
                    "value": other["value"],
                    "important": other["important"],
                    "origin": other["origin"],
                    "condition": other["condition"],
                    "specificity": list(other["specificity"]),
                    "layer": other["layer"],
                    "context": other["context"],
                    "against": declaration["property"],
                    "relation": relation,
                    "decided_by": decided_by,
                    "screen_level": _screen_level(other["property"], other["value"]),
                })
        candidate["conflicts"].sort(
            key=lambda item: (not item["screen_level"], item["file"], item["line"], item["selector"])
        )
        del candidate["identity"]

    # Rules that reach below the root first: that is where a global rule meets a
    # screen it was never written for.
    candidates.sort(key=lambda item: (item["reach"] == "root", item["file"], item["line"]))
    return {
        "target": target.as_posix(),
        "stylesheets": len(files),
        "markup_files": markup_files,
        "tailwind": tailwind,
        "applied_rules": applied_rules,
        "candidates": candidates,
        "notes": notes,
    }


_GUIDANCE = (
    "Static evidence only. A candidate reaches the document root, every element, or the root's "
    "untargeted children, descendants or siblings, and sets a property that decides positioning, "
    "scrolling, sizing, display or the containing block of fixed elements. A conflict is a class, id "
    "or attribute rule the candidate can beat on the same property, or a `position: fixed` rule it would become the containing block of; when a stylesheet uses Tailwind, "
    "screen-level utilities in string-literal class attributes count too. Whether both match the same "
    "element is not decided here: confirm it against the component tree, and find where a scope class "
    "is applied with usage_finder.py."
)

_DECIDED = {
    "important": "`!important`",
    "layer": "cascade layer order",
    "layer-order-unknown": "cascade layer order, which depends on how the files load",
    "specificity": "specificity",
    "source-order": "source order, since specificity ties and it comes later",
    "source-order-unknown": "source order, which depends on how the files load",
}


def _spec_text(spec) -> str:
    return ",".join(str(part) for part in spec)


def _provenance(item: dict) -> str:
    parts = []
    if item.get("origin"):
        parts.append(f"from `{item['origin']}`")
    if item.get("condition"):
        parts.append(f"under the `{item['condition']}` variant")
    return f", {' '.join(parts)}" if parts else ""


def format_markdown(report: dict) -> str:
    candidates = report["candidates"]
    lines = [
        f"# Cascade scan: `{report['target']}`",
        "",
        f"Stylesheets: {report['stylesheets']} | Markup files read: {report.get('markup_files', 0)} "
        f"| Applied rules: {report['applied_rules']} | Candidates: {len(candidates)}",
        "",
        _GUIDANCE,
        "",
    ]
    if not candidates:
        lines += ["No rule reaches the root or its untargeted children with a layout property.", ""]
    for candidate in candidates:
        if candidate["reach"] == "root":
            reach_text = f"the root or mount element itself, `{candidate['anchor']}`"
        elif candidate["reach"] == "universal":
            reach_text = "every element, `*`"
        else:
            reach_text = f"untargeted {candidate['relation']} of `{candidate['anchor']}`"
        lines += [f"## `{candidate['file']}:{candidate['line']}` `{candidate['selector']}`", ""]
        lines.append(f"- Reach: {reach_text}")
        if candidate["scope"]:
            scope = ", ".join(f"`{item}`" for item in candidate["scope"])
            lines.append(f"- Scope: applies only where {scope} matches; search where it is applied")
        if candidate["context"]:
            lines.append("- Inside: " + "; ".join(f"`{item}`" for item in candidate["context"]))
        if candidate["layer"]:
            lines.append(f"- Layer: `{candidate['layer']}`")
        lines.append(f"- Specificity: {_spec_text(candidate['specificity'])}")
        lines.append("- Declares:")
        for declaration in candidate["declarations"]:
            important = " !important" if declaration["important"] else ""
            lines.append(
                f"  - `{declaration['property']}: {declaration['value']}{important}` "
                f"({declaration['group']}, line {declaration['line']}{_provenance(declaration)})"
            )
        overrides = [item for item in candidate["conflicts"] if item["relation"] == "overrides"]
        blocks = [item for item in candidate["conflicts"] if item["relation"] == "containing-block"]
        screen = [item for item in overrides if item["screen_level"]]
        rest = [item for item in overrides if not item["screen_level"]]
        for heading, group in (
            ("- Can override a screen-level rule (a fixed or sticky position, a scroll container, "
             "a viewport height):", screen),
            ("- Can also override:" if screen else "- Can override:", rest),
        ):
            if not group:
                continue
            lines.append(heading)
            for item in group:
                important = " !important" if item["important"] else ""
                lines.append(
                    f"  - `{item['file']}:{item['line']}` `{item['selector']}` "
                    f"`{item['property']}: {item['value']}{important}` ({_spec_text(item['specificity'])}"
                    f"{_provenance(item)}), decided by {_DECIDED[item['decided_by']]}"
                )
        if blocks:
            lines.append("- Becomes the containing block of any of these fixed elements rendered under it:")
            for item in blocks:
                lines.append(f"  - `{item['file']}:{item['line']}` `{item['selector']}`{_provenance(item)}")
        if candidate["reach"] == "root":
            lines.append(
                "- Overrides on the root or mount element itself are not compared, to limit noise: "
                "check the classes applied to that element by hand."
            )
        elif not candidate["conflicts"]:
            lines.append(
                "- No stylesheet rule, and no screen-level Tailwind utility in markup, that could match "
                "the same element declares a value it can beat."
            )
        lines.append("")
    if report["notes"]:
        lines += ["## Notes", ""] + [f"- {note}" for note in report["notes"]] + [""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List stylesheet rules with global reach that can break a screen, with their conflicts.",
    )
    parser.add_argument("path", type=Path, help="A stylesheet or a directory to scan")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    args = parser.parse_args(argv)
    if not args.path.exists():
        parser.error(f"path not found: {args.path}")
    report = scan(args.path)
    print(json.dumps(report, indent=2) if args.json else format_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
