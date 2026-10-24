"""Render a static HTML preview of a presentation plan before construction.

Reads the Office slide design library for direction palettes and the pattern
catalogue, then writes a self-contained HTML page: one 16:9 frame per slide with
the planned pattern wireframe, the real headline, palette tokens, and per-slide
density notes. The preview is a review artifact; it never becomes a PowerPoint
deliverable and never replaces native construction or rendered review.

Standard library only. No network, no Node, no external service.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCES = HERE.parent / "references"
LAYOUT_PATTERNS = REFERENCES / "layout-patterns.md"
VISUAL_DIRECTIONS = HERE.parent.parent / "design" / "references" / "directions.md"

MIN_BODY_PT = 13
MAX_SLIDES = 60
MAX_HEADLINE_CHARS = 90
MAX_TITLE_CHARS = 70
MAX_KICKER_CHARS = 60
MAX_BODY_CHARS = 220

# Slot geometry on a normalized 1000 x 562.5 canvas (16:9, editor margins kept).
PATTERN_GEOMETRY: dict[str, tuple[dict, dict]] = {
    "cover": (
        {"kind": "cover"},
        {
            "title": (60, 180, 430, 80),
            "subtitle": (60, 272, 430, 40),
            "meta": (60, 320, 430, 36),
            "accent band": (500, 54, 440, 454),
        },
    ),
    "agenda": (
        {"kind": "list", "count": 6},
        {
            "section 1": (60, 150, 880, 52),
            "section 2": (60, 210, 880, 52),
            "section 3": (60, 270, 880, 52),
            "section 4": (60, 330, 880, 52),
            "section 5": (60, 390, 880, 52),
            "section 6": (60, 450, 880, 52),
        },
    ),
    "section divider": (
        {"kind": "divider"},
        {
            "section number": (60, 120, 200, 90),
            "section title": (60, 240, 880, 120),
            "progress marker": (60, 480, 880, 16),
        },
    ),
    "executive summary": (
        {"kind": "cards", "count": 3},
        {
            "card 1": (60, 150, 286, 300),
            "card 2": (357, 150, 286, 300),
            "card 3": (654, 150, 286, 300),
            "takeaway": (60, 470, 880, 56),
        },
    ),
    "key metric spotlight": (
        {"kind": "cards", "count": 4},
        {
            "metric 1": (60, 150, 205, 200),
            "metric 2": (285, 150, 205, 200),
            "metric 3": (510, 150, 205, 200),
            "metric 4": (735, 150, 205, 200),
            "takeaway": (60, 370, 880, 150),
        },
    ),
    "chart and insight": (
        {"kind": "split", "count": 2, "lead": "chart"},
        {
            "chart title": (60, 150, 545, 340),
            "axis labels": (60, 500, 545, 36),
            "insight": (630, 150, 310, 240),
            "decision impact": (630, 410, 310, 80),
        },
    ),
    "comparison matrix": (
        {"kind": "table", "count": 4},
        {
            "criteria": (60, 150, 240, 340),
            "option 1": (310, 150, 205, 340),
            "option 2": (525, 150, 205, 340),
            "option 3": (740, 150, 200, 340),
            "recommendation": (60, 500, 880, 40),
        },
    ),
    "options and recommendation": (
        {"kind": "cards", "count": 4},
        {
            "option 1": (60, 150, 205, 300),
            "option 2": (285, 150, 205, 300),
            "option 3": (510, 150, 205, 300),
            "option 4": (735, 150, 205, 300),
            "recommendation": (60, 470, 880, 56),
        },
    ),
    "data table": (
        {"kind": "table", "count": 6},
        {
            "header row": (60, 150, 880, 48),
            "row 1": (60, 204, 880, 44),
            "row 2": (60, 254, 880, 44),
            "row 3": (60, 304, 880, 44),
            "row 4": (60, 354, 880, 44),
            "row 5": (60, 404, 880, 44),
            "totals": (60, 454, 880, 36),
            "note": (60, 500, 880, 36),
        },
    ),
    "timeline and roadmap": (
        {"kind": "columns", "count": 6},
        {
            "period 1": (60, 150, 140, 40),
            "period 2": (205, 150, 140, 40),
            "period 3": (350, 150, 140, 40),
            "period 4": (495, 150, 140, 40),
            "period 5": (640, 150, 140, 40),
            "period 6": (785, 150, 140, 40),
            "items": (60, 210, 880, 200),
            "note": (60, 420, 880, 110),
        },
    ),
    "process flow": (
        {"kind": "steps", "count": 5},
        {
            "stage 1": (60, 200, 160, 120),
            "stage 2": (245, 200, 160, 120),
            "stage 3": (430, 200, 160, 120),
            "stage 4": (615, 200, 160, 120),
            "stage 5": (800, 200, 140, 120),
            "deliverables": (60, 360, 880, 100),
            "handoffs": (60, 480, 880, 60),
        },
    ),
    "architecture and system map": (
        {"kind": "bands", "count": 4},
        {
            "layer 1": (60, 150, 880, 80),
            "layer 2": (60, 245, 880, 80),
            "layer 3": (60, 340, 880, 80),
            "layer 4": (60, 435, 880, 50),
            "legend": (60, 495, 640, 40),
            "constraints": (720, 495, 220, 40),
        },
    ),
    "risk and mitigation table": (
        {"kind": "table", "count": 5},
        {
            "header": (60, 150, 880, 48),
            "risk 1": (60, 204, 880, 50),
            "risk 2": (60, 260, 880, 50),
            "risk 3": (60, 316, 880, 50),
            "risk 4": (60, 372, 880, 50),
            "risk 5": (60, 428, 880, 50),
            "note": (60, 490, 880, 48),
        },
    ),
    "case study": (
        {"kind": "columns", "count": 3},
        {
            "context": (60, 150, 286, 300),
            "action": (357, 150, 286, 300),
            "result": (654, 150, 286, 300),
            "proof": (60, 470, 880, 56),
        },
    ),
    "quote and testimonial": (
        {"kind": "quote"},
        {
            "quote": (100, 150, 800, 200),
            "attribution": (100, 365, 800, 50),
            "supporting fact": (100, 435, 800, 60),
        },
    ),
    "team and organization": (
        {"kind": "cards", "count": 6},
        {
            "person 1": (60, 150, 286, 180),
            "person 2": (357, 150, 286, 180),
            "person 3": (654, 150, 286, 180),
            "person 4": (60, 340, 286, 180),
            "person 5": (357, 340, 286, 180),
            "person 6": (654, 340, 286, 180),
        },
    ),
    "workshop and training plan": (
        {"kind": "steps", "count": 5},
        {
            "step 1": (60, 160, 160, 140),
            "step 2": (245, 160, 160, 140),
            "step 3": (430, 160, 160, 140),
            "step 4": (615, 160, 160, 140),
            "step 5": (800, 160, 140, 140),
            "timing": (60, 330, 880, 60),
            "materials": (60, 410, 880, 120),
        },
    ),
    "next steps and decision request": (
        {"kind": "cards", "count": 3},
        {
            "decision": (60, 140, 880, 80),
            "action 1": (60, 240, 286, 160),
            "action 2": (357, 240, 286, 160),
            "action 3": (654, 240, 286, 160),
            "owner/date": (60, 420, 880, 100),
        },
    ),
}

SCOPE_NOTE = "preview only: wireframe of the plan, not a rendered or final deck"


def parse_directions(path: Path) -> dict[str, dict]:
    directions: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| **"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        name = re.sub(r"\s+", " ", cells[0].strip("* ")).strip()
        label = name.split(" ")[0]
        palette = re.findall(r"#[0-9A-Fa-f]{6}", cells[2])
        if len(palette) < 4:
            palette = [""] * 4
        directions[label] = {
            "name": name,
            "background": palette[0],
            "ink": palette[1],
            "surface": palette[2],
            "accent": palette[3],
            "typography": cells[3],
            "rhythm": cells[4],
            "best_for": cells[1],
        }
    return directions


def parse_patterns(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    patterns: dict[str, dict] = {}
    for match in re.finditer(r"^\| (\d+) \| ([^|]+) \| ([^|]+) \|$", text, re.M):
        number = int(match.group(1))
        pattern_separator = "\u2014"
        entry = re.search(
            rf"^{number}\.\s+\*\*(.+?)\*\*\s*{pattern_separator}\s*(.*?)(?=^\d+\.\s+\*\*|\Z)",
            text, re.M | re.S,
        )
        details = ""
        if entry:
            details = " ".join(entry.group(2).split())
        slots = re.findall(r"`([^`]+)`", details)
        # The pattern's own range ("3 to 6 periods", "2, 3 or 4 cards", "4 to 7 rows
        # maximum") is the capacity; the wireframe draws one variant of it.
        ranges = re.findall(r"\b(\d+)(?:,\s*\d+)*\s+(?:to|or)\s+(\d+)\s+(?!%)[a-z]", details)
        capacity = max((int(high) for _, high in ranges), default=None)
        patterns[match.group(2).strip().lower()] = {
            "number": number,
            "name": match.group(2).strip(),
            "job": match.group(3).strip(),
            "details": details,
            "slots": slots,
            "capacity": capacity,
        }
    return patterns


def load_library() -> tuple[dict[str, dict], dict[str, dict]]:
    return parse_patterns(LAYOUT_PATTERNS), parse_directions(VISUAL_DIRECTIONS)


def resolve_pattern(plan: dict, patterns: dict[str, dict]) -> dict:
    geometry = PATTERN_GEOMETRY[plan]
    entry = patterns.get(plan)
    number = entry["number"] if entry else None
    name = entry["name"] if entry else plan
    drawn = _repeatable_capacity(geometry[1])
    capacity = entry["capacity"] if entry and entry["capacity"] else drawn
    return {
        "key": plan,
        "number": number,
        "name": name,
        "job": entry["job"] if entry else "",
        "capacity": max(capacity, drawn),
        "drawn": drawn,
        "slots": entry["slots"] if entry else [],
        "kind": geometry[0]["kind"],
        "boxes": geometry[1],
    }


def resolve_direction(direction: dict, directions: dict[str, dict]) -> tuple[dict, list[str]]:
    problems: list[str] = []
    label = direction.get("library")
    resolved: dict = {}
    if label:
        label = str(label).upper()
        if label not in directions:
            problems.append(f"unknown library direction: {label}")
        else:
            resolved = dict(directions[label])
    palette = direction.get("palette") or {}
    for key in ("background", "ink", "surface", "accent"):
        value = palette.get(key)
        if value is None:
            continue
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(value)):
            problems.append(f"palette.{key} is not a #RRGGBB value: {value}")
        else:
            resolved[key] = str(value).upper()
    for key in ("background", "ink", "surface", "accent"):
        if not resolved.get(key):
            problems.append(f"missing {key}: give a library direction or all four palette colours")
    if direction.get("name"):
        resolved["name"] = direction["name"]
    return resolved, problems


def pattern_capacity(pattern: dict) -> int | None:
    return pattern["capacity"]


def _repeatable_capacity(boxes: dict) -> int:
    """Count the dedicated repeated slot boxes drawn in the wireframe."""
    matched = [
        label for label in boxes
        if re.search(r"\b(?:\d+|row|card|metric|stage|step|risk|period|person|option|layer)\b", label)
    ]
    numbers = [int(match.group(1)) for label in matched if (match := re.search(r"(\d+)$", label))]
    return max(numbers) if numbers else len(matched)


def count_plan_items(plan: dict) -> int | None:
    content = plan.get("content") or {}
    for key in ("sections", "stages", "rows", "periods", "options", "criteria", "steps",
                "metrics", "cards", "people", "risks", "layers", "items"):
        value = content.get(key)
        if isinstance(value, list):
            return len(value)
    return None


def check_slide(index: int, plan: dict, pattern: dict) -> list[str]:
    notes: list[str] = []
    headline = str(plan.get("headline") or "")
    title = str(plan.get("title") or "")
    kicker = str(plan.get("kicker") or "")
    content = plan.get("content")
    density = plan.get("density")
    mode = str(plan.get("mode") or "").lower()
    if pattern["kind"] not in ("cover", "divider") and not headline and mode != "showcase":
        notes.append("no action headline or label: state the slide's takeaway in one line, "
                     "or declare the deck's showcase mode")
    if len(headline) > MAX_HEADLINE_CHARS:
        notes.append(f"headline is {len(headline)} characters: likely three lines at headline scale")
    if len(title) > MAX_TITLE_CHARS:
        notes.append(f"title is {len(title)} characters: shorten or split the slide")
    if len(kicker) > MAX_KICKER_CHARS:
        notes.append("kicker exceeds the short section label")
    if isinstance(content, str) and len(content) > MAX_BODY_CHARS:
        notes.append(f"body text is {len(content)} characters: split across slides instead of shrinking")
    if density is not None:
        try:
            if int(density) < MIN_BODY_PT:
                notes.append(f"declared density {density} pt is below the {MIN_BODY_PT} pt floor")
        except (TypeError, ValueError):
            notes.append(f"declared density is not a number: {density}")
    planned = count_plan_items(plan)
    capacity = pattern_capacity(pattern)
    if planned is not None and capacity is not None and planned > capacity:
        notes.append(f"{planned} items exceed the pattern's {capacity} for this layout: split the slide")
    return notes


def build_document(plan: dict, library: dict) -> tuple[str, list[str]]:
    patterns, directions = library
    problems: list[str] = []
    slides = plan.get("slides")
    if not isinstance(slides, list) or not slides:
        problems.append("plan has no slides")
        slides = []
    if len(slides) > MAX_SLIDES:
        problems.append(f"{len(slides)} slides exceed the {MAX_SLIDES}-slide preview bound")
    direction, direction_problems = resolve_direction(plan.get("direction") or {}, directions)
    problems.extend(direction_problems)
    resolved: list[dict] = []
    for index, slide in enumerate(slides, start=1):
        key = str(slide.get("pattern") or "").strip().lower()
        if key not in PATTERN_GEOMETRY:
            problems.append(f"slide {index}: unknown pattern '{slide.get('pattern')}'")
            continue
        pattern = resolve_pattern(key, patterns)
        resolved.append({"index": index, "plan": slide, "pattern": pattern})
        problems.extend(f"slide {index}: {note}" for note in check_slide(index, slide, pattern))
    if problems:
        return "", problems

    palette = direction
    background = palette["background"]
    ink = palette["ink"]
    surface = palette["surface"]
    accent = palette["accent"]
    deck_title = plan.get("deck_title") or plan.get("title") or "Presentation preview"
    deck_meta = plan.get("deck_meta") or ""
    body = "\n".join(render_slide(item, palette) for item in resolved)
    summary_rows = "\n".join(
        f"<tr><td>{item['index']}</td><td>{escape(item['pattern']['name'])}</td>"
        f"<td>{escape(str(item['plan'].get('headline') or item['plan'].get('title') or ''))}</td>"
        f"<td>{escape(item['pattern']['job'])}</td></tr>"
        for item in resolved
    )
    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(str(deck_title))}: design preview</title>
<style>
:root {{ --bg: {background}; --surface: {surface}; --ink: {ink}; --accent: {accent}; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 32px; background: #eef0f3; color: #14181d;
  font-family: "Segoe UI", Calibri, Arial, sans-serif; }}
header {{ max-width: 1180px; margin: 0 auto 24px; }}
h1 {{ font-size: 22px; margin: 0 0 6px; }}
p.meta {{ margin: 0 0 4px; color: #4b5563; font-size: 13px; }}
p.note {{ margin: 4px 0 0; color: #92400e; font-size: 13px; font-weight: 600; }}
section.slide {{ max-width: 1180px; margin: 0 auto 34px; }}
.caption {{ display: flex; gap: 10px; align-items: baseline; font-size: 13px; margin: 0 0 8px; }}
.caption strong {{ font-size: 14px; }}
.caption span {{ color: #4b5563; }}
.canvas {{ position: relative; width: 100%; aspect-ratio: 16 / 9; background: var(--bg);
  color: var(--ink); border: 1px solid #d1d5db; border-radius: 4px; overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12); }}
.box {{ position: absolute; border-radius: 3px; padding: 6px 8px; overflow: hidden;
  background: var(--surface); border: 1px solid rgba(0, 0, 0, 0.14); font-weight: 600; }}
.box em {{ display: block; font-style: normal; font-weight: 400; font-size: 9px;
  text-transform: uppercase; letter-spacing: 0.4px; opacity: 0.65; }}
.kind-slide-title {{ position: absolute; left: 6%; top: 5%; width: 88%; hyphens: none;
  font-size: 16px; font-weight: 700; color: var(--accent); }}
.kind-kicker {{ position: absolute; left: 6%; top: 9%; font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.6px; color: var(--accent); }}
.kind-headline {{ position: absolute; left: 6%; top: 14%; width: 88%; font-size: 17px;
  font-weight: 700; overflow: hidden; }}
.kind-source {{ position: absolute; left: 6%; bottom: 4%; width: 88%; font-size: 10px;
  opacity: 0.7; font-weight: 400; }}
.kind-accent {{ background: var(--accent); color: var(--bg); border-color: transparent;
  opacity: 0.9; }}
.kind-metric, .kind-card {{ display: flex; flex-direction: column; justify-content: center;
  gap: 4px; text-align: left; }}
.kind-metric strong, .kind-card strong {{ font-size: 13px; }}
.kind-metric span, .kind-card span {{ font-size: 10px; font-weight: 400; opacity: 0.75; }}
.kind-quote blockquote {{ margin: 0; font-size: 13px; line-height: 1.4; font-weight: 400; }}
ol.steps {{ list-style: none; }}
.step-number {{ position: absolute; right: 8px; bottom: 4px; font-size: 34px; font-weight: 700;
  line-height: 1; opacity: 0.22; }}
table.summary {{ max-width: 1180px; margin: 0 auto; border-collapse: collapse; font-size: 13px;
  background: #fff; }}
table.summary th, table.summary td {{ border: 1px solid #d1d5db; padding: 6px 10px; text-align: left; }}
footer {{ max-width: 1180px; margin: 0 auto; color: #4b5563; font-size: 12px; }}
</style>
</head>
<body>
<header>
<h1>{escape(str(deck_title))}</h1>
<p class="meta">{escape(str(deck_meta))}</p>
<p class="meta">direction: {escape(str(palette.get('name', 'custom')))} | canvas 16:9 | slides: {len(resolved)}</p>
<p class="note">{escape(SCOPE_NOTE)}</p>
</header>
{body}
<h1 style="max-width:1180px;margin:34px auto 12px;font-size:18px">Slide sequence</h1>
<table class="summary">
<thead><tr><th>#</th><th>Pattern</th><th>Headline or title</th><th>Job</th></tr></thead>
<tbody>
{summary_rows}
</tbody>
</table>
<footer>{escape(SCOPE_NOTE)}</footer>
</body>
</html>
"""
    return document, []


