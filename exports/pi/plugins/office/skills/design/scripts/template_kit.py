#!/usr/bin/env python3
"""Generate a native PowerPoint or Word base template from a palette and a font pairing.

The output extension selects the package: `.potx` or `.pptx` writes a slide master,
a theme and nine layouts on the 16:9 canvas; `.dotx` or `.docx` writes a theme,
paragraph, character and table styles, page geometry and a page-number footer. The
theme maps the palette roles to the colour scheme and the pairing to the major
and minor fonts, so every engine and Office application inherits them.

    template_kit.py OUT.potx --palette chosen.json --pairing 1 [--samples] [--name TEXT]
    template_kit.py OUT.dotx --palette candidates.json --variant faithful --pairing 4 [--page letter]
    template_kit.py OUT.pptx --palette brand.json --heading-font "Brand Sans" --body-font "Brand Text"

`--palette` takes one palette (the roles background, ink, surface, accent, muted,
data) or `palette.py candidates` output with `--variant` or `--choice`.
`--samples` adds one sample slide per layout, or sample pages, for rendering and
review; the base template has none. Standard library only. Output is
deterministic. Prints a JSON report; exit 0 on success, 1 on invalid input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

SCHEMA = "mukade/template-kit/v1"
PAIRINGS = Path(__file__).resolve().parent.parent / "references" / "font-pairings.md"
HEX = re.compile(r"^#?([0-9A-Fa-f]{6})$")
EMU_IN = 914400
SLIDE_W, SLIDE_H = 12192000, 6858000
MARGIN_X, MARGIN_Y, GAP = 548640, 457200, 228600
CONTENT_W = SLIDE_W - 2 * MARGIN_X
TITLE_Y, TITLE_H = MARGIN_Y, 914400
BODY_Y = TITLE_Y + TITLE_H + GAP
BODY_H = SLIDE_H - MARGIN_Y - BODY_Y
FOOT_Y, FOOT_H = SLIDE_H - 411480, 274320

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
DECORATIVE = ('<a:extLst><a:ext uri="{C183D7F6-B498-43B3-948B-1728B52AA6E4}">'
              '<adec:decorative xmlns:adec="http://schemas.microsoft.com/office/drawing/2017/decorative" val="1"/>'
              '</a:ext></a:extLst>')
MAIN_TYPES = {
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
    ".potx": "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    ".dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml",
}
PAGES = {"a4": (11906, 16838, 1418), "letter": (12240, 15840, 1440)}


class KitError(ValueError):
    """The palette, the fonts or the output cannot produce a template."""


# Inputs

def hex6(value, role):
    match = HEX.match(str(value or ""))
    if not match:
        raise KitError(f"palette role {role!r} is not a #RRGGBB colour: {value!r}")
    return match.group(1).upper()


def load_palette(path, variant=None, choice=None):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "candidates" in data:
        candidates = data["candidates"]
        if variant:
            matches = [item for item in candidates if item.get("variant") == variant]
            if not matches:
                raise KitError(f"no candidate with variant {variant!r}")
            data = matches[0]
        elif choice:
            if not 1 <= choice <= len(candidates):
                raise KitError(f"--choice must be between 1 and {len(candidates)}")
            data = candidates[choice - 1]
        else:
            raise KitError("candidates file: pass --variant or --choice")
    palette = {role: hex6(data.get(role), role) for role in ("background", "ink", "surface", "accent", "muted")}
    palette["data"] = [hex6(item, "data") for item in data.get("data", [])][:4]
    if len(palette["data"]) < 3:
        raise KitError("palette needs three or four data colours")
    palette["dark"] = bool(data.get("dark"))
    palette["name"] = data.get("name") or data.get("variant") or "palette"
    return palette


def _family(text):
    match = re.match(r"\s*(.+?)\s+\d{3}(?:/\d{3})*\b", text)
    if not match:
        raise KitError(f"cannot read a family and weight from {text!r}")
    return match.group(1).strip()


def load_pairing(number):
    # The catalog table is read by its header, so a column added for human
    # readers does not shift the columns this kit depends on.
    columns = None
    for line in PAIRINGS.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[:1] == ["#"]:
            columns = {name: index for index, name in enumerate(cells)}
            continue
        if columns and cells[0] == str(number) and len(cells) == len(columns):
            heading, body = cells[columns["Headings"]], cells[columns["Body"]]
            fallback = cells[columns["Office fallback (headings / body)"]]
            weight = int(re.search(r"\b(\d{3})\b", heading).group(1))
            heading_fallback, _, body_fallback = fallback.partition("/")
            return {
                "pairing": number, "name": cells[1],
                "heading": {"family": _family(heading), "weight": weight,
                            "fallback": heading_fallback.strip()},
                "body": {"family": _family(body), "weight": 400,
                         "fallback": body_fallback.strip().split(",")[0].strip()},
            }
    raise KitError(f"pairing {number} is not in {PAIRINGS.name}")


def resolve_fonts(pairing=None, heading_font=None, body_font=None):
    if pairing is None and not (heading_font and body_font):
        raise KitError("pass --pairing, or both --heading-font and --body-font")
    fonts = load_pairing(pairing) if pairing is not None else {
        "pairing": None, "name": "supplied fonts",
        "heading": {"family": heading_font, "weight": 700, "fallback": None},
        "body": {"family": body_font, "weight": 400, "fallback": None},
    }
    if heading_font:
        fonts["heading"] = {"family": heading_font, "weight": 700, "fallback": None}
    if body_font:
        fonts["body"] = {"family": body_font, "weight": 400, "fallback": None}
    return fonts


# Theme

def scheme(palette):
    """Map palette roles to the twelve theme colours, honouring a dark palette."""
    accents = list(palette["data"])
    if palette["accent"] not in accents:
        accents.insert(0, palette["accent"])
    for extra in (palette["muted"], palette["ink"]):
        if len(accents) < 6 and extra not in accents:
            accents.append(extra)
    while len(accents) < 6:
        accents.append(accents[len(accents) % 4])
    if palette["dark"]:
        base = {"dk1": palette["background"], "lt1": palette["ink"],
                "dk2": palette["surface"], "lt2": palette["muted"]}
        mapping = {"bg1": "dk1", "tx1": "lt1", "bg2": "dk2", "tx2": "lt2"}
    else:
        base = {"dk1": palette["ink"], "lt1": palette["background"],
                "dk2": palette["muted"], "lt2": palette["surface"]}
        mapping = {"bg1": "lt1", "tx1": "dk1", "bg2": "lt2", "tx2": "dk2"}
    colours = {**base, **{f"accent{n}": value for n, value in enumerate(accents[:6], 1)},
               "hlink": palette["accent"], "folHlink": palette["muted"]}
    return colours, mapping


def theme_xml(name, colours, fonts):
    order = ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4",
             "accent5", "accent6", "hlink", "folHlink")
    clr = "".join(f'<a:{key}><a:srgbClr val="{colours[key]}"/></a:{key}>' for key in order)

    def font(kind, family):
        return (f'<a:{kind}><a:latin typeface={quoteattr(family)}/><a:ea typeface=""/>'
                f'<a:cs typeface=""/></a:{kind}>')

    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    line = '<a:ln w="{w}" cap="flat" cmpd="sng" algn="ctr">' + fill + '<a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>'
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<a:theme xmlns:a="{A}" name={quoteattr(name)}>'
            f'<a:themeElements><a:clrScheme name={quoteattr(name)}>{clr}</a:clrScheme>'
            f'<a:fontScheme name={quoteattr(name)}>{font("majorFont", fonts["heading"]["family"])}'
            f'{font("minorFont", fonts["body"]["family"])}</a:fontScheme>'
            f'<a:fmtScheme name={quoteattr(name)}><a:fillStyleLst>{fill * 3}</a:fillStyleLst>'
            f'<a:lnStyleLst>{"".join(line.format(w=w) for w in (6350, 12700, 19050))}</a:lnStyleLst>'
            f'<a:effectStyleLst>{"<a:effectStyle><a:effectLst/></a:effectStyle>" * 3}</a:effectStyleLst>'
            f'<a:bgFillStyleLst>{fill * 3}</a:bgFillStyleLst></a:fmtScheme></a:themeElements>'
            '<a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')


# Package

def write_package(path, parts):
    """Write parts in a fixed order with a fixed timestamp so output is reproducible."""
    names = ["[Content_Types].xml", "_rels/.rels"] + sorted(set(parts) - {"[Content_Types].xml", "_rels/.rels"})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, parts[name])


def rels(items):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{PR}">'
            + "".join(f'<Relationship Id="{rel_id}" Type="{kind}" Target="{target}"/>'
                      for rel_id, kind, target in items) + "</Relationships>")


def content_types(overrides):
    defaults = ('<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="{CT}">{defaults}'
            + "".join(f'<Override PartName="/{name}" ContentType="{kind}"/>' for name, kind in overrides)
            + "</Types>")


def doc_props(name, application):
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>' + escape(name) + '</dc:title>'
            '<dc:creator>Mukade template kit</dc:creator></cp:coreProperties>')
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           f'<Application>{application}</Application></Properties>')
    return core, app


PACKAGE_RELS = (
    ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
    ("rId3", f"{R}/extended-properties", "docProps/app.xml"),
)
PROPS_TYPES = (
    ("docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
    ("docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml"),
)


# PowerPoint

def xfrm(x, y, cx, cy):
    return f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'


def run_props(size=None, bold=False, italic=False, colour=None, font=None):
    attributes = (f' sz="{size}"' if size else "") + (' b="1"' if bold else "") + (' i="1"' if italic else "")
    fill = f'<a:solidFill><a:schemeClr val="{colour}"/></a:solidFill>' if colour else ""
    face = (f'<a:latin typeface="{font}"/><a:ea typeface="{font.replace("lt", "ea")}"/>'
            f'<a:cs typeface="{font.replace("lt", "cs")}"/>') if font else ""
    return f'<a:defRPr{attributes}>{fill}{face}</a:defRPr>'


def level(number, size, bullet=True, bold=False, colour="tx1", font="+mn-lt", space=800, align=None):
    margin = 285750 * number if bullet else 0
    indent = ' indent="-285750"' if bullet else ""
    bullets = ('<a:buClr><a:schemeClr val="accent1"/></a:buClr><a:buFont typeface="Arial"/><a:buChar char="&#8226;"/>'
               if bullet else "<a:buNone/>")
    algn = f' algn="{align}"' if align else ""
    return (f'<a:lvl{number}pPr marL="{margin}"{indent}{algn}><a:lnSpc><a:spcPct val="110000"/></a:lnSpc>'
            f'<a:spcBef><a:spcPts val="{space}"/></a:spcBef>{bullets}'
            f'{run_props(size, bold, colour=colour, font=font)}</a:lvl{number}pPr>')


def list_style(size, bold=False, colour="tx1", font="+mn-lt", align=None, italic=False):
    attributes = f' algn="{align}"' if align else ""
    props = run_props(size, bold, italic, colour, font)
    return (f'<a:lstStyle><a:lvl1pPr marL="0" indent="0"{attributes}><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
            f'<a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/>{props}</a:lvl1pPr></a:lstStyle>')


def placeholder(shape_id, name, ph, box=None, styles="", text="", fill=None, anchor="t", inset=0):
    geometry = (xfrm(*box) + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>') if box else ""
    background = f'<a:solidFill><a:schemeClr val="{fill}"/></a:solidFill>' if fill else ""
    paragraph = f'<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>{escape(text)}</a:t></a:r></a:p>' if text else "<a:p/>"
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name={quoteattr(name)}/><p:cNvSpPr><a:spLocks noGrp="1"/>'
            f'</p:cNvSpPr><p:nvPr>{ph}</p:nvPr></p:nvSpPr><p:spPr>{geometry}{background}</p:spPr>'
            f'<p:txBody><a:bodyPr lIns="{inset}" tIns="{inset}" rIns="{inset}" bIns="{inset}" anchor="{anchor}">'
            f'<a:normAutofit/></a:bodyPr>{styles}{paragraph}</p:txBody></p:sp>')


def band(shape_id, name, box, colour):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name={quoteattr(name)}>{DECORATIVE}</p:cNvPr><p:cNvSpPr/>'
            f'<p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr>{xfrm(*box)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:schemeClr val="{colour}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>')


def footers(start, inverse=False):
    colour = "bg1" if inverse else "tx2"
    style = list_style(1100, colour=colour)
    third = (CONTENT_W - 2 * GAP) // 3
    date = ('<a:p><a:fld id="{4C9D1A2E-6F0B-4E8A-9C1D-2B3A4C5D6E70}" type="datetimeFigureOut">'
            '<a:rPr lang="en-US"/><a:t>Date</a:t></a:fld></a:p>')
    number = ('<a:p><a:pPr algn="r"/><a:fld id="{7E2F3A4B-5C6D-4E8F-9A0B-1C2D3E4F5A60}" type="slidenum">'
              '<a:rPr lang="en-US"/><a:t>&#8249;#&#8250;</a:t></a:fld></a:p>')
    shapes = []
    for offset, (kind, size, idx, label, body) in enumerate((
            ("dt", "half", 10, "Date Placeholder", date), ("ftr", "quarter", 11, "Footer Placeholder", "<a:p/>"),
            ("sldNum", "quarter", 12, "Slide Number Placeholder", number))):
        box = (MARGIN_X + offset * (third + GAP), FOOT_Y, third, FOOT_H)
        shapes.append(placeholder(start + offset, label, f'<p:ph type="{kind}" sz="{size}" idx="{idx}"/>', box,
                                  style, anchor="ctr").replace("<a:p/></p:txBody>", body + "</p:txBody>"))
    return "".join(shapes)


def tree(shapes):
    return ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
            f'<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{shapes}</p:spTree>')


TITLE_BOX = (MARGIN_X, TITLE_Y, CONTENT_W, TITLE_H)
BODY_BOX = (MARGIN_X, BODY_Y, CONTENT_W, BODY_H)
HALF_W = (CONTENT_W - GAP) // 2
THIRD_W = (CONTENT_W - 2 * GAP) // 3
CHART_W = CONTENT_W * 62 // 100
LEFT_W = SLIDE_W * 2 // 3

# name, type, master shapes shown, patterns served, shapes, sample texts by placeholder name
LAYOUTS = (
    ("Cover", "title", False, ["Cover"], lambda: (
        band(20, "Accent band", (LEFT_W, 0, SLIDE_W - LEFT_W, SLIDE_H), "accent1")
        + placeholder(2, "Title", '<p:ph type="ctrTitle"/>', (MARGIN_X, 1828800, LEFT_W - MARGIN_X - GAP, 1600200),
                      list_style(4800, True, font="+mj-lt"), anchor="b")
        + placeholder(3, "Subtitle", '<p:ph type="subTitle" idx="1"/>', (MARGIN_X, 3566160, LEFT_W - MARGIN_X - GAP, 914400),
                      list_style(2000, colour="tx2"))
        + placeholder(4, "Meta", '<p:ph type="body" sz="quarter" idx="13"/>', (MARGIN_X, 5394960, LEFT_W - MARGIN_X - GAP, 457200),
                      list_style(1400, colour="tx2"), anchor="b")
        + placeholder(5, "Picture", '<p:ph type="pic" sz="quarter" idx="14"/>', (LEFT_W, 0, SLIDE_W - LEFT_W, SLIDE_H))),
     {"Title": "Deck title on two lines at most", "Subtitle": "What the audience will decide",
      "Meta": "Audience · Presenter · Date"}),
    ("Section", "secHead", False, ["Section divider"], lambda: (
        band(20, "Section background", (0, 0, SLIDE_W, SLIDE_H), "accent1")
        + placeholder(2, "Section number", '<p:ph type="body" idx="1"/>', (MARGIN_X, 2148840, CONTENT_W, 548640),
                      list_style(1400, True, colour="bg1"), anchor="b")
        + placeholder(3, "Title", '<p:ph type="title"/>', (MARGIN_X, 2788920, CONTENT_W, 1463040),
                      list_style(4000, True, colour="bg1", font="+mj-lt"))
        + footers(10, inverse=True)),
     {"Section number": "02", "Title": "Section title"}),
    ("Title and Content", "obj", True, ["Agenda", "Next steps and decision request"], lambda: (
        placeholder(2, "Title", '<p:ph type="title"/>')
        + placeholder(3, "Content", '<p:ph idx="1"/>') + footers(10)),
     {"Title": "Headline states the takeaway", "Content": "First point with its evidence"}),
    ("Two Content", "twoObj", True, ["Comparison matrix", "Case study"], lambda: (
        placeholder(2, "Title", '<p:ph type="title"/>')
        + placeholder(3, "Left", '<p:ph sz="half" idx="1"/>', (MARGIN_X, BODY_Y, HALF_W, BODY_H))
        + placeholder(4, "Right", '<p:ph sz="half" idx="2"/>', (MARGIN_X + HALF_W + GAP, BODY_Y, HALF_W, BODY_H))
        + footers(10)),
     {"Title": "Two options compared on the same criteria", "Left": "Option A", "Right": "Option B"}),
    ("Chart and Insight", "obj", True, ["Chart and insight"], lambda: (
        placeholder(2, "Title", '<p:ph type="title"/>')
        + placeholder(3, "Chart", '<p:ph type="chart" sz="half" idx="1"/>', (MARGIN_X, BODY_Y, CHART_W, BODY_H))
        + placeholder(4, "Insight", '<p:ph type="body" sz="half" idx="2"/>',
                      (MARGIN_X + CHART_W + GAP, BODY_Y, CONTENT_W - CHART_W - GAP, BODY_H),
                      list_style(1600), fill="bg2", inset=182880)
        + footers(10)),
     {"Title": "The chart's finding in one line", "Insight": "What the data means for the decision"}),
    ("Key Metrics", "obj", True, ["Key metric spotlight"], lambda: (
        placeholder(2, "Title", '<p:ph type="title"/>')
        + "".join(placeholder(3 + n, f"Metric {n + 1}", f'<p:ph type="body" sz="quarter" idx="{15 + n}"/>',
                              (MARGIN_X + n * (THIRD_W + GAP), BODY_Y, THIRD_W, 2286000),
                              list_style(4400, True, colour="accent1", font="+mj-lt"), fill="bg2",
                              anchor="ctr", inset=182880) for n in range(3))
        + placeholder(6, "Context", '<p:ph type="body" sz="quarter" idx="18"/>',
                      (MARGIN_X, BODY_Y + 2286000 + GAP, CONTENT_W, 1371600), list_style(1600, colour="tx2"))
        + footers(10)),
     {"Title": "Three numbers that carry the argument", "Metric 1": "42%", "Metric 2": "3.1 M",
      "Metric 3": "+18", "Context": "Period and source of every value"}),
    ("Quote", "obj", True, ["Quote and testimonial"], lambda: (
        placeholder(2, "Title", '<p:ph type="title"/>', (MARGIN_X, TITLE_Y, CONTENT_W, 548640),
                    list_style(1600, True, colour="accent1"))
        + placeholder(3, "Quote", '<p:ph type="body" idx="1"/>', (1371600, 1828800, SLIDE_W - 2 * 1371600, 2743200),
                      list_style(2800, italic=True, font="+mj-lt", align="ctr"), anchor="ctr")
        + placeholder(4, "Attribution", '<p:ph type="body" sz="quarter" idx="19"/>',
                      (1371600, 4754880, SLIDE_W - 2 * 1371600, 548640), list_style(1600, colour="tx2", align="ctr"))
        + footers(10)),
     {"Title": "Customer voice", "Quote": "An exact quotation, never an invented one.",
      "Attribution": "Name, role, organisation"}),
    ("Title Only", "titleOnly", True, ["Executive summary", "Options and recommendation", "Data table",
                                       "Timeline and roadmap", "Process flow", "Architecture and system map",
                                       "Risk and mitigation table", "Team and organization",
                                       "Workshop and training plan"], lambda: (
        placeholder(2, "Title", '<p:ph type="title"/>') + footers(10)),
     {"Title": "Headline above native tables, diagrams or cards"}),
    ("Blank", "blank", True, [], lambda: footers(10), {}),
)


def master_xml(mapping, layout_count):
    body = "".join(level(n, size) for n, size in ((1, 1800), (2, 1600), (3, 1400)))
    body += "".join(level(n, 1400) for n in (4, 5))
    title = ('<a:lvl1pPr algn="l"><a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:spcBef><a:spcPct val="0"/></a:spcBef>'
             f'<a:buNone/>{run_props(3000, True, colour="tx1", font="+mj-lt")}</a:lvl1pPr>')
    other = f'<a:lvl1pPr>{run_props(1800, colour="tx1", font="+mn-lt")}</a:lvl1pPr>'
    clr = " ".join(f'{key}="{value}"' for key, value in mapping.items())
    shapes = (placeholder(2, "Title Placeholder", '<p:ph type="title"/>', TITLE_BOX, anchor="b", text="Click to edit title")
              + placeholder(3, "Text Placeholder", '<p:ph type="body" idx="1"/>', BODY_BOX, text="Click to edit text")
              + footers(4) + band(20, "Accent rule", (MARGIN_X, 320040, 457200, 45720), "accent1"))
    layouts = "".join(f'<p:sldLayoutId id="{2147483649 + n}" r:id="rId{n + 1}"/>' for n in range(layout_count))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sldMaster xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}">'
            '<p:cSld><p:bg><p:bgPr><a:solidFill><a:schemeClr val="bg1"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
            f'{tree(shapes)}</p:cSld>'
            f'<p:clrMap {clr} accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
            'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            f'<p:sldLayoutIdLst>{layouts}</p:sldLayoutIdLst><p:txStyles><p:titleStyle>{title}</p:titleStyle>'
            f'<p:bodyStyle>{body}</p:bodyStyle><p:otherStyle>{other}</p:otherStyle></p:txStyles></p:sldMaster>')


def layout_xml(name, kind, show_master, shapes):
    hide = "" if show_master else ' showMasterSp="0"'
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sldLayout xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}" '
            f'type="{kind}" preserve="1"{hide}><p:cSld name={quoteattr(name)}>{tree(shapes)}</p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def sample_slide(shapes, texts):
    """Copy the layout's placeholders that have sample text, with neither geometry nor body
    properties, so position, insets and anchoring all come from the layout."""
    kept = []
    for match in re.finditer(r'<p:sp><p:nvSpPr><p:cNvPr id="(\d+)" name="([^"]*)"/>.*?<p:nvPr>(<p:ph [^>]*/>)</p:nvPr>', shapes):
        shape_id, name, ph = match.groups()
        if name in texts:
            shape = placeholder(shape_id, name, ph, text=texts[name])
            kept.append(re.sub(r"<a:bodyPr[^>]*>.*?</a:bodyPr>", "<a:bodyPr/>", shape))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sld xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}">'
            f'<p:cSld>{tree("".join(kept))}</p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def build_presentation(out, name, colours, mapping, fonts, samples):
    ml = "application/vnd.openxmlformats-officedocument.presentationml."
    parts, overrides = {}, [("ppt/presentation.xml", MAIN_TYPES[out.suffix.lower()])]
    layout_rels = []
    report = []
    slides = []
    for number, (layout, kind, show, patterns, shapes, texts) in enumerate(LAYOUTS, 1):
        xml = shapes()
        part = f"ppt/slideLayouts/slideLayout{number}.xml"
        parts[part] = layout_xml(layout, kind, show, xml)
        parts[f"ppt/slideLayouts/_rels/slideLayout{number}.xml.rels"] = rels(
            [("rId1", f"{R}/slideMaster", "../slideMasters/slideMaster1.xml")])
        overrides.append((part, ml + "slideLayout+xml"))
        layout_rels.append((f"rId{number}", f"{R}/slideLayout", f"../slideLayouts/slideLayout{number}.xml"))
        report.append({"name": layout, "type": kind, "patterns": patterns})
        if samples and texts:
            slides.append((number, sample_slide(xml, texts)))
    parts["ppt/slideMasters/slideMaster1.xml"] = master_xml(mapping, len(LAYOUTS))
    parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = rels(
        layout_rels + [(f"rId{len(LAYOUTS) + 1}", f"{R}/theme", "../theme/theme1.xml")])
    parts["ppt/theme/theme1.xml"] = theme_xml(name, colours, fonts)
    overrides += [("ppt/slideMasters/slideMaster1.xml", ml + "slideMaster+xml"),
                  ("ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml")]
    presentation_rels = [("rId1", f"{R}/slideMaster", "slideMasters/slideMaster1.xml"),
                         ("rId2", f"{R}/theme", "theme/theme1.xml"),
                         ("rId3", f"{R}/presProps", "presProps.xml"),
                         ("rId4", f"{R}/viewProps", "viewProps.xml"),
                         ("rId5", f"{R}/tableStyles", "tableStyles.xml")]
    slide_ids = []
    for index, (layout_number, xml) in enumerate(slides, 1):
        part = f"ppt/slides/slide{index}.xml"
        parts[part] = xml
        parts[f"ppt/slides/_rels/slide{index}.xml.rels"] = rels(
            [("rId1", f"{R}/slideLayout", f"../slideLayouts/slideLayout{layout_number}.xml")])
        overrides.append((part, ml + "slide+xml"))
        presentation_rels.append((f"rId{10 + index}", f"{R}/slide", f"slides/slide{index}.xml"))
        slide_ids.append(f'<p:sldId id="{255 + index}" r:id="rId{10 + index}"/>')
    default_text = ('<p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr>'
                    f'<a:lvl1pPr marL="0" algn="l">{run_props(1800, colour="tx1", font="+mn-lt")}</a:lvl1pPr>'
                    '</p:defaultTextStyle>')
    parts["ppt/presentation.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:presentation xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}" '
        'saveSubsetFonts="1"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        + (f'<p:sldIdLst>{"".join(slide_ids)}</p:sldIdLst>' if slide_ids else "")
        + f'<p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}"/><p:notesSz cx="6858000" cy="9144000"/>{default_text}</p:presentation>')
    parts["ppt/_rels/presentation.xml.rels"] = rels(presentation_rels)
    parts["ppt/presProps.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:presentationPr xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"/>'
    parts["ppt/viewProps.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:viewPr xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"/>'
    parts["ppt/tableStyles.xml"] = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<a:tblStyleLst xmlns:a="{A}" '
                                    'def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>')
    overrides += [("ppt/presProps.xml", ml + "presProps+xml"), ("ppt/viewProps.xml", ml + "viewProps+xml"),
                  ("ppt/tableStyles.xml", ml + "tableStyles+xml")]
    parts["docProps/core.xml"], parts["docProps/app.xml"] = doc_props(name, "Mukade template kit")
    parts["_rels/.rels"] = rels([("rId1", f"{R}/officeDocument", "ppt/presentation.xml"), *PACKAGE_RELS])
    parts["[Content_Types].xml"] = content_types(overrides + list(PROPS_TYPES))
    write_package(out, parts)
    return {"layouts": report, "sample_slides": len(slides)}


# Word

def word_run(fonts=None, size=None, bold=False, italic=False, colour=None, extra=""):
    face = (f'<w:rFonts w:asciiTheme="{fonts}HAnsi" w:hAnsiTheme="{fonts}HAnsi" w:eastAsiaTheme="{fonts}EastAsia" '
            f'w:cstheme="{fonts}Bidi"/>') if fonts else ""
    return ("<w:rPr>" + face + ("<w:b/><w:bCs/>" if bold else "") + ("<w:i/><w:iCs/>" if italic else "")
            + (f'<w:color w:val="{colour}"/>' if colour else "") + extra
            + (f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else "") + "</w:rPr>")


def paragraph_style(style_id, name, ppr="", rpr="", based="Normal", following="Normal", outline=None, priority=None):
    outline_xml = f'<w:outlineLvl w:val="{outline}"/>' if outline is not None else ""
    return (f'<w:style w:type="paragraph" w:styleId="{style_id}"><w:name w:val="{name}"/>'
            + (f'<w:basedOn w:val="{based}"/>' if based else "") + (f'<w:next w:val="{following}"/>' if following else "")
            + (f'<w:uiPriority w:val="{priority}"/>' if priority is not None else "")
            + f"<w:qFormat/><w:pPr>{ppr}{outline_xml}</w:pPr>{rpr}</w:style>")


def styles_xml(palette):
    ink, accent, muted, surface = palette["ink"], palette["accent"], palette["muted"], palette["surface"]
    keep = "<w:keepNext/><w:keepLines/>"
    heading = lambda before, after: keep + f'<w:spacing w:before="{before}" w:after="{after}" w:line="259" w:lineRule="auto"/>'
    styles = [
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>',
        '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont"><w:name w:val="Default Paragraph Font"/>'
        '<w:uiPriority w:val="1"/><w:semiHidden/><w:unhideWhenUsed/></w:style>',
        paragraph_style("Title", "Title", '<w:spacing w:after="120" w:line="240" w:lineRule="auto"/>',
                        word_run("major", 56, True, colour=ink), priority=10),
        paragraph_style("Subtitle", "Subtitle", '<w:spacing w:after="480"/>', word_run("minor", 28, colour=muted),
                        priority=11),
        paragraph_style("Heading1", "heading 1", heading(480, 160), word_run("major", 40, True, colour=accent),
                        outline=0, priority=9),
        paragraph_style("Heading2", "heading 2", heading(360, 120), word_run("major", 30, True, colour=ink),
                        outline=1, priority=9),
        paragraph_style("Heading3", "heading 3", heading(240, 80), word_run("major", 24, True, colour=ink),
                        outline=2, priority=9),
        paragraph_style("Quote", "Quote", f'<w:pBdr><w:left w:val="single" w:sz="24" w:space="12" w:color="{accent}"/></w:pBdr>'
                        '<w:spacing w:before="240" w:after="240"/><w:ind w:left="567" w:right="567"/>',
                        word_run("minor", 24, italic=True, colour=ink), priority=29),
        paragraph_style("Caption", "caption", '<w:spacing w:before="80" w:after="240"/>',
                        word_run("minor", 18, colour=muted), priority=35),
        paragraph_style("ListParagraph", "List Paragraph", '<w:ind w:left="720"/><w:contextualSpacing/>', priority=34),
        paragraph_style("Footer", "footer", '<w:tabs><w:tab w:val="right" w:pos="9026"/></w:tabs>'
                        '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/>', word_run("minor", 18, colour=muted),
                        following=None, priority=99),
        f'<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:uiPriority w:val="99"/>'
        f'<w:unhideWhenUsed/>{word_run(colour=accent, extra=chr(60) + "w:u w:val=" + chr(34) + "single" + chr(34) + "/>")}</w:style>',
        '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:uiPriority w:val="99"/>'
        '<w:semiHidden/><w:unhideWhenUsed/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar>'
        '<w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/>'
        '<w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>',
        f'<w:style w:type="table" w:styleId="KitTable"><w:name w:val="Kit Table"/><w:basedOn w:val="TableNormal"/>'
        f'<w:uiPriority w:val="40"/><w:pPr><w:spacing w:before="60" w:after="60" w:line="240" w:lineRule="auto"/></w:pPr>'
        f'{word_run(size=20)}<w:tblPr><w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="{ink}"/>'
        f'<w:bottom w:val="single" w:sz="8" w:space="0" w:color="{ink}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{muted}"/></w:tblBorders><w:tblCellMar>'
        '<w:left w:w="108" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr>'
        f'<w:tblStylePr w:type="firstRow">{word_run(bold=True, colour=ink)}<w:tcPr>'
        f'<w:shd w:val="clear" w:color="auto" w:fill="{surface}"/></w:tcPr></w:tblStylePr></w:style>',
    ]
    defaults = (f'<w:docDefaults><w:rPrDefault>{word_run("minor", 22, colour=ink, extra=chr(60) + "w:lang w:val=" + chr(34) + "en-US" + chr(34) + "/>")}'
                '</w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="288" w:lineRule="auto"/></w:pPr>'
                '</w:pPrDefault></w:docDefaults>')
    # w:lang follows w:sz in the schema order of run properties.
    defaults = defaults.replace('<w:lang w:val="en-US"/><w:sz w:val="22"/><w:szCs w:val="22"/>',
                                '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US"/>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles xmlns:w="{W}" xmlns:r="{R}">'
            + defaults + "".join(styles) + "</w:styles>")


def word_paragraph(text, style=None):
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f'<w:p>{style_xml}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def sample_table(width):
    column = width // 3
    rows = (("Item", "Owner", "Date"), ("Kick-off", "Programme lead", "2026-11-03"), ("Pilot", "Operations", "2026-12-01"))
    body = "".join("<w:tr>" + "".join(
        f'<w:tc><w:tcPr><w:tcW w:w="{column}" w:type="dxa"/></w:tcPr>{word_paragraph(cell)}</w:tc>' for cell in row)
        + "</w:tr>" for row in rows)
    return ('<w:tbl><w:tblPr><w:tblStyle w:val="KitTable"/><w:tblW w:w="5000" w:type="pct"/>'
            '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
            f'</w:tblPr><w:tblGrid>{"".join(f"<w:gridCol w:w={chr(34)}{column}{chr(34)}/>" for _ in range(3))}</w:tblGrid>'
            f"{body}</w:tbl>")


def build_document(out, name, colours, palette, fonts, samples, page):
    width, height, margin = PAGES[page]
    ml = "application/vnd.openxmlformats-officedocument.wordprocessingml."
    if samples:
        content = "".join((
            word_paragraph("Document title", "Title"), word_paragraph("Subtitle states the purpose", "Subtitle"),
            word_paragraph("First section", "Heading1"),
            word_paragraph("Body text sets the reading measure, line spacing and colour of the document."),
            word_paragraph("A subsection", "Heading2"), word_paragraph("A quotation stands apart from the argument.", "Quote"),
            word_paragraph("A detail heading", "Heading3"), sample_table(width - 2 * margin),
            word_paragraph("Table 1. Caption names the table and its source.", "Caption")))
    else:
        content = "<w:p/>"
    section = (f'<w:sectPr><w:footerReference w:type="default" r:id="rId4"/><w:pgSz w:w="{width}" w:h="{height}"/>'
               f'<w:pgMar w:top="{margin}" w:right="{margin}" w:bottom="{margin}" w:left="{margin}" w:header="709" '
               'w:footer="709" w:gutter="0"/><w:cols w:space="708"/></w:sectPr>')
    page_field = ('<w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="right"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                  '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>'
                  '<w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    header = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    parts = {
        "word/document.xml": f'{header}<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{content}{section}</w:body></w:document>',
        "word/styles.xml": styles_xml(palette),
        "word/settings.xml": (f'{header}<w:settings xmlns:w="{W}"><w:defaultTabStop w:val="709"/>'
                              '<w:characterSpacingControl w:val="doNotCompress"/><w:compat><w:compatSetting '
                              'w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
                              '</w:compat></w:settings>'),
        "word/theme/theme1.xml": theme_xml(name, colours, fonts),
        "word/footer1.xml": f'{header}<w:ftr xmlns:w="{W}" xmlns:r="{R}">{page_field}</w:ftr>',
        "word/_rels/document.xml.rels": rels([
            ("rId1", f"{R}/styles", "styles.xml"), ("rId2", f"{R}/settings", "settings.xml"),
            ("rId3", f"{R}/theme", "theme/theme1.xml"), ("rId4", f"{R}/footer", "footer1.xml")]),
        "_rels/.rels": rels([("rId1", f"{R}/officeDocument", "word/document.xml"), *PACKAGE_RELS]),
    }
    parts["docProps/core.xml"], parts["docProps/app.xml"] = doc_props(name, "Mukade template kit")
    parts["[Content_Types].xml"] = content_types([
        ("word/document.xml", MAIN_TYPES[out.suffix.lower()]), ("word/styles.xml", ml + "styles+xml"),
        ("word/settings.xml", ml + "settings+xml"), ("word/footer1.xml", ml + "footer+xml"),
        ("word/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"), *PROPS_TYPES])
    write_package(out, parts)
    return {"styles": ["Title", "Subtitle", "Heading1", "Heading2", "Heading3", "Quote", "Caption",
                       "ListParagraph", "Footer", "Hyperlink", "KitTable"], "page": page,
            "sample_pages": bool(samples)}


def build(out, palette, fonts, name=None, samples=False, page="a4"):
    out = Path(out)
    suffix = out.suffix.lower()
    if suffix not in MAIN_TYPES:
        raise KitError("output must end in .potx, .pptx, .dotx or .docx")
    name = name or f"Kit {palette['name']}"
    colours, mapping = scheme(palette)
    notes = []
    heading = fonts["heading"]
    if heading["weight"] not in (400, 700):
        notes.append(f"Heading weight {heading['weight']} is set as bold (700): the theme names families, "
                     "and DeckCraft draws only Regular, Bold and Italic faces.")
    if suffix in (".potx", ".pptx"):
        detail = build_presentation(out, name, colours, mapping, fonts, samples)
        kind = "presentation"
    else:
        detail = build_document(out, name, colours, palette, fonts, samples, page)
        kind = "document"
    return {"schema": SCHEMA, "path": str(out.resolve()), "kind": kind,
            "template": suffix in (".potx", ".dotx"), "name": name,
            "theme_colours": colours, "colour_map": mapping,
            "fonts": {"major": heading["family"], "minor": fonts["body"]["family"], "pairing": fonts["pairing"],
                      "fallbacks": {"heading": heading["fallback"], "body": fonts["body"]["fallback"]}},
            **detail, "notes": notes,
            "notice": "Structure and theme only. Open the result in the target application and render it before "
                      "claiming visual fidelity."}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a PowerPoint or Word base template from a palette and fonts.")
    parser.add_argument("output", help="path ending in .potx, .pptx, .dotx or .docx; never an existing file")
    parser.add_argument("--palette", required=True, help="palette JSON, or palette.py candidates output")
    parser.add_argument("--variant", help="candidate variant to use (sober, faithful, bold, deep, dark)")
    parser.add_argument("--choice", type=int, help="1-based candidate number to use")
    parser.add_argument("--pairing", type=int, help="font pairing number from references/font-pairings.md")
    parser.add_argument("--heading-font", help="heading family, overriding the pairing (brand fonts)")
    parser.add_argument("--body-font", help="body family, overriding the pairing (brand fonts)")
    parser.add_argument("--name", help="theme and template name")
    parser.add_argument("--samples", action="store_true", help="add sample slides or pages for rendering and review")
    parser.add_argument("--page", choices=sorted(PAGES), default="a4", help="Word page size")
    args = parser.parse_args(argv)
    try:
        if Path(args.output).exists():
            raise KitError(f"output exists and is never overwritten: {args.output}")
        palette = load_palette(args.palette, args.variant, args.choice)
        fonts = resolve_fonts(args.pairing, args.heading_font, args.body_font)
        report = build(args.output, palette, fonts, args.name, args.samples, args.page)
    except (KitError, OSError, ValueError) as error:
        print(json.dumps({"schema": SCHEMA, "ok": False, "error": str(error)}, indent=2))
        return 1
    print(json.dumps({"ok": True, **report}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
