#!/usr/bin/env python3
"""Report integrity findings for a Word, PowerPoint or Excel package without changing it.

Only the standard library is required. The package is read through the bounded
Office inspectors. Every finding carries a rule, severity, location and fix class.
A clean result covers only the static rules listed in references/rules.md: it is
never evidence of visual layout, formula recalculation or schema validity.
"""

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[2]


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, SKILLS / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


xlsx = _load("office_verify_xlsx", "xlsx/scripts/xlsx_inspect.py")
docx = _load("office_verify_docx", "docx/scripts/docx_inspect.py")
pptx = _load("office_verify_pptx", "deckcraft/scripts/pptx_inspect.py")
package = xlsx

SCHEMA = "mukade/office-verify/v1"
FORMATS = {".docx": "docx", ".docm": "docx", ".pptx": "pptx",
           ".xlsx": "xlsx", ".xlsm": "xlsx", ".xltx": "xlsx", ".xltm": "xlsx"}
SEVERITIES = ("error", "warning", "info")
NOT_CHECKED = {
    "docx": ["rendered page layout and pagination", "font availability and substitution",
             "field results such as a table of contents", "OOXML schema validity"],
    "pptx": ["text overflow and overlapping objects (requires rendering)",
             "font availability and substitution", "OOXML schema validity"],
    "xlsx": ["formula recalculation correctness (requires a calculation engine)",
             "circular references (requires a calculation engine)", "OOXML schema validity"],
}
REF = re.compile(r"(?<![A-Za-z0-9_.\\])(\$?)([A-Z]{1,3})(\$?)([0-9]{1,7})(?![A-Za-z0-9_(])")
NUMBER = re.compile(r"(?<![A-Za-z0-9_.$:!\]])(\d+(?:\.\d+)?)(?![A-Za-z0-9_.:(\[])")
STRING = re.compile(r'"(?:[^"]|"")*"')
QUOTED_SHEET = re.compile(r"'(?:[^']|'')*'!")
OPERATORS = set("*/+-")


def finding(rule, severity, location, message, fix):
    return {"rule": rule, "severity": severity, "location": location, "message": message, "fix": fix}


def local(element):
    return package.local_name(element.tag)


def attribute(element, name):
    return next((value for key, value in element.attrib.items() if package.local_name(key) == name), None)


def first(element, name):
    return next((item for item in element if local(item) == name), None)


def decorative(element):
    return any(local(item) == "decorative" and attribute(item, "val") in {"1", "true"} for item in element.iter())


def package_findings(result, external):
    findings = [finding("package.invalid", "error", "package", message, "none") for message in result["errors"]]
    for item in external:
        if not item["type"].endswith("/hyperlink"):
            findings.append(finding("package.external-link", "warning", item["source"] or "package",
                                    "Content depends on an external target: " + item["target"], "review"))
    sensitive = result.get("preservation_sensitive", {})
    if sensitive.get("macros"):
        findings.append(finding("package.macros", "info", ", ".join(sensitive["macros"]),
                                "The file carries macros; they were not run.", "none"))
    return findings


# Word

def heading_levels(roots):
    """Map style id to heading level from built-in names or outline levels."""
    levels = {}
    for root in roots.values():
        if not docx.word(root, "styles"):
            continue
        for style in root:
            if not docx.word(style, "style"):
                continue
            style_id = attribute(style, "styleId")
            name = first(style, "name")
            match = re.fullmatch(r"(?i)heading\s*([1-9])", attribute(name, "val") or "") if name is not None else None
            if match:
                levels[style_id] = int(match.group(1))
                continue
            properties = first(style, "pPr")
            outline = first(properties, "outlineLvl") if properties is not None else None
            if outline is not None and (attribute(outline, "val") or "").isdigit() and int(attribute(outline, "val")) < 9:
                levels[style_id] = int(attribute(outline, "val")) + 1
    return levels


def paragraph_level(paragraph, levels):
    properties = first(paragraph, "pPr")
    if properties is None:
        return None
    outline = first(properties, "outlineLvl")
    if outline is not None and (attribute(outline, "val") or "").isdigit() and int(attribute(outline, "val")) < 9:
        return int(attribute(outline, "val")) + 1
    style = first(properties, "pStyle")
    return levels.get(attribute(style, "val")) if style is not None else None


