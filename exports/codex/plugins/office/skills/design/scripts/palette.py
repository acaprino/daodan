#!/usr/bin/env python3
"""Extract colour seeds from a logo, a website or an Office file, and build
contrast-safe palette candidates from seeds.

Subcommands:
  from-image IMAGE [--count N]       dominant colours of a logo or picture (needs Pillow)
  from-url URL                       colours a website declares in its CSS, theme-color and images
  from-css PATH...                   colours declared in local stylesheets, token files or design notes
  from-file FILE.pptx|FILE.docx      theme scheme and colours used in an Office file
  candidates --seed HEX [--seed HEX] [--count 5] [--name LABEL]
                                     five complete palettes built from one or two seeds
  check PALETTE.json                 contrast and distinctness report for a palette

Every command prints JSON. A palette has the roles background, ink, surface,
accent, muted and data (3 to 4 colours). Ink, accent and muted hold at least
4.5:1 contrast on both background and surface; data colours hold 3:1 on the
background, differ from each other perceptually and stay distinguishable under
simulated red-green colour blindness. All colour mathematics is in OKLCH and
needs only the standard library; Pillow is required only for `from-image`.
Exit 0 on success, 1 when a source could not be read, 2 on invalid use.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree

SCHEMA = "daodan/palette/v1"
TEXT_CONTRAST = 4.5
GRAPHIC_CONTRAST = 3.0
DATA_DISTANCE = 0.12
CVD_DISTANCE = 0.08
MAX_HTML = 2 * 1024 * 1024
MAX_CSS = 1024 * 1024
MAX_IMAGE = 8 * 1024 * 1024
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (compatible; office-palette/1.0)"
NOTICE = ("Contrast and distinctness are computed from the hex values; how an engine, "
          "a projector or a printer reproduces them is separate evidence.")


class PaletteError(Exception):
    pass


# ---------------------------------------------------------------- colour maths

def hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise PaletteError(f"not a #RRGGBB colour: {value!r}")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(min(1.0, max(0.0, c)) * 255):02X}" for c in rgb)


def _to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def rgb_to_oklab(rgb):
    r, g, b = (_to_linear(c) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklab_to_rgb(lab):
    L, a, b = lab
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return tuple(_to_srgb(c) for c in (r, g, bb))


def to_oklch(rgb):
    L, a, b = rgb_to_oklab(rgb)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def from_oklch(L: float, C: float, H: float):
    """sRGB for an OKLCH colour, with chroma reduced until it fits the gamut."""
    rad = math.radians(H)
    for _ in range(40):
        rgb = oklab_to_rgb((L, C * math.cos(rad), C * math.sin(rad)))
        if all(-0.0005 <= c <= 1.0005 for c in rgb):
            return tuple(min(1.0, max(0.0, c)) for c in rgb)
        C *= 0.9
    return tuple(min(1.0, max(0.0, c)) for c in oklab_to_rgb((L, 0.0, 0.0)))


def luminance(rgb) -> float:
    r, g, b = (_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def distance(a, b) -> float:
    return math.dist(rgb_to_oklab(a), rgb_to_oklab(b))


_DEUTAN = ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881))
_PROTAN = ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998))


def simulate(rgb, matrix):
    """Machado (2009) full-severity dichromacy simulation in linear RGB."""
    lin = [_to_linear(c) for c in rgb]
    return tuple(min(1.0, max(0.0, _to_srgb(sum(m * v for m, v in zip(row, lin))))) for row in matrix)


def hue_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ---------------------------------------------------------------- building palettes

def _fit_text(L: float, C: float, H: float, backgrounds, darken: bool):
    """Move L of a text colour until it meets 4.5:1 on every background."""
    for _ in range(100):
        rgb = from_oklch(L, C, H)
        if all(contrast(rgb, bg) >= TEXT_CONTRAST for bg in backgrounds):
            return rgb, L
        L = L - 0.01 if darken else L + 0.01
        if not 0.0 <= L <= 1.0:
            break
    return from_oklch(0.0 if darken else 1.0, 0.0, H), 0.0 if darken else 1.0


def _data_colours(accent_rgb, hue: float, L: float, extra_hue: float | None, background, dark: bool):
    """Accent first, then three hues spread around the wheel at a mid lightness band."""
    hues = [hue]
    if extra_hue is not None and hue_diff(hue, extra_hue) >= 30:
        hues.append(extra_hue)
    for offset in (130, 215, 300, 60, 160, 250):
        if len(hues) == 4:
            break
        candidate = (hue + offset) % 360
        if all(hue_diff(candidate, h) >= 30 for h in hues):
            hues.append(candidate)
    low, high = (0.62, 0.84) if dark else (0.38, 0.60)
    levels = (0.72, 0.66, 0.78) if dark else (0.50, 0.44, 0.56)

    def fits(rgb):
        return contrast(rgb, background) >= GRAPHIC_CONTRAST

    colours = [accent_rgb]
    for i, h in enumerate(hues[1:]):
        level = levels[i % 3]
        rgb = from_oklch(level, 0.14, h)
        while not fits(rgb) and low - 0.1 < level < high + 0.1:
            level += 0.02 if dark else -0.02
            rgb = from_oklch(level, 0.14, h)
        colours.append(rgb)

    def apart(a, b):
        plain = distance(a, b)
        cvd = min(distance(simulate(a, m), simulate(b, m)) for m in (_DEUTAN, _PROTAN))
        return plain >= DATA_DISTANCE and cvd >= CVD_DISTANCE

    # Separate pairs that collapse normally or under red-green colour blindness:
    # rotate the hue first, then step lightness inside the band, keeping 3:1.
    for i in range(1, len(colours)):
        Li, Ci, Hi = to_oklch(colours[i])
        for attempt in range(24):
            if all(apart(colours[i], colours[j]) for j in range(i)) and fits(colours[i]):
                break
            Hi = (Hi + 25) % 360
            if attempt % 3 == 2:
                Li = Li + (0.05 if attempt % 2 else -0.05)
                Li = min(high, max(low, Li))
            colours[i] = from_oklch(Li, Ci, Hi)
            while not fits(colours[i]) and low - 0.1 < Li < high + 0.1:
                Li += 0.02 if dark else -0.02
                colours[i] = from_oklch(Li, Ci, Hi)
    return colours


VARIANTS = (
    ("sober", "Sober: accent chroma reduced, near-white background"),
    ("faithful", "Faithful: the seeds as given, corrected only for contrast"),
    ("bold", "Bold: tinted background, full-chroma accent, darker ink"),
    ("deep", "Deep: ink takes the seed's hue, accent stays saturated"),
    ("dark", "Dark: dark stage in the seed's hue, light text, lightened accent"),
)


def build_palette(variant: str, seeds: list[str], name: str | None = None) -> dict:
    if not seeds:
        raise PaletteError("at least one seed colour is required")
    primary = hex_to_rgb(seeds[0])
    second = hex_to_rgb(seeds[1]) if len(seeds) > 1 else None
    pL, pC, pH = to_oklch(primary)
    sH = to_oklch(second)[2] if second else None
    dark = variant == "dark"
    accent_C = max(0.08, pC)
    if variant == "sober":
        accent_C *= 0.7
    if variant in ("bold", "deep"):
        accent_C = max(accent_C, 0.14)

    if dark:
        background = from_oklch(0.19, 0.03, pH)
        surface = from_oklch(0.25, 0.035, pH)
        ink = from_oklch(0.96, 0.008, pH)
        muted, _ = _fit_text(0.74, 0.02, pH, (background, surface), darken=False)
        accent, aL = _fit_text(max(pL, 0.7), accent_C, pH, (background, surface), darken=False)
    else:
        bg_L, bg_C = {"sober": (0.988, 0.004), "faithful": (0.978, 0.008),
                      "bold": (0.94, 0.02), "deep": (0.97, 0.012)}[variant]
        background = from_oklch(bg_L, bg_C, pH)
        surface = from_oklch(bg_L - 0.035, bg_C + 0.004, pH) if variant != "bold" else from_oklch(0.995, 0.0, pH)
        ink_L, ink_C = {"sober": (0.22, 0.015), "faithful": (0.21, 0.02),
                        "bold": (0.17, 0.025), "deep": (0.24, 0.07)}[variant]
        ink = from_oklch(ink_L, ink_C, pH)
        muted, _ = _fit_text(0.47, 0.025, pH, (background, surface), darken=True)
        accent_hue = sH if (variant == "deep" and sH is not None) else pH
        accent, aL = _fit_text(min(pL, 0.62), accent_C, accent_hue, (background, surface), darken=True)
    data = _data_colours(accent, to_oklch(accent)[2], to_oklch(accent)[0], sH, background, dark)
    palette = {
        "variant": variant,
        "label": dict(VARIANTS)[variant],
        "name": name or f"{variant} {seeds[0].upper()}",
        "dark": dark,
        "seeds": [s.upper() for s in seeds],
        "background": rgb_to_hex(background),
        "ink": rgb_to_hex(ink),
        "surface": rgb_to_hex(surface),
        "accent": rgb_to_hex(accent),
        "muted": rgb_to_hex(muted),
        "data": [rgb_to_hex(c) for c in data],
    }
    palette["check"] = check_palette(palette)
    return palette


def check_palette(palette: dict) -> dict:
    bg, sf = hex_to_rgb(palette["background"]), hex_to_rgb(palette["surface"])
    text = {}
    for role in ("ink", "accent", "muted"):
        rgb = hex_to_rgb(palette[role])
        text[role] = {"on_background": round(contrast(rgb, bg), 2), "on_surface": round(contrast(rgb, sf), 2)}
    data = [hex_to_rgb(c) for c in palette.get("data", [])]
    pairs = []
    for i in range(len(data)):
        for j in range(i):
            pairs.append({"pair": [palette["data"][j], palette["data"][i]],
                          "distance": round(distance(data[i], data[j]), 3),
                          "cvd_distance": round(min(distance(simulate(data[i], m), simulate(data[j], m))
                                                    for m in (_DEUTAN, _PROTAN)), 3)})
    data_contrast = [round(contrast(c, bg), 2) for c in data]
    passes = (all(v >= TEXT_CONTRAST for role in text.values() for v in role.values())
              and all(v >= GRAPHIC_CONTRAST for v in data_contrast)
              and all(p["distance"] >= DATA_DISTANCE and p["cvd_distance"] >= CVD_DISTANCE for p in pairs))
    return {"passes": passes, "text": text, "data_on_background": data_contrast, "data_pairs": pairs,
            "thresholds": {"text": TEXT_CONTRAST, "graphic": GRAPHIC_CONTRAST,
                           "data_distance": DATA_DISTANCE, "cvd_distance": CVD_DISTANCE}}


# ---------------------------------------------------------------- seed sources

def _is_neutral(rgb) -> bool:
    L, C, _ = to_oklch(rgb)
    return C < 0.03 or L > 0.97 or L < 0.12


def rank_seeds(weighted: dict[str, float], count: int) -> list[dict]:
    """Order candidate colours by weight times chroma, dropping neutrals and near-duplicates."""
    scored = []
    for hex_value, weight in weighted.items():
        rgb = hex_to_rgb(hex_value)
        L, C, H = to_oklch(rgb)
        scored.append((weight * (0.2 + C) * (0 if _is_neutral(rgb) else 1), hex_value, rgb, L, C, H))
    scored.sort(key=lambda item: item[0], reverse=True)
    seeds: list[dict] = []
    for score, hex_value, rgb, L, C, H in scored:
        if score <= 0 or any(distance(rgb, hex_to_rgb(s["hex"])) < 0.08 for s in seeds):
            continue
        seeds.append({"hex": hex_value.upper(), "weight": round(weighted[hex_value], 4),
                      "oklch": {"L": round(L, 3), "C": round(C, 3), "H": round(H, 1)}})
        if len(seeds) >= count:
            break
    if not seeds and scored:
        hex_value = scored[0][1]
        seeds.append({"hex": hex_value.upper(), "weight": round(weighted[hex_value], 4),
                      "oklch": dict(zip("LCH", (round(v, 3) for v in to_oklch(hex_to_rgb(hex_value))))),
                      "note": "only neutral colours found"})
    return seeds


def seeds_from_image_bytes(data: bytes, count: int) -> list[dict]:
    try:
        from PIL import Image
    except ImportError as error:
        raise PaletteError("reading images needs Pillow (`pip install Pillow`); it is not installed") from error
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as error:  # Pillow raises many types for a bad file
        raise PaletteError(f"cannot decode image: {error}") from error
    image = image.convert("RGBA")
    image.thumbnail((256, 256))
    raw = image.tobytes()
    pixels = [tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3] > 128]
    if not pixels:
        raise PaletteError("image has no opaque pixels")
    flat = Image.new("RGB", (len(pixels), 1))
    flat.putdata(pixels)
    quantized = flat.quantize(colors=min(16, len(set(pixels))), method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[: 16 * 3]
    counts = quantized.getcolors() or []
    total = sum(n for n, _ in counts) or 1
    weighted = {}
    for n, index in counts:
        r, g, b = palette[index * 3: index * 3 + 3]
        weighted[rgb_to_hex((r / 255, g / 255, b / 255))] = n / total
    return rank_seeds(weighted, count)


def _get(url: str, limit: int) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise PaletteError(f"only http(s) URLs are read: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise PaletteError(f"{url} exceeds {limit} bytes")
    return data


_COLOUR = re.compile(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b|rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")


def colours_in_css(text: str) -> dict[str, float]:
    weighted: dict[str, float] = {}
    for match in _COLOUR.finditer(text):
        if match.group(1) is not None:
            parts = [min(255, int(match.group(i))) / 255 for i in (1, 2, 3)]
            value = rgb_to_hex(tuple(parts))
        else:
            value = rgb_to_hex(hex_to_rgb(match.group(0)))
        weighted[value] = weighted.get(value, 0.0) + 1.0
    return weighted


def seeds_from_url(url: str, count: int) -> dict:
    html = _get(url, MAX_HTML).decode("utf-8", errors="replace")
    weighted = colours_in_css(html)
    declared = []
    for match in re.finditer(r"<meta[^>]+name=[\"']theme-color[\"'][^>]*content=[\"']([^\"']+)", html, re.I):
        try:
            value = rgb_to_hex(hex_to_rgb(match.group(1)))
        except PaletteError:
            continue
        declared.append(value)
        weighted[value] = weighted.get(value, 0.0) + 50.0
    stylesheets, read = [], []
    for match in re.finditer(r"<link[^>]+rel=[\"']stylesheet[\"'][^>]*href=[\"']([^\"']+)", html, re.I):
        stylesheets.append(urllib.parse.urljoin(url, match.group(1)))
    for match in re.finditer(r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]*rel=[\"']stylesheet[\"']", html, re.I):
        stylesheets.append(urllib.parse.urljoin(url, match.group(1)))
    for sheet in dict.fromkeys(stylesheets[:6]):
        try:
            css = _get(sheet, MAX_CSS).decode("utf-8", errors="replace")
        except (OSError, PaletteError):
            continue
        read.append(sheet)
        for value, weight in colours_in_css(css).items():
            weighted[value] = weighted.get(value, 0.0) + weight
    images = []
    for pattern in (r"<meta[^>]+property=[\"']og:image[\"'][^>]*content=[\"']([^\"']+)",
                    r"<link[^>]+rel=[\"'](?:apple-touch-icon|icon)[\"'][^>]*href=[\"']([^\"']+)"):
        match = re.search(pattern, html, re.I)
        if match:
            images.append(urllib.parse.urljoin(url, match.group(1)))
    image_seeds, image_notes = [], []
    for image_url in images[:2]:
        try:
            image_seeds.append({"url": image_url, "seeds": seeds_from_image_bytes(_get(image_url, MAX_IMAGE), 4)})
        except (OSError, PaletteError) as error:
            image_notes.append(f"{image_url}: {error}")
    return {"url": url, "theme_color": declared, "stylesheets_read": read,
            "seeds": rank_seeds(weighted, count), "images": image_seeds, "image_notes": image_notes}


STYLE_SUFFIXES = (".css", ".scss", ".sass", ".less", ".styl", ".json", ".toml", ".yaml", ".yml", ".md", ".js", ".ts")
STYLE_SKIP = {"node_modules", ".git", "dist", "build", "vendor", "__pycache__"}
_TOKEN_NAME = re.compile(r"([A-Za-z0-9_-]*(?:primary|brand|accent|secondary|highlight)[A-Za-z0-9_-]*)\s*[:=]\s*"
                         r"(#[0-9A-Fa-f]{3,6}|rgba?\([^)]*\))", re.I)


def seeds_from_css(paths: list[Path], count: int) -> dict:
    """Colours declared in a project's stylesheets, design tokens or design notes."""
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.suffix.casefold() in STYLE_SUFFIXES and candidate.is_file()                         and not (STYLE_SKIP & set(candidate.relative_to(path).parts[:-1])):
                    files.append(candidate)
        elif path.is_file():
            files.append(path)
        else:
            raise PaletteError(f"{path} does not exist")
    if not files:
        raise PaletteError("no stylesheet, token or design file found under the given paths")
    weighted: dict[str, float] = {}
    named: dict[str, str] = {}
    read = []
    for file in files[:400]:
        try:
            text = file.read_bytes()[:MAX_CSS].decode("utf-8", errors="replace")
        except OSError:
            continue
        read.append(str(file))
        for value, weight in colours_in_css(text).items():
            weighted[value] = weighted.get(value, 0.0) + weight
        for match in _TOKEN_NAME.finditer(text):
            try:
                value = rgb_to_hex(hex_to_rgb(match.group(2))) if match.group(2).startswith("#") else None
            except PaletteError:
                value = None
            if value is None:
                parsed = colours_in_css(match.group(2))
                value = next(iter(parsed), None)
            if value:
                named.setdefault(match.group(1).lstrip("-$@"), value)
                weighted[value] = weighted.get(value, 0.0) + 25.0
    return {"files_read": read, "named_tokens": named, "seeds": rank_seeds(weighted, count)}


