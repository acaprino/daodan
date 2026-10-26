#!/usr/bin/env python3
"""Inspect and compare Word packages without editing, executing or rendering them.

Native structures and hashes reveal preservation deltas. They do not establish
authorized edits, Word field updates, semantic completeness or layout fidelity.
"""

import argparse
import difflib
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter
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
    "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml",
    "application/vnd.ms-word.document.macroEnabled.main+xml",
}
STORY_ROOTS = {"document", "hdr", "ftr", "footnotes", "endnotes", "comments", "glossaryDocument"}
STORY_RELATIONS = {"header": "hdr", "footer": "ftr", "footnotes": "footnotes", "endnotes": "endnotes", "comments": "comments"}
REVISION_TAGS = {"ins", "del", "moveFrom", "moveTo", "pPrChange", "rPrChange", "tblPrChange", "trPrChange", "tcPrChange", "sectPrChange", "numberingChange", "cellIns", "cellDel", "cellMerge"}
DELTA_NOTICE = "Observed deltas require review against authorized edits. Structural validity and unchanged text do not establish semantic preservation or layout fidelity."
# Shared bound on closest-match and added-text comparisons, so hostile documents stay linear in time.
MAX_TEXT_COMPARISONS = 5_000_000
COVERAGE_NOTICE = (
    "Structural text evidence only, not a visual or fidelity verdict. Source paragraphs and table "
    "cells of the body, headers, footers, footnotes, endnotes and comments are matched "
    "position-independently after NFKC and whitespace normalization, without case folding: an item "
    "is present when its text occurs anywhere in the candidate text of the same group (body with "
    "body, notes with notes, furniture with furniture). Presence does not prove meaning, order, "
    "emphasis or rendering. Similarity ratios for missing items are hints and never count as "
    "present. Field results, tracked deletions and generated numbering are not text items.")


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