def empty_paragraph(paragraph):
    return (not docx.native_text(paragraph).strip()
            and not any(local(item) in {"drawing", "pict", "object", "fldChar", "fldSimple", "sectPr", "br"}
                        for item in paragraph.iter()))


def verify_docx(path):
    result, roots = docx._read_with_roots(path)
    findings = package_findings(result, result["external_relationships"])
    if not result["valid"]:
        return result, findings
    main = roots.get(result.get("document_part"))
    levels = heading_levels(roots)
    for name, root in sorted(roots.items()):
        for shape in (item for item in root.iter() if local(item) == "docPr"):
            if not (attribute(shape, "descr") or "").strip() and not decorative(shape):
                findings.append(finding("docx.alt-text-missing", "warning",
                                        f"{name} image '{shape.get('name', shape.get('id', '?'))}'",
                                        "Image has no alternative text.", "content"))
    for story in result["stories"]:
        if story["revisions"]:
            findings.append(finding("docx.tracked-changes", "warning", story["part"],
                                    f"{len(story['revisions'])} unresolved tracked changes.", "review"))
        comments = [item for item in story["comments"] if item["kind"] == "comment"]
        if comments:
            findings.append(finding("docx.comments", "info", story["part"],
                                    f"{len(comments)} comments remain in the document.", "review"))
    if main is not None:
        # Body-level paragraphs only: empty table cells are not spacing.
        body = next((item for item in main if docx.word(item, "body")), main)
        previous, empty_run = 0, []

        def close_run():
            if len(empty_run) >= 3:
                findings.append(finding("docx.empty-paragraph-spacing", "info",
                                        f"{result['document_part']} paragraphs {empty_run[0]}-{empty_run[-1]}",
                                        f"{len(empty_run)} consecutive empty paragraphs used as spacing.", "review"))
            empty_run.clear()

        for index, paragraph in enumerate((item for item in body if docx.word(item, "p")), 1):
            level = paragraph_level(paragraph, levels)
            if level is not None:
                if level > previous + 1:
                    findings.append(finding("docx.heading-skip", "warning", f"{result['document_part']} paragraph {index}",
                                            f"Heading level {level} follows level {previous}; a level is skipped.", "review"))
                previous = level
            if empty_paragraph(paragraph):
                empty_run.append(index)
            else:
                close_run()
        close_run()
        bookmarks = {attribute(item, "name") for root in roots.values() for item in root.iter()
                     if docx.word(item, "bookmarkStart")}
        for link in (item for item in main.iter() if docx.word(item, "hyperlink")):
            anchor = attribute(link, "anchor")
            if anchor and anchor != "_top" and anchor not in bookmarks:
                findings.append(finding("docx.broken-anchor", "error", result["document_part"],
                                        f"Internal link points to missing bookmark '{anchor}'.", "review"))
    return result, findings


# PowerPoint

def transform(element):
    holder = next((item for item in element if local(item) in {"spPr", "grpSpPr", "xfrm"}), None)
    if holder is None:
        return None
    xfrm = holder if local(holder) == "xfrm" else first(holder, "xfrm")
    if xfrm is None:
        return None
    offset, extent = first(xfrm, "off"), first(xfrm, "ext")
    try:
        return (int(offset.get("x")), int(offset.get("y")), int(extent.get("cx")), int(extent.get("cy")))
    except (AttributeError, TypeError, ValueError):
        return None


def shape_name(element):
    properties = next((item for item in element.iter() if local(item) == "cNvPr"), None)
    return properties.get("name", properties.get("id", "?")) if properties is not None else "?"


def placeholder(element):
    return next((item for item in element.iter() if local(item) == "ph"), None)


def shape_text(element):
    return "".join(pptx.text_runs(element)).strip()


