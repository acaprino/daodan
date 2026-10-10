#!/usr/bin/env python3
"""Inspect and compare native spreadsheet packages without evaluating formulas.

Only the standard library is required. Inspection is read-only and bounded. A
clean result establishes package structure, never formula recalculation or visual
quality. Comparison reports deltas; the task determines whether they are intended.
"""

import argparse
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


MAX_PARTS = 10000
MAX_PART_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_CELLS = 250000
MAX_XML_NODES = 1000000
SHEET_NAMESPACES = {
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "http://purl.oclc.org/ooxml/spreadsheetml/main",
}
REL_NAMESPACES = {
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://purl.oclc.org/ooxml/officeDocument/relationships",
}
PACKAGE_REL_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPE_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/content-types"
CELL_REF = re.compile(r"^([A-Z]{1,3})([1-9][0-9]{0,6})$")
DELTA_NOTICE = (
    "Observed changes require review against the task's authorized edits. "
    "A removed part or changed formula is not automatically a defect."
)


class InspectionError(ValueError):
    """A package cannot be inspected safely or completely."""


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def namespace(tag):
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def children(element, name):
    return [child for child in element if local_name(child.tag) == name]


def child(element, name):
    return next((item for item in element if local_name(item.tag) == name), None)


def relation_id(element):
    for uri in REL_NAMESPACES:
        value = element.get("{" + uri + "}id")
        if value is not None:
            return value
    return None


def source_for_rels(name):
    if name == "_rels/.rels":
        return ""
    parent, filename = posixpath.split(name)
    if posixpath.basename(parent) != "_rels" or not filename.endswith(".rels"):
        raise InspectionError("Invalid relationship part path: " + name)
    return posixpath.join(posixpath.dirname(parent), filename[:-5])


def resolve_target(source, target):
    if "\\" in target:
        raise InspectionError("Backslash in internal relationship target: " + target)
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.query:
        raise InspectionError("Invalid internal relationship URI: " + target)
    decoded = unquote(parsed.path)
    if "\\" in decoded or "\x00" in decoded or not decoded:
        raise InspectionError("Invalid internal relationship target: " + target)
    if decoded.startswith("/"):
        resolved = posixpath.normpath(decoded.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), decoded))
    if resolved == ".." or resolved.startswith("../") or resolved.startswith("/"):
        raise InspectionError("Relationship target escapes the package: " + target)
    return resolved


def xml_part(name, data, node_budget):
    # Reject declarations before parsing, including declarations encoded as UTF-16.
    declaration_scan = data.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in declaration_scan or b"<!ENTITY" in declaration_scan:
        raise InspectionError("DTD or entity declaration is unsupported: " + name)
    try:
        root = ET.fromstring(data)
    except (ET.ParseError, LookupError, ValueError) as exc:
        raise InspectionError("Invalid XML in " + name + ": " + str(exc)) from exc
    count = sum(1 for _ in root.iter())
    node_budget[0] += count
    if node_budget[0] > MAX_XML_NODES:
        raise InspectionError("XML node limit exceeded")
    return root


def read_package(path):
    """Read bounded package bytes. Never extract paths to the filesystem."""
    parts = {}
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_PARTS:
                raise InspectionError("Package part count limit exceeded")
            total = 0
            for entry in entries:
                name = entry.filename
                if (
                    "\\" in name or "\x00" in name or name.startswith("/")
                    or posixpath.normpath(name.rstrip("/")) != name.rstrip("/")
                    or name.startswith("../") or name.rstrip("/") in {"", ".", ".."}
                ):
                    raise InspectionError("Invalid package path: " + repr(name))
                if entry.is_dir():
                    continue
                if name in parts:
                    raise InspectionError("Duplicate package part: " + name)
                if entry.flag_bits & 1:
                    raise InspectionError("Encrypted ZIP entry is unsupported: " + name)
                if entry.file_size > MAX_PART_BYTES:
                    raise InspectionError("Package part byte limit exceeded: " + name)
                total += entry.file_size
                if total > MAX_TOTAL_BYTES:
                    raise InspectionError("Package total byte limit exceeded")
                with archive.open(entry) as stream:
                    data = stream.read(MAX_PART_BYTES + 1)
                if len(data) > MAX_PART_BYTES or len(data) != entry.file_size:
                    raise InspectionError("Invalid or oversized package part: " + name)
                parts[name] = data
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise InspectionError("Cannot read spreadsheet package: " + str(exc)) from exc
    return parts