_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def seeds_from_file(path: Path, count: int) -> dict:
    suffix = path.suffix.casefold()
    if suffix not in (".pptx", ".pptm", ".docx", ".docm"):
        raise PaletteError(f"unsupported file type {suffix!r}; expected .pptx or .docx")
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as error:
        raise PaletteError(f"cannot read {path}: {error}") from error
    scheme: dict[str, str] = {}
    weighted: dict[str, float] = {}
    with archive:
        names = archive.namelist()
        for name in names:
            if re.fullmatch(r"(ppt|word)/theme/theme\d*\.xml", name) and not scheme:
                root = ElementTree.fromstring(archive.read(name))
                for element in root.iter(f"{{{_A}}}clrScheme"):
                    for child in element:
                        value = child.find(f"{{{_A}}}srgbClr")
                        system = child.find(f"{{{_A}}}sysClr")
                        colour = value.get("val") if value is not None else (
                            system.get("lastClr") if system is not None else None)
                        if colour:
                            scheme[child.tag.split("}")[1]] = "#" + colour.upper()
                    break
            if re.fullmatch(r"ppt/slides/slide\d+\.xml|word/document\.xml", name):
                text = archive.read(name).decode("utf-8", errors="replace")
                for match in re.finditer(r'<a:srgbClr val="([0-9A-Fa-f]{6})"', text):
                    value = "#" + match.group(1).upper()
                    weighted[value] = weighted.get(value, 0.0) + 1.0
                for match in re.finditer(r'w:(?:color|fill)="([0-9A-Fa-f]{6})"', text):
                    value = "#" + match.group(1).upper()
                    weighted[value] = weighted.get(value, 0.0) + 1.0
    for role, value in scheme.items():
        if role.startswith("accent"):
            weighted[value] = weighted.get(value, 0.0) + (12.0 if role == "accent1" else 4.0)
    return {"path": str(path), "theme_scheme": scheme, "seeds": rank_seeds(weighted, count)}


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("from-image", help="dominant colours of an image (needs Pillow)")
    sub.add_argument("image", type=Path)
    sub.add_argument("--count", type=int, default=4)
    sub = commands.add_parser("from-url", help="colours a website declares")
    sub.add_argument("url")
    sub.add_argument("--count", type=int, default=4)
    sub = commands.add_parser("from-css", help="colours in local stylesheets, token files or design notes")
    sub.add_argument("paths", nargs="+", type=Path)
    sub.add_argument("--count", type=int, default=4)
    sub = commands.add_parser("from-file", help="theme scheme and used colours of a PPTX or DOCX")
    sub.add_argument("file", type=Path)
    sub.add_argument("--count", type=int, default=4)
    sub = commands.add_parser("candidates", help="build palette candidates from seeds")
    sub.add_argument("--seed", action="append", required=True, metavar="HEX")
    sub.add_argument("--count", type=int, default=5, help="how many of the five variants, in order")
    sub.add_argument("--name")
    sub = commands.add_parser("check", help="contrast report for a palette JSON file")
    sub.add_argument("palette", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "from-image":
            result = {"path": str(args.image), "seeds": seeds_from_image_bytes(args.image.read_bytes(), args.count)}
        elif args.command == "from-url":
            result = seeds_from_url(args.url, args.count)
        elif args.command == "from-css":
            result = seeds_from_css(args.paths, args.count)
        elif args.command == "from-file":
            result = seeds_from_file(args.file, args.count)
        elif args.command == "candidates":
            if len(args.seed) > 2:
                raise PaletteError("use at most two seeds: the primary colour and an optional second one")
            variants = [v for v, _ in VARIANTS][: max(1, min(5, args.count))]
            result = {"seeds": [s.upper() for s in args.seed],
                      "candidates": [build_palette(v, args.seed, args.name) for v in variants]}
        else:
            palette = json.loads(args.palette.read_text(encoding="utf-8"))
            result = {"path": str(args.palette), "check": check_palette(palette)}
    except (OSError, PaletteError, ValueError, ElementTree.ParseError) as error:
        print(json.dumps({"schema": SCHEMA, "command": args.command, "ok": False, "error": str(error)}, indent=2))
        return 1
    print(json.dumps({"schema": SCHEMA, "command": args.command, "ok": True, **result, "notice": NOTICE},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