def verify_pptx(path):
    result, roots = pptx.read_presentation(path)
    findings = package_findings(result, result["external_relationships"])
    if not result["valid"]:
        return result, findings
    canvas = result.get("canvas") or {}
    try:
        width, height = int(canvas["cx"]), int(canvas["cy"])
    except (KeyError, ValueError):
        width = height = None
    for number, slide_info in enumerate(result["slides"], 1):
        where = f"slide {number} ({slide_info['part']})"
        slide = roots[slide_info["part"]]
        if slide_info["hidden"]:
            findings.append(finding("pptx.hidden-slide", "info", where, "Slide is hidden in the show.", "review"))
        tree = next((item for item in slide.iter() if local(item) == "spTree"), None)
        objects = [] if tree is None else [item for item in tree if local(item) in {"sp", "pic", "graphicFrame", "cxnSp", "grpSp"}]
        titled = False
        for element in objects:
            name = shape_name(element)
            ph = placeholder(element)
            if ph is not None and ph.get("type") in {"title", "ctrTitle"} and shape_text(element):
                titled = True
            box = transform(element)
            if box and width:
                x, y, cx, cy = box
                if x < 0 or y < 0 or x + cx > width or y + cy > height:
                    findings.append(finding("pptx.off-slide", "warning", f"{where} shape '{name}'",
                                            "Object extends beyond the slide canvas.", "review"))
            if local(element) == "sp" and ph is not None and not shape_text(element) \
                    and not any(local(item) == "blipFill" for item in element.iter()):
                findings.append(finding("pptx.empty-placeholder", "warning", f"{where} placeholder '{name}'",
                                        "Placeholder has no content and shows prompt text while editing.", "safe"))
        for picture in (item for item in slide.iter() if local(item) == "pic"):
            properties = next((item for item in picture.iter() if local(item) == "cNvPr"), None)
            if properties is not None and not (properties.get("descr") or "").strip() and not decorative(properties):
                findings.append(finding("pptx.alt-text-missing", "warning", f"{where} picture '{shape_name(picture)}'",
                                        "Picture has no alternative text.", "content"))
        if not titled:
            findings.append(finding("pptx.title-missing", "info", where,
                                    "Slide has no title placeholder with text; screen readers and outlines lose it.", "content"))
    return result, findings


# Excel

def column_number(letters):
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - 64
    return value


def coordinates(ref):
    match = package.CELL_REF.fullmatch(ref)
    return column_number(match.group(1)), int(match.group(2))


def code(text):
    """Formula text with string literals and quoted sheet names neutralized."""
    return QUOTED_SHEET.sub("S!", STRING.sub('""', text))


def relative_form(text, column, row):
    def replace(match):
        col_abs, letters, row_abs, digits = match.groups()
        col = "C" + str(column_number(letters)) if col_abs else "C[" + str(column_number(letters) - column) + "]"
        line = "R" + digits if row_abs else "R[" + str(int(digits) - row) + "]"
        return line + col
    return REF.sub(replace, code(text))


def hardcoded(text):
    source = code(text)
    for match in NUMBER.finditer(source):
        if float(match.group(1)) in (0.0, 1.0):
            continue
        before = source[:match.start()].rstrip()[-1:]
        after = source[match.end():].lstrip("%").lstrip()[:1]
        if before in OPERATORS or after in OPERATORS:
            yield match.group(1)