def box_style(box: tuple[int, int, int, int]) -> str:
    width, height = 1000, 562.5
    x, y, w, h = box
    return (
        f"left:{x / width * 100:.2f}%;top:{y / height * 100:.2f}%;"
        f"width:{w / width * 100:.2f}%;height:{h / height * 100:.2f}%"
    )


def render_slide(item: dict, palette: dict) -> str:
    plan = item["plan"]
    pattern = item["pattern"]
    kind = pattern["kind"]
    boxes: list[str] = []
    for position, (label, box) in enumerate(pattern["boxes"].items(), start=1):
        classes = ["box"]
        if kind == "cards":
            classes.append("kind-card")
        if "accent" in label or "band" in label:
            classes.append("kind-accent")
        if label in ("quote", "attribution"):
            classes.append("kind-quote")
        counter = ""
        if kind == "steps" and label.startswith(("stage ", "step ")):
            counter = f'<span class="step-number">{position}</span>'
        inner = f"<strong>{escape(label)}</strong>{counter}"
        boxes.append(
            f'<div class="{" ".join(classes)}" style="{box_style(box)}">{inner}</div>'
        )
    title = escape(str(plan.get("title") or ""))
    kicker = escape(str(plan.get("kicker") or ""))
    headline = escape(str(plan.get("headline") or ""))
    note = escape(str(plan.get("source_note") or "source"))
    classes = ["canvas", f"pattern-{pattern['key'].replace(' ', '-')}", f"kind-{kind}"]
    header = (
        f'<div class="kind-kicker">{kicker}</div>' if kicker else ""
    )
    headline_block = f'<div class="kind-headline">{headline}</div>' if headline else ""
    title_block = f'<div class="kind-slide-title">{title}</div>' if title else ""
    number = f"{pattern['number']}. " if pattern["number"] else ""
    caption = (
        f'<div class="caption"><strong>{item["index"]}.</strong>'
        f'<span>{escape(number + pattern["name"])} ({escape(pattern["job"])})</span></div>'
    )
    return (
        f'<section class="slide" id="slide-{item["index"]}">'
        f"{caption}"
        f'<div class="{" ".join(classes)}">'
        f"{title_block}{header}{headline_block}"
        f'{"".join(boxes)}'
        f'<div class="kind-source">{note}</div>'
        "</div></section>"
    )


