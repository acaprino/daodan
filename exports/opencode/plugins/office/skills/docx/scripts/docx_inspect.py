#!/usr/bin/env python3
"""Inspect and compare Word packages without editing, executing or rendering them.

Native structures and hashes reveal preservation deltas. They do not establish
authorized edits, Word field updates, semantic completeness or layout fidelity.
"""

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


_PACKAGE_SCRIPT = Path(__file__).resolve().parents[2] / "xlsx/scripts/xlsx_inspect.py"
_SPEC = importlib.util.spec_from_file_location("office_package_reader", _PACKAGE_SCRIPT)
package = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(package)
WORD_NAMESPACES = {
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://purl.oclc.org/ooxml/wordprocessingml/main",
}
MATH_NAMESPACES = {
    "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://purl.oclc.org/ooxml/officeDocument/math",
}
MAIN_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    "application/vnd.ms-word.document.macroEnabled.main+xml",
}
STORY_ROOTS = {"document", "hdr", "ftr", "footnotes", "endnotes", "comments", "glossaryDocument"}
STORY_RELATIONS = {"header": "hdr", "footer": "ftr", "footnotes": "footnotes", "endnotes": "endnotes", "comments": "comments"}
REVISION_TAGS = {"ins", "del", "moveFrom", "moveTo", "pPrChange", "rPrChange", "tblPrChange", "trPrChange", "tcPrChange", "sectPrChange", "numberingChange", "cellIns", "cellDel", "cellMerge"}
DELTA_NOTICE = "Observed deltas require review against authorized edits. Structural validity and unchanged text do not establish semantic preservation or layout fidelity."


def word(element, name=None):
    return package.namespace(element.tag) in WORD_NAMESPACES and (name is None or package.local_name(element.tag) == name)


def descendants(element, name):
    return [item for item in element.iter() if word(item, name)]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(element):
    return digest(ET.tostring(element, encoding="utf-8"))


def native_text(element):
    substitutions = {"tab": "\t", "br": "\n", "cr": "\n", "noBreakHyphen": "\u2011", "softHyphen": "\u00ad"}
    return "".join((item.text or "") if package.local_name(item.tag) in {"t", "delText"} else substitutions.get(package.local_name(item.tag), "") for item in element.iter() if word(item))


def record(element):
    return {"kind": package.local_name(element.tag), "attributes": dict(sorted(element.attrib.items())), "sha256": fingerprint(element)}


def inspect_story(part, root):
    paragraphs = []
    for paragraph in descendants(root, "p"):
        formatting = [record(item) for item in paragraph if word(item, "pPr")]
        formatting.extend({"run_attributes": dict(sorted(run.attrib.items())), "properties": [record(item) for item in run if word(item, "rPr")]} for run in descendants(paragraph, "r"))
        paragraphs.append({"text": native_text(paragraph), "native_sha256": fingerprint(paragraph), "formatting_sha256": digest(json.dumps(formatting, sort_keys=True).encode("utf-8"))})
    tables = []
    for table in descendants(root, "tbl"):
        rows = [item for item in table if word(item, "tr")]
        tables.append({"rows": len(rows), "cells_per_row": [len([item for item in row if word(item, "tc")]) for row in rows], "text": native_text(table), "sha256": fingerprint(table)})
    fields = []
    for item in root.iter():
        if word(item) and package.local_name(item.tag) in {"fldSimple", "fldChar", "instrText", "delInstrText"}:
            fields.append({**record(item), "instruction_text": item.text or ""})
    sections = [{**record(section), "properties": [{"kind": package.local_name(item.tag), "attributes": dict(sorted(item.attrib.items()))} for item in section if word(item)]} for section in descendants(root, "sectPr")]
    return {
        "part": part, "kind": package.local_name(root.tag), "paragraphs": paragraphs,
        "tables": tables, "sections": sections, "fields": fields,
        "revisions": [record(item) for item in root.iter() if word(item) and package.local_name(item.tag) in REVISION_TAGS],
        "comments": [record(item) for item in root.iter() if word(item) and package.local_name(item.tag) in {"comment", "commentRangeStart", "commentRangeEnd", "commentReference"}],
        "math": [record(item) for item in root.iter() if package.namespace(item.tag) in MATH_NAMESPACES and package.local_name(item.tag) == "oMath"],
        "content_controls": [record(item) for item in descendants(root, "sdt")],
        "hyperlinks": [record(item) for item in descendants(root, "hyperlink")],
        "imported_content": [record(item) for item in descendants(root, "altChunk")],
    }