def parse_relationships(parts, roots, errors):
    relationships = {}
    external = []
    for name in sorted(roots):
        if not name.endswith(".rels"):
            continue
        root = roots[name]
        if root.tag != "{" + PACKAGE_REL_NAMESPACE + "}Relationships":
            errors.append("Invalid relationship document root: " + name)
            continue
        try:
            source = source_for_rels(name)
        except InspectionError as exc:
            errors.append(str(exc))
            continue
        if source and source not in parts:
            errors.append("Missing relationship source part: " + source)
        by_id = {}
        for item in root:
            if item.tag != "{" + PACKAGE_REL_NAMESPACE + "}Relationship":
                errors.append("Invalid relationship element in " + name)
                continue
            rel_id, rel_type, target = item.get("Id"), item.get("Type"), item.get("Target")
            if not rel_id or not rel_type or not target:
                errors.append("Incomplete relationship in " + name)
                continue
            if rel_id in by_id:
                errors.append("Duplicate relationship ID in " + name + ": " + rel_id)
                continue
            mode = item.get("TargetMode", "Internal")
            record = {"id": rel_id, "type": rel_type, "target": target, "mode": mode}
            if mode == "External":
                external.append({"source": source, **record})
            elif mode == "Internal":
                try:
                    record["part"] = resolve_target(source, target)
                    if record["part"] not in parts:
                        errors.append("Missing relationship target: " + source + " -> " + record["part"])
                except InspectionError as exc:
                    errors.append(str(exc))
            else:
                errors.append("Invalid relationship TargetMode in " + name + ": " + mode)
            by_id[rel_id] = record
        relationships[source] = by_id
    return relationships, external


def content_types(parts, roots, errors):
    name = "[Content_Types].xml"
    root = roots.get(name)
    if root is None:
        errors.append("Missing or invalid [Content_Types].xml")
        return {}
    if root.tag != "{" + CONTENT_TYPE_NAMESPACE + "}Types":
        errors.append("Invalid content type document root")
        return {}
    defaults, overrides = {}, {}
    for item in root:
        kind = local_name(item.tag)
        content_type = item.get("ContentType")
        if namespace(item.tag) != CONTENT_TYPE_NAMESPACE or not content_type:
            errors.append("Invalid content type entry")
            continue
        if kind == "Default":
            ext = item.get("Extension", "").lower()
            if not ext or ext in defaults:
                errors.append("Missing or duplicate default content type extension")
            defaults[ext] = content_type
        elif kind == "Override":
            target = item.get("PartName", "")
            if not target.startswith("/"):
                errors.append("Content type override lacks an absolute part name")
                continue
            try:
                part = resolve_target("", target)
            except InspectionError as exc:
                errors.append(str(exc))
                continue
            if part in overrides:
                errors.append("Duplicate content type override: " + part)
            if part not in parts:
                errors.append("Content type override names a missing part: " + part)
            overrides[part] = content_type
        else:
            errors.append("Unknown content type declaration: " + kind)
    result = {}
    for part in parts:
        if part == name:
            continue
        value = overrides.get(part) or defaults.get(part.rsplit(".", 1)[-1].lower())
        if not value:
            errors.append("Missing content type for package part: " + part)
        result[part] = value
    return result