def verify_xlsx(path):
    result = package.inspect_workbook(path)
    findings = package_findings(result, result["external_relationships"])
    if not result["valid"]:
        return result, findings
    for name in result["defined_names"]:
        if "#REF!" in name["text"]:
            findings.append(finding("xlsx.broken-name", "error", "name " + name["attributes"].get("name", "?"),
                                    "Defined name refers to a deleted range (#REF!).", "review"))
    calc = result["calculation_properties"]
    if calc.get("fullCalcOnLoad") in {"1", "true"}:
        findings.append(finding("xlsx.not-calculated", "warning", "workbook",
                                "Stored results were not calculated by the writer (fullCalcOnLoad).", "safe"))
    for sheet in result["sheets"]:
        title = sheet["name"]
        if sheet.get("formula_cache_missing_count"):
            findings.append(finding("xlsx.not-calculated", "warning", title,
                                    f"{sheet['formula_cache_missing_count']} formulas have no stored result.", "safe"))
        for item in sheet["cached_errors"]:
            if item["formula"]:
                findings.append(finding("xlsx.cached-error", "error", f"{title}!{item['cell']}",
                                        f"Formula result is the error {item['value']}.", "review"))
            else:
                findings.append(finding("xlsx.literal-error", "warning", f"{title}!{item['cell']}",
                                        f"Cell holds the literal error value {item['value']}.", "review"))
        shared, forms = {}, {}
        for ref, formula in sheet["formulas"].items():
            attributes = formula["attributes"]
            if attributes.get("t") == "shared" and formula["text"]:
                shared[attributes.get("si")] = relative_form(formula["text"], *coordinates(ref))
        for ref, formula in sheet["formulas"].items():
            attributes, text = formula["attributes"], formula["text"]
            column, row = coordinates(ref)
            if attributes.get("t") == "shared" and not text:
                forms[(column, row)] = shared.get(attributes.get("si"))
                continue
            forms[(column, row)] = relative_form(text, column, row)
            if "#REF!" in text:
                findings.append(finding("xlsx.ref-error-in-formula", "error", f"{title}!{ref}",
                                        "Formula refers to a deleted range (#REF!).", "review"))
            constants = sorted(set(hardcoded(text)))
            if constants:
                findings.append(finding("xlsx.hardcoded-constant", "info", f"{title}!{ref}",
                                        "Formula embeds constants " + ", ".join(constants)
                                        + "; an input cell keeps assumptions visible.", "review"))
        for (column, row), form in sorted(forms.items()):
            if form is None:
                continue
            for first_neighbor, second_neighbor in (((column, row - 1), (column, row + 1)),
                                                    ((column - 1, row), (column + 1, row))):
                a, b = forms.get(first_neighbor), forms.get(second_neighbor)
                if a is not None and a == b and a != form:
                    findings.append(finding("xlsx.inconsistent-formula", "warning",
                                            f"{title}!{xlsx_ref(column, row)}",
                                            "Formula differs from the matching formulas on both sides.", "review"))
                    break
    return result, findings


def xlsx_ref(column, row):
    letters = ""
    while column:
        column, remainder = divmod(column - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters + str(row)


VERIFIERS = {"docx": verify_docx, "pptx": verify_pptx, "xlsx": verify_xlsx}


def verify(path, max_per_rule=50):
    path = Path(path)
    kind = FORMATS.get(path.suffix.lower())
    if kind is None:
        raise ValueError("Unsupported file type: " + path.suffix + " (supported: " + ", ".join(sorted(FORMATS)) + ")")
    if not path.is_file():
        raise ValueError("File not found: " + str(path))
    inspection, findings = VERIFIERS[kind](path)
    order = {severity: index for index, severity in enumerate(SEVERITIES)}
    findings.sort(key=lambda item: (order[item["severity"]], item["rule"], item["location"]))
    counts = Counter(item["severity"] for item in findings)
    listed, omitted, seen = [], {}, Counter()
    for item in findings:
        seen[item["rule"]] += 1
        if seen[item["rule"]] <= max_per_rule:
            listed.append(item)
        else:
            omitted[item["rule"]] = omitted.get(item["rule"], 0) + 1
    verdict = "fail" if counts["error"] else "warnings" if counts["warning"] else "pass"
    return {
        "schema": SCHEMA, "path": str(path.resolve()), "format": kind,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "package_valid": inspection["valid"], "verdict": verdict,
        "counts": {severity: counts[severity] for severity in SEVERITIES},
        "rules": dict(sorted(Counter(item["rule"] for item in findings).items())),
        "findings": listed, "omitted": omitted, "not_checked": NOT_CHECKED[kind],
        "notice": "Static rules only. A pass is not evidence of layout, recalculation or schema validity.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report integrity findings for an Office file without changing it.")
    parser.add_argument("input", help="DOCX, DOCM, PPTX, XLSX, XLSM, XLTX or XLTM file")
    parser.add_argument("--max-per-rule", type=int, default=50, help="findings listed per rule; counts stay complete")
    args = parser.parse_args(argv)
    try:
        report = verify(args.input, max(args.max_per_rule, 1))
    except ValueError as exc:
        print(json.dumps({"schema": SCHEMA, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["verdict"] == "fail" or not report["package_valid"] else 0


if __name__ == "__main__":
    sys.exit(main())