def inspect_document(path):
    result = {
        "schema": "daodan/docx-inspection/v1", "path": str(Path(path).resolve()),
        "valid": False, "errors": [], "warnings": [], "parts": {}, "stories": [],
        "styles": [], "object_relationships": [], "external_relationships": [],
        "metadata_parts": [], "preservation_sensitive": {},
        "field_verification": "unverified: instructions and stored results are not updated",
        "layout_verification": "unverified: no pages were rendered",
    }
    errors, sensitive = result["errors"], result["preservation_sensitive"]
    try:
        parts = package.read_package(path)
        result["parts"] = {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(parts.items())}
        roots, budget = {}, [0]
        for name, data in sorted(parts.items()):
            if name.endswith((".xml", ".rels")):
                try:
                    roots[name] = package.xml_part(name, data, budget)
                except package.InspectionError as exc:
                    errors.append(str(exc))
        types = package.content_types(parts, roots, errors)
        relations, external = package.parse_relationships(parts, roots, errors)
        result["external_relationships"] = external
        allowed = {uri + "/officeDocument" for uri in package.REL_NAMESPACES}
        main = [rel for rel in relations.get("", {}).values() if rel["type"] in allowed]
        if len(main) != 1 or main[0].get("mode") != "Internal" or not main[0].get("part"):
            errors.append("Package must have one internal Word officeDocument relationship")
        else:
            part = main[0]["part"]
            result["document_part"], result["main_content_type"] = part, types.get(part)
            root = roots.get(part)
            if root is None or not word(root, "document"):
                errors.append("Missing or unsupported Word document root: " + part)
            elif not any(word(item, "body") and package.namespace(item.tag) == package.namespace(root.tag) for item in root):
                errors.append("Missing Word document body: " + part)
            if types.get(part) not in MAIN_TYPES:
                errors.append("Unsupported Word main content type: " + str(types.get(part)))
        for source in sorted(set(relations) | set(roots)):
            entries = relations.get(source, {})
            for rel in entries.values():
                kind = rel["type"].rsplit("/", 1)[-1]
                if kind in STORY_RELATIONS and rel["type"] in {uri + "/" + kind for uri in package.REL_NAMESPACES}:
                    target = roots.get(rel.get("part"))
                    if rel.get("mode") != "Internal" or target is None or not word(target, STORY_RELATIONS[kind]):
                        errors.append("Invalid Word story relationship: " + source + " -> " + rel["target"])
                if kind in {"image", "chart", "oleObject", "package", "aFChunk", "control"}:
                    result["object_relationships"].append({"source": source, **rel})
            source_root = roots.get(source)
            if source_root is not None:
                for item in source_root.iter():
                    if word(item) and package.local_name(item.tag) in {"headerReference", "footerReference", "altChunk"}:
                        rel = entries.get(package.relation_id(item))
                        expected = {"headerReference": "header", "footerReference": "footer", "altChunk": "aFChunk"}[package.local_name(item.tag)]
                        if rel is None or rel["type"] not in {uri + "/" + expected for uri in package.REL_NAMESPACES}:
                            errors.append("Missing or incorrect Word reference relationship: " + source)
        for name, root in sorted(roots.items()):
            if word(root) and package.local_name(root.tag) in STORY_ROOTS:
                result["stories"].append(inspect_story(name, root))
            if word(root, "styles"):
                result["styles"].append({"part": name, "definitions": [record(item) for item in root if word(item, "style")], "sha256": fingerprint(root)})
        patterns = {"macros": ("vba", "macroenabled"), "embedded_objects": ("embeddings/", "oleobject"), "controls_or_legacy_drawings": ("activex", "ctrlprops", ".vml", "customui"), "signatures": ("_xmlsignatures/", "signature"), "custom_xml": ("customxml/",), "extension_metadata": ("commentsextended", "commentsids", "people.xml"), "imported_content": ("afchunk", "altchunk")}
        known = re.compile(r"^(?:\[Content_Types\]\.xml|_rels/\.rels|(?:.*/)?_rels/[^/]+\.rels|docProps/(?:core|app|custom)\.xml|word/(?:document|header[0-9]*|footer[0-9]*|footnotes|endnotes|comments|styles|stylesWithEffects|settings|fontTable|numbering|webSettings)\.xml|word/(?:theme|charts|drawings|glossary)/[^/]+\.xml|word/(?:media|printerSettings)/[^/]+)$")
        for name in sorted(parts):
            hint = name.lower() + " " + (types.get(name) or "").lower()
            for category, fragments in patterns.items():
                if any(fragment in hint for fragment in fragments):
                    sensitive.setdefault(category, []).append(name)
            if name.startswith("docProps/"):
                result["metadata_parts"].append(name)
                sensitive.setdefault("document_metadata", []).append(name)
            if not known.fullmatch(name):
                sensitive.setdefault("unknown_parts", []).append(name)
        for story in result["stories"]:
            for feature in ("fields", "revisions", "comments", "math", "content_controls", "hyperlinks", "imported_content"):
                if story[feature]:
                    sensitive.setdefault(feature, []).append(story["part"])
            if story["kind"] in {"footnotes", "endnotes"}:
                sensitive.setdefault("footnotes_or_endnotes", []).append(story["part"])
        if external:
            sensitive["external_relationships"] = sorted({item["source"] for item in external})
            result["warnings"].append("External relationship targets were inventoried without contacting them.")
        if sensitive:
            result["warnings"].append("Preservation-sensitive features require demonstrated round-trip support and explicit review of deltas.")
    except (package.InspectionError, RecursionError) as exc:
        errors.append(str(exc))
    result["valid"] = not errors
    return result