def valid_cell_ref(ref):
    match = CELL_REF.fullmatch(ref or "")
    if not match or int(match.group(2)) > 1048576:
        return False
    column = 0
    for letter in match.group(1):
        column = column * 26 + ord(letter) - ord("A") + 1
    return column <= 16384


def inspect_sheet(name, part, root, errors, total_cells):
    result = {
        "name": name, "part": part, "cell_count": 0, "formula_count": 0,
        "formulas": {}, "cached_errors": [], "formula_cache_missing_count": 0,
        "formula_cache_empty_count": 0, "features": {},
    }
    if local_name(root.tag) != "worksheet" or namespace(root.tag) not in SHEET_NAMESPACES:
        errors.append("Invalid worksheet root: " + part)
        return result
    dimension = child(root, "dimension")
    result["declared_dimension"] = dimension.get("ref") if dimension is not None else None
    seen = set()
    data = child(root, "sheetData")
    if data is None:
        errors.append("Missing sheetData in worksheet: " + part)
        return result
    for row in children(data, "row"):
        for cell in children(row, "c"):
            total_cells[0] += 1
            if total_cells[0] > MAX_CELLS:
                raise InspectionError("Worksheet cell limit exceeded")
            result["cell_count"] += 1
            ref = cell.get("r")
            if not valid_cell_ref(ref) or ref in seen:
                errors.append("Invalid or duplicate cell reference in " + part + ": " + str(ref))
                continue
            seen.add(ref)
            formula, value = child(cell, "f"), child(cell, "v")
            cache = {
                "present": value is not None,
                "value": value.text if value is not None else None,
                "type": cell.get("t", "n"),
            }
            if formula is not None:
                result["formulas"][ref] = {
                    "text": formula.text or "", "attributes": dict(sorted(formula.attrib.items())),
                    "cache": cache,
                }
                result["formula_count"] += 1
                if value is None:
                    result["formula_cache_missing_count"] += 1
                elif value.text is None or value.text == "":
                    result["formula_cache_empty_count"] += 1
            if cache["type"] == "e":
                result["cached_errors"].append({"cell": ref, "value": cache["value"], "formula": formula is not None})
    for feature in (
        "mergeCells", "dataValidations", "conditionalFormatting", "autoFilter",
        "tableParts", "drawing", "legacyDrawing", "sheetProtection", "extLst",
    ):
        matches = children(root, feature)
        if matches:
            result["features"][feature] = sum(len(item) or 1 for item in matches)
    return result


def classify_parts(parts, roots, types):
    """Name preservation risks without asserting any editing engine can round-trip them."""
    sensitive = {}
    known = re.compile(
        r"^(?:\[Content_Types\]\.xml|_rels/\.rels|docProps/(?:core|app|custom)\.xml|"
        r"xl/(?:workbook|styles|sharedStrings|calcChain)\.xml|"
        r"xl/(?:worksheets|chartsheets|dialogsheets)/[^/]+\.xml|"
        r"xl/(?:tables|charts|drawings|theme)/[^/]+\.xml|"
        r"xl/media/[^/]+|xl/printerSettings/[^/]+|"
        r"(?:.*/)?_rels/[^/]+\.rels|xl/comments[^/]*\.xml)$"
    )
    patterns = {
        "macros": ("vba", "macroenabled"),
        "pivots": ("pivot",),
        "slicers_or_timelines": ("slicer", "timeline"),
        "external_links": ("externallink",),
        "connections_or_queries": ("connection", "querytable", "powerquery"),
        "embedded_objects": ("embeddings/", "oleobject"),
        "controls_or_legacy_drawings": ("activex", "ctrlprops", ".vml", "customui"),
        "signatures": ("_xmlsignatures/", "signature"),
        "custom_xml": ("customxml/",),
        "data_model_or_rich_data": ("model/", "richdata/", "metadata.xml", "customdata/"),
        "threaded_comments": ("threadedcomment", "persons/"),
        "binary_workbook": ("workbook.bin", "sheet.binary"),
    }
    for name in sorted(parts):
        hint = name.lower() + " " + (types.get(name) or "").lower()
        for category, fragments in patterns.items():
            if any(fragment in hint for fragment in fragments):
                sensitive.setdefault(category, []).append(name)
        if not known.fullmatch(name):
            sensitive.setdefault("unknown_parts", []).append(name)
        root = roots.get(name)
        if root is not None and any(local_name(item.tag) == "extLst" for item in root.iter()):
            sensitive.setdefault("extension_metadata", []).append(name)
    return sensitive


