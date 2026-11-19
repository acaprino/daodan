"""A plain drawing from an SVG file nobody trusts: the one function that decides what Daodan shows as a mark.

Used by the registry builder (marks it ships) and by the product (a mark it downloads from the owner's package)."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

MAX_MARK = 64 * 1024  # bytes: the largest mark of Simple Icons is 54 KB

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
_DRAWN = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon", "g", "defs", "title", "linearGradient",
          "radialGradient", "stop", "clipPath", "mask", "use", "symbol", "style"}
_REMOVED = {"script", "foreignObject", "metadata", "desc", "animate", "set", "animateTransform", "animateMotion"}
_CSS = {"fill", "fill-opacity", "fill-rule", "clip-rule", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
        "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset", "stroke-opacity", "opacity", "stop-color",
        "stop-opacity", "display", "visibility", "clip-path", "mask"}
_ATTRS = _CSS | {"id", "class", "d", "points", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "fx", "fy",
                 "width", "height", "viewBox", "transform", "offset", "gradientUnits", "gradientTransform",
                 "spreadMethod", "clipPathUnits", "maskUnits", "maskContentUnits", "preserveAspectRatio"}


def safe_member(name: object) -> bool:
    """A path inside an archive that stays inside it: relative, no `..`, no drive, no backslash, an `.svg` file."""
    return (isinstance(name, str) and name.endswith(".svg") and not name.startswith("/") and ":" not in name
            and "\\" not in name and ".." not in name.split("/"))


def _safe(value: str) -> bool:
    """A value that fetches nothing and runs nothing: every `url(...)` points to an id of the same file."""
    if re.search(r"javascript:|data:|expression\s*\(|@import|[<\\]", value, re.I):
        return False
    return all(ref.strip(" '\"").startswith("#") for ref in re.findall(r"url\(([^)]*)\)", value, re.I))


def _declarations(text: str) -> str:
    """The declarations of a style that draw (`_CSS`) and are safe, as `prop:value;prop:value`."""
    kept = []
    for declaration in text.split(";"):
        prop, _, value = declaration.partition(":")
        if prop.strip().casefold() in _CSS and _safe(value):
            kept.append(f"{prop.strip().casefold()}:{value.strip()}")
    return ";".join(kept)


def _stylesheet(text: str) -> str:
    """A `<style>` of plain rules (`.a{fill:#fff}`); anything else, an `@import` first, is a ValueError."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", text)
    if "@" in text or re.sub(r"([^{}]+)\{([^{}]*)\}", "", text).strip():
        raise ValueError("a style with more than plain rules")
    out = []
    for selector, body in rules:
        selector = re.sub(r"\s+", " ", selector.strip())
        if not re.fullmatch(r"[\w.#*>, -]+", selector):
            raise ValueError(f"a style selector {selector!r}")
        out.append(f"{selector}{{{_declarations(body)}}}")
    return "".join(out)


def _split(name: str) -> tuple[str, str]:
    """Namespace and local name of an ElementTree name, `{uri}local`."""
    return tuple(name[1:].split("}", 1)) if name.startswith("{") else ("", name)


def _node(node, root: bool = False) -> str:
    space, name = _split(node.tag if isinstance(node.tag, str) else "")
    if space != SVG or name in _REMOVED:
        return ""
    children = "".join(_node(child) for child in node)
    if name == "a":  # a link is not drawing; what it holds is
        return children
    if name not in _DRAWN and not (root and name == "svg"):
        raise ValueError(f"<{name}> is not part of a plain drawing")
    attrs = {}
    for key, value in node.attrib.items():
        space, local = _split(key)
        if local == "href" and space in ("", XLINK):
            if value.startswith("#"):
                attrs["href"] = value
        elif space == "" and local == "style":
            if _declarations(value):
                attrs["style"] = _declarations(value)
        elif space == "" and local in _ATTRS and _safe(value) and (local not in ("id", "class") or re.fullmatch(r"[\w.:\- ]+", value)):
            attrs[local] = value
    if name == "use" and "href" not in attrs:  # a `use` that points outside the file draws nothing safe
        return ""
    if root:
        if "viewBox" not in attrs:
            try:
                width, height = (float(re.sub(r"px$", "", node.get(k, ""))) for k in ("width", "height"))
            except ValueError:
                raise ValueError("no viewBox, and no width and height to make one") from None
            attrs["viewBox"] = f"0 0 {width:g} {height:g}"
        attrs.pop("width", None)
        attrs.pop("height", None)
        attrs = {"xmlns": SVG, "viewBox": attrs.pop("viewBox"), **attrs}
    text = escape(node.text or "") if name == "title" else escape(_stylesheet(node.text or "")) if name == "style" else ""
    head = "<" + name + "".join(f" {k}={quoteattr(v)}" for k, v in attrs.items())
    return f"{head}>{text}{children}</{name}>" if text or children else head + "/>"


def clean_svg(data: bytes, fill: str | None = None) -> str:
    """A plain drawing from an SVG file nobody trusts; ValueError when it is not one.

    Kept: shapes, groups, gradients, clips, masks, `use` of an id of the file, a title and plain style rules, with
    the attributes that draw. Left out: scripts, `foreignObject`, metadata, event attributes, every link or `url(...)`
    that is not an id of the same file, other namespaces. Refused: a file over `MAX_MARK`, a DOCTYPE, a raster, text,
    a filter or any element that is not drawing, a style with an `@`. `fill` is the colour of a mark that has none."""
    if len(data) > MAX_MARK:
        raise ValueError(f"{len(data)} bytes, at most {MAX_MARK}")
    if re.search(rb"<!\s*(DOCTYPE|ENTITY)", data, re.I):
        raise ValueError("a DOCTYPE or an entity")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise ValueError(f"not XML: {error}") from None
    if root.tag != f"{{{SVG}}}svg":
        raise ValueError("not an SVG document")
    out = _node(root, root=True)
    if fill and ' fill="' not in out.split(">", 1)[0]:
        out = re.sub(r'( viewBox="[^"]*")', lambda m: m.group(1) + f" fill={quoteattr(fill)}", out, count=1)
    return out