def compare_documents(before_path, after_path):
    before, after = inspect_document(before_path), inspect_document(after_path)
    old_parts, new_parts = before["parts"], after["parts"]
    old_stories, new_stories = ({story["part"]: story for story in item["stories"]} for item in (before, after))
    changes = {"text_changes": [], "formatting_changes": [], "native_paragraph_changes": []}
    for name in sorted(set(old_stories) | set(new_stories)):
        old, new = old_stories.get(name, {}).get("paragraphs", []), new_stories.get(name, {}).get("paragraphs", [])
        for index in range(max(len(old), len(new))):
            a, b = old[index] if index < len(old) else None, new[index] if index < len(new) else None
            for key, field in (("text_changes", "text"), ("formatting_changes", "formatting_sha256"), ("native_paragraph_changes", "native_sha256")):
                previous, current = a.get(field) if a else None, b.get(field) if b else None
                if previous != current:
                    changes[key].append({"part": name, "paragraph_index": index, "before": previous, "after": current})
    feature_changes = {feature + "_changed_parts": [name for name in sorted(set(old_stories) | set(new_stories)) if old_stories.get(name, {}).get(feature, []) != new_stories.get(name, {}).get(feature, [])] for feature in ("tables", "sections", "fields", "revisions", "comments", "math", "content_controls", "hyperlinks", "imported_content")}
    object_parts = {item["part"] for inspection in (before, after) for item in inspection["object_relationships"] if "part" in item}
    object_part_changes = [name for name in sorted(object_parts) if old_parts.get(name) != new_parts.get(name)]
    return {
        "schema": "daodan/docx-comparison/v1", "valid": before["valid"] and after["valid"],
        "notice": DELTA_NOTICE, "before": before, "after": after,
        "paragraph_matching": "positional per story; insertions can shift later comparisons",
        "removed_parts": sorted(set(old_parts) - set(new_parts)), "added_parts": sorted(set(new_parts) - set(old_parts)),
        "changed_parts": sorted(name for name in set(old_parts) & set(new_parts) if old_parts[name]["sha256"] != new_parts[name]["sha256"]),
        "removed_story_parts": sorted(set(old_stories) - set(new_stories)), "added_story_parts": sorted(set(new_stories) - set(old_stories)),
        "styles_changed": before["styles"] != after["styles"], "objects_changed": bool(object_part_changes) or before["object_relationships"] != after["object_relationships"],
        "object_part_changes": object_part_changes,
        "external_relationships_changed": before["external_relationships"] != after["external_relationships"],
        **changes, **feature_changes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_parser = commands.add_parser("inspect", help="Inspect a DOCX or XML-based DOCM package")
    inspect_parser.add_argument("document", type=Path)
    compare_parser = commands.add_parser("compare", help="Report native content and package deltas")
    compare_parser.add_argument("before", type=Path)
    compare_parser.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    result = inspect_document(args.document) if args.command == "inspect" else compare_documents(args.before, args.after)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