def inspect_workbook(path):
    """Return a JSON-serializable inspection, including explicit incompleteness."""
    result = {
        "schema": "daodan/xlsx-inspection/v1", "path": str(Path(path).resolve()),
        "valid": False, "errors": [], "warnings": [], "parts": {}, "sheets": [],
        "tables": [], "chart_parts": [], "defined_names": [], "calculation_properties": {},
        "external_relationships": [], "preservation_sensitive": {},
        "cache_verification": "unverified: cached values do not establish recalculation",
    }
    errors = result["errors"]
    try:
        parts = read_package(path)
        result["parts"] = {
            name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(parts.items())
        }
        roots, node_budget = {}, [0]
        for name, data in sorted(parts.items()):
            if name.endswith((".xml", ".rels")):
                try:
                    roots[name] = xml_part(name, data, node_budget)
                except InspectionError as exc:
                    errors.append(str(exc))
        types = content_types(parts, roots, errors)
        relationships, external = parse_relationships(parts, roots, errors)
        result["external_relationships"] = external
        result["preservation_sensitive"] = classify_parts(parts, roots, types)
        main = [rel for rel in relationships.get("", {}).values() if rel["type"].endswith("/officeDocument")]
        if len(main) != 1 or main[0].get("mode") != "Internal" or not main[0].get("part"):
            errors.append("Package must have one internal officeDocument relationship")
        else:
            workbook_part = main[0]["part"]
            result["workbook_part"] = workbook_part
            workbook = roots.get(workbook_part)
            if workbook is None or local_name(workbook.tag) != "workbook" or namespace(workbook.tag) not in SHEET_NAMESPACES:
                errors.append("Missing or unsupported XML workbook: " + workbook_part)
            else:
                calc = child(workbook, "calcPr")
                result["calculation_properties"] = dict(sorted(calc.attrib.items())) if calc is not None else {}
                names = child(workbook, "definedNames")
                if names is not None:
                    result["defined_names"] = [
                        {"attributes": dict(sorted(item.attrib.items())), "text": item.text or ""}
                        for item in children(names, "definedName")
                    ]
                sheets = child(workbook, "sheets")
                if sheets is None or not children(sheets, "sheet"):
                    errors.append("Workbook has no sheets")
                else:
                    seen_names, total_cells = set(), [0]
                    for sheet in children(sheets, "sheet"):
                        name = sheet.get("name", "")
                        if not name or name in seen_names:
                            errors.append("Missing or duplicate workbook sheet name: " + name)
                        seen_names.add(name)
                        rel = relationships.get(workbook_part, {}).get(relation_id(sheet))
                        if rel is None or rel.get("mode") != "Internal" or not rel.get("part"):
                            errors.append("Missing internal sheet relationship: " + name)
                            continue
                        part = rel["part"]
                        if part not in roots:
                            errors.append("Missing or unsupported sheet XML: " + part)
                            continue
                        if rel["type"].endswith("/worksheet"):
                            record = inspect_sheet(name, part, roots[part], errors, total_cells)
                            record["state"] = sheet.get("state", "visible")
                            result["sheets"].append(record)
                        elif rel["type"].endswith("/chartsheet"):
                            result["sheets"].append({"name": name, "part": part, "kind": "chartsheet", "formulas": {}})
                        else:
                            errors.append("Unsupported sheet relationship type: " + rel["type"])
        for name, root in sorted(roots.items()):
            if local_name(root.tag) == "table" and namespace(root.tag) in SHEET_NAMESPACES:
                columns = child(root, "tableColumns")
                result["tables"].append({
                    "part": name, "name": root.get("name"), "display_name": root.get("displayName"),
                    "ref": root.get("ref"), "columns": [item.get("name") for item in children(columns, "tableColumn")] if columns is not None else [],
                })
            if local_name(root.tag) == "chartSpace":
                result["chart_parts"].append(name)
        styles = [name for name, root in roots.items() if local_name(root.tag) == "styleSheet"]
        result["style_parts"] = sorted(styles)
        formula_count = sum(sheet.get("formula_count", 0) for sheet in result["sheets"])
        result["formula_count"] = formula_count
        result["cached_error_count"] = sum(len(sheet.get("cached_errors", [])) for sheet in result["sheets"])
        if formula_count:
            result["warnings"].append("Formula caches may be absent or stale. Validate results with a compatible calculation engine.")
        if result["preservation_sensitive"]:
            result["warnings"].append("Preservation-sensitive features require an editing engine with demonstrated round-trip support.")
        if external:
            result["warnings"].append("External relationships were inventoried without contacting their targets.")
    except InspectionError as exc:
        errors.append(str(exc))
    result["valid"] = not errors
    return result