def normalize_text(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def visible_text(element):
    """Paragraph text as a reader sees it: no tracked deletions, no field instructions."""
    parts = []
    for item in element.iter():
        if not word(item):
            continue
        name = package.local_name(item.tag)
        if name == "t":
            parts.append(item.text or "")
        elif name in {"tab", "br", "cr"}:
            parts.append(" ")
    return normalize_text("".join(parts))


def _text_without_deletions(element):
    """A copy-free walk that skips w:del subtrees and instrText, so deleted text is not an item."""
    skip = {"del", "moveFrom", "instrText", "delInstrText", "delText"}
    stack, parts = [element], []
    while stack:
        node = stack.pop()
        name = package.local_name(node.tag) if word(node) else None
        if name in skip:
            continue
        if name == "t":
            parts.append(node.text or "")
        elif name in {"tab", "br", "cr"}:
            parts.append(" ")
        stack.extend(reversed(list(node)))
    return normalize_text("".join(parts))


def is_heading(paragraph):
    for properties in (item for item in paragraph if word(item, "pPr")):
        for item in properties:
            if word(item, "outlineLvl"):
                return True
            if word(item, "pStyle"):
                style = next((value for key, value in item.attrib.items() if package.local_name(key) == "val"), "")
                if re.match(r"(?i)^(heading|title|titolo|überschrift|titre|t[ií]tulo)", style):
                    return True
    return False


def coverage_items(inspection, roots, label):
    """Every visible text item of a document: paragraphs outside tables and table cells, per story."""
    items = []
    for story in inspection["stories"]:
        root = roots.get(story["part"])
        if root is None:
            continue
        kind = story["kind"]
        group = "body" if kind in {"document", "glossaryDocument"} else "notes" if kind in {"footnotes", "endnotes", "comments"} else "furniture"
        section = None
        in_table = set()
        for table in descendants(root, "tbl"):
            for cell in descendants(table, "tc"):
                for paragraph in descendants(cell, "p"):
                    in_table.add(id(paragraph))
        for element in root.iter():
            if word(element, "tc"):
                text = _text_without_deletions(element)
                if text:
                    items.append({"part": story["part"], "group": group, "kind": "cell", "section": section, "text": text})
                continue
            if not word(element, "p") or id(element) in in_table:
                continue
            paragraph = element
            text = _text_without_deletions(paragraph)
            if not text:
                continue
            if is_heading(paragraph):
                section = text
            items.append({"part": story["part"], "group": group, "kind": "heading" if is_heading(paragraph) else "paragraph",
                          "section": section, "text": text})
    return items


def read_cuts(path, errors):
    """Return validated cut entries. A malformed file adds errors and applies no cut."""
    try:
        with open(path, "rb") as stream:
            data = stream.read(package.MAX_PART_BYTES + 1)
        if len(data) > package.MAX_PART_BYTES:
            raise ValueError("file exceeds the byte limit")
        entries = json.loads(data.decode("utf-8-sig"))
    except (OSError, ValueError, RecursionError) as exc:
        errors.append("Invalid cuts file: " + str(exc))
        return []
    problems, cuts = [], []
    if not isinstance(entries, list):
        problems.append("expected a JSON list of cut entries")
        entries = []
    for index, entry in enumerate(entries):
        where = f"cuts[{index}]: "
        if not isinstance(entry, dict):
            problems.append(where + "expected an object")
            continue
        unknown = sorted(set(entry) - {"text", "section", "reason"})
        if unknown:
            problems.append(where + "unknown fields: " + ", ".join(unknown))
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            problems.append(where + "reason must be a non-empty string")
        if ("text" in entry) == ("section" in entry):
            problems.append(where + "give exactly one of text or section")
            continue
        key = "text" if "text" in entry else "section"
        value = entry.get(key)
        if not isinstance(value, str) or not normalize_text(value):
            problems.append(where + f"{key} must be a non-empty string")
            continue
        cuts.append({"index": index, key: normalize_text(value), "reason": reason})
    if problems:
        errors.extend("Invalid cuts file: " + problem for problem in problems)
        return []
    return cuts


def closest_text(text, pool, budget):
    """Best difflib ratio in the pool, or (None, None) once the comparison budget runs out."""
    matcher = difflib.SequenceMatcher(None)
    matcher.set_seq2(text)
    best, ratio = None, 0.0
    for candidate in pool:
        if budget[0] >= MAX_TEXT_COMPARISONS:
            budget[1] = True
            return None, None
        budget[0] += 1
        matcher.set_seq1(candidate)
        if matcher.real_quick_ratio() > ratio and matcher.quick_ratio() > ratio:
            value = matcher.ratio()
            if value > ratio:
                best, ratio = candidate, value
    return best, round(ratio, 3)


def derived_from_source(text, haystack, sources, budget):
    """True when the text occurs in the source, or is source texts merged with punctuation only."""
    if text in haystack:
        return True
    remainder = text
    for source in sources:
        if budget[0] >= MAX_TEXT_COMPARISONS:
            budget[1] = True
            return False
        budget[0] += 1
        if source in remainder:
            remainder = remainder.replace(source, "\n")
    return not any(character.isalnum() for character in remainder)


def _read_with_roots(path):
    inspection = inspect_document(path)
    roots = {}
    if inspection["valid"] or inspection["parts"]:
        try:
            parts = package.read_package(path)
            budget = [0]
            for name, data in parts.items():
                if name.endswith(".xml"):
                    try:
                        roots[name] = package.xml_part(name, data, budget)
                    except package.InspectionError:
                        pass
        except (package.InspectionError, RecursionError):
            pass
    return inspection, roots


def check_coverage(source_path, candidate_path, cuts_path=None):
    source, source_roots = _read_with_roots(source_path)
    candidate, candidate_roots = _read_with_roots(candidate_path)
    errors = (["source: " + error for error in source["errors"]]
              + ["candidate: " + error for error in candidate["errors"]])
    cuts = [] if cuts_path is None else read_cuts(cuts_path, errors)
    source_items = coverage_items(source, source_roots, "source")
    candidate_items = coverage_items(candidate, candidate_roots, "candidate")

    pools = {"body": [], "notes": [], "furniture": []}
    for item in candidate_items:
        pools[item["group"]].append(item["text"])
    haystacks = {name: "\n".join(texts) for name, texts in pools.items()}
    unique_pools = {name: list(dict.fromkeys(texts)) for name, texts in pools.items()}
    budget = [0, False]
    for item in source_items:
        covering = [cut["index"] for cut in cuts
                    if cut.get("text") == item["text"]
                    or ("section" in cut and item["section"] == cut["section"])]
        if covering:
            item["cuts"] = covering
        if item["text"] in haystacks[item["group"]]:
            item["status"] = "cut-but-present" if covering else "present"
        elif covering:
            item["status"] = "cut"
        else:
            item["status"] = "missing"
            item["closest"], item["similarity"] = closest_text(item["text"], unique_pools[item["group"]], budget)
    for cut in cuts:
        covered = [item for item in source_items if cut["index"] in item.get("cuts", ())]
        present = sum(item["status"] == "cut-but-present" for item in covered)
        if not covered:
            still_present = "text" in cut and any(cut["text"] in haystack for haystack in haystacks.values())
        else:
            still_present = present > 0 if "text" in cut else present == len(covered)
        cut["status"] = "cut-but-present" if still_present else "applied" if covered else "unmatched"
        cut["covered_items"], cut["present_items"] = len(covered), present

    sources = {"body": [], "notes": [], "furniture": []}
    for item in source_items:
        sources[item["group"]].append(item["text"])
    source_haystacks = {name: "\n".join(texts) for name, texts in sources.items()}
    longest_first = {name: sorted(set(texts), key=len, reverse=True) for name, texts in sources.items()}
    added = [{"part": item["part"], "kind": item["kind"], "text": item["text"]} for item in candidate_items
             if not derived_from_source(item["text"], source_haystacks[item["group"]], longest_first[item["group"]], budget)]
    counts = Counter(item["status"] for item in source_items)
    valid = not errors
    return {"schema": "daodan/docx-coverage/v1", "valid": valid, "errors": errors,
            "complete": valid and counts["missing"] == 0,
            "notice": COVERAGE_NOTICE,
            "summary": {"source_items": len(source_items), "present": counts["present"],
                        "cut": counts["cut"], "cut_but_present": counts["cut-but-present"],
                        "unexpected_missing": counts["missing"], "added": len(added)},
            "source": {"path": source["path"], "valid": source["valid"], "stories": len(source["stories"])},
            "candidate": {"path": candidate["path"], "valid": candidate["valid"], "stories": len(candidate["stories"])},
            "cuts_file": None if cuts_path is None else str(Path(cuts_path).resolve()),
            "cuts": cuts, "items": source_items, "added": added,
            "comparison_budget_exhausted": budget[1]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_parser = commands.add_parser("inspect", help="Inspect a DOCX or XML-based DOCM package")
    inspect_parser.add_argument("document", type=Path)
    compare_parser = commands.add_parser("compare", help="Report native content and package deltas")
    compare_parser.add_argument("before", type=Path)
    compare_parser.add_argument("after", type=Path)
    coverage_help = ("Check that every source text item (paragraphs, table cells, headers, footers, "
                     "notes, comments) reached the candidate document, except approved cuts. "
                     "Structural text evidence only, not a visual or fidelity verdict.")
    coverage_parser = commands.add_parser("coverage", help=coverage_help, description=coverage_help)
    coverage_parser.add_argument("source", type=Path)
    coverage_parser.add_argument("candidate", type=Path)
    coverage_parser.add_argument("--cuts", type=Path, help=(
        'JSON list of approved cuts, each {"text": "...", "reason": "..."} (a source item with exactly '
        'that normalized text) or {"section": "<heading text>", "reason": "..."} (every item from that '
        'heading to the next heading)'))
    args = parser.parse_args(argv)
    if args.command == "inspect":
        result = inspect_document(args.document)
    elif args.command == "compare":
        result = compare_documents(args.before, args.after)
    else:
        result = check_coverage(args.source, args.candidate, args.cuts)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