def parse_plan(text: str) -> tuple[dict, list[str]]:
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as error:
        return {}, [f"plan is not valid JSON: {error.msg} at line {error.lineno} column {error.colno}"]
    if not isinstance(plan, dict):
        return {}, ["plan must be a JSON object"]
    slides = plan.get("slides")
    if slides is not None and not isinstance(slides, list):
        return {}, ["plan.slides must be a list"]
    return plan, []


def main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a static HTML design preview from a presentation plan."
    )
    parser.add_argument("--plan", type=Path, help="plan JSON file, or - for stdin")
    parser.add_argument("--out", type=Path, help="HTML output path; omit for a check-only run")
    parser.add_argument("--view", action="store_true", help="text summary of the plan without writing HTML")
    parser.add_argument(
        "--direction",
        help="override the plan's library direction, to preview a candidate without editing the plan",
    )
    return parser


def run(arguments: list[str]) -> int:
    args = main_parser().parse_args(arguments)
    if args.plan is None:
        print("plan: missing --plan; nothing was read or written", file=sys.stderr)
        return 2
    if args.plan is not None and str(args.plan) == "-":
        text = sys.stdin.read()
    else:
        try:
            text = args.plan.read_text(encoding="utf-8")
        except OSError as error:
            print(f"plan: {error}", file=sys.stderr)
            print("nothing was read or written", file=sys.stderr)
            return 2
    plan, problems = parse_plan(text)
    if not problems and args.direction:
        plan["direction"] = {**(plan.get("direction") or {}), "library": args.direction}
    library = load_library()
    if not problems:
        document, problems = build_document(plan, library)
    if problems:
        for problem in problems:
            print(f"plan: {problem}", file=sys.stderr)
        print("no preview written", file=sys.stderr)
        return 1
    if args.view:
        for slide in plan.get("slides", []):
            key = str(slide.get("pattern") or "").strip().lower()
            planned = count_plan_items(slide)
            capacity = ""
            if key in PATTERN_GEOMETRY and planned is not None:
                resolved = resolve_pattern(key, library[0])
                if resolved["capacity"]:
                    capacity = f" | {planned}/{resolved['capacity']} {resolved['name']} capacity"
            print(
                f"{slide.get('pattern')}: {slide.get('headline') or slide.get('title') or '(untitled)'}"
                f"{capacity}"
            )
        print(SCOPE_NOTE, file=sys.stderr)
    if args.out is None:
        return 0
    parent = args.out.parent
    if str(parent) and not parent.exists():
        print(f"plan: output directory does not exist: {parent}", file=sys.stderr)
        print("no preview written", file=sys.stderr)
        return 2
    try:
        args.out.write_text(document, encoding="utf-8")
    except OSError as error:
        print(f"plan: failed to write {args.out}: {error}", file=sys.stderr)
        return 2
    print(f"wrote {args.out} ({len(document)} bytes); open it with the host's browser")
    print(SCOPE_NOTE)
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