def compare_workbooks(before_path, after_path):
    before, after = inspect_workbook(before_path), inspect_workbook(after_path)
    before_parts, after_parts = before["parts"], after["parts"]
    before_sheets = {sheet["name"]: sheet for sheet in before["sheets"]}
    after_sheets = {sheet["name"]: sheet for sheet in after["sheets"]}
    formula_changes, cache_changes = [], []
    for name in sorted(set(before_sheets) | set(after_sheets)):
        old = before_sheets.get(name, {}).get("formulas", {})
        new = after_sheets.get(name, {}).get("formulas", {})
        for ref in sorted(set(old) | set(new)):
            old_formula = {key: value for key, value in old.get(ref, {}).items() if key != "cache"} if ref in old else None
            new_formula = {key: value for key, value in new.get(ref, {}).items() if key != "cache"} if ref in new else None
            if old_formula != new_formula:
                formula_changes.append({"sheet": name, "cell": ref, "before": old_formula, "after": new_formula})
            if ref in old and ref in new and old[ref]["cache"] != new[ref]["cache"]:
                cache_changes.append({"sheet": name, "cell": ref, "before": old[ref]["cache"], "after": new[ref]["cache"]})
    return {
        "schema": "daodan/xlsx-comparison/v1", "valid": before["valid"] and after["valid"],
        "notice": DELTA_NOTICE, "cache_verification": "unverified: cache changes do not prove recalculation",
        "before": before, "after": after,
        "removed_parts": sorted(set(before_parts) - set(after_parts)),
        "added_parts": sorted(set(after_parts) - set(before_parts)),
        "changed_parts": sorted(name for name in set(before_parts) & set(after_parts) if before_parts[name]["sha256"] != after_parts[name]["sha256"]),
        "removed_sheets": sorted(set(before_sheets) - set(after_sheets)),
        "added_sheets": sorted(set(after_sheets) - set(before_sheets)),
        "removed_chart_parts": sorted(set(before["chart_parts"]) - set(after["chart_parts"])),
        "formula_changes": formula_changes, "cache_changes": cache_changes,
        "defined_names_changed": before["defined_names"] != after["defined_names"],
        "tables_changed": before["tables"] != after["tables"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_parser = commands.add_parser("inspect", help="Inspect an .xlsx or XML-based .xlsm package")
    inspect_parser.add_argument("workbook", type=Path)
    compare_parser = commands.add_parser("compare", help="Report before/after package and formula deltas")
    compare_parser.add_argument("before", type=Path)
    compare_parser.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    result = inspect_workbook(args.workbook) if args.command == "inspect" else compare_workbooks(args.before, args.after)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
