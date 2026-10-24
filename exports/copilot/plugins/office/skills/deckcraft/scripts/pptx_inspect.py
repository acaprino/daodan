"""Read, compare and check text coverage of PPTX packages independently of the presentation engine.

Reuse Office's bounded ZIP/XML reader. Never extract packages, fetch links or
render slides. Deltas and coverage are evidence to review, not an automatic
fidelity verdict.
"""

import argparse
from collections import Counter
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unicodedata


_READER = Path(__file__).resolve().parents[2] / "xlsx/scripts/xlsx_inspect.py"
_SPEC = importlib.util.spec_from_file_location("office_pptx_package_reader", _READER)
package = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(package)
PRESENTATION_NS = {"http://schemas.openxmlformats.org/presentationml/2006/main",
                   "http://purl.oclc.org/ooxml/presentationml/main"}
DRAWING_NS = {"http://schemas.openxmlformats.org/drawingml/2006/main",
             "http://purl.oclc.org/ooxml/drawingml/main"}
MAIN_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
CHART_NS = {"http://schemas.openxmlformats.org/drawingml/2006/chart",
            "http://purl.oclc.org/ooxml/drawingml/chart"}
MC_NS = {"http://schemas.openxmlformats.org/markup-compatibility/2006"}
# Slide relationships whose text this checker does not read; reported, never silently dropped.
UNREAD_TEXT_PARTS = {"chartEx": "chartEx chart text is not read",
                     "diagramData": "SmartArt diagram text is not read"}
# Shared bound on closest-match and added-text comparisons, so hostile decks stay linear in time.
MAX_TEXT_COMPARISONS = 5_000_000
COVERAGE_NOTICE = (
    "Structural text evidence only, not a visual or fidelity verdict. Source paragraphs, table "
    "cells, chart text (titles, axis titles, category labels, series names) and speaker notes are "
    "matched position-independently after NFKC and whitespace normalization, without case folding: "
    "an item is present when its text occurs anywhere in the candidate text of the same group "
    "(notes against notes, everything else against all slide text). Presence does not prove "
    "meaning, order, emphasis or rendering. Similarity ratios for missing items are hints and never "
    "count as present. Generated slide-number and date fields are not text items.")


def matches(element, local, namespaces=PRESENTATION_NS):
    return package.namespace(element.tag) in namespaces and package.local_name(element.tag) == local


def text_runs(root):
    return [element.text or "" for element in root.iter() if matches(element, "t", DRAWING_NS)]


def inspect_presentation(path):
    return read_presentation(path)[0]


def read_presentation(path):
    """Return the inspection result and the parsed XML roots it was built from."""
    result = {"schema": "daodan/pptx-inspection/v1", "path": str(Path(path).resolve()),
              "valid": False, "errors": [], "parts": {}, "slides": [],
              "external_relationships": [], "features": {}, "payload_hashes": [],
              "visual_review": "unverified: no rendering performed"}
    errors = result["errors"]
    roots, budget = {}, [0]
    try:
        parts = package.read_package(path)
        result["parts"] = {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                           for name, data in sorted(parts.items())}
        for name, data in parts.items():
            if name.endswith((".xml", ".rels")):
                try:
                    roots[name] = package.xml_part(name, data, budget)
                except package.InspectionError as exc:
                    errors.append(str(exc))
        types = package.content_types(parts, roots, errors)
        relationships, external = package.parse_relationships(parts, roots, errors)
        result["external_relationships"] = external
        office_types = {uri + "/officeDocument" for uri in package.REL_NAMESPACES}
        mains = [item for item in relationships.get("", {}).values() if item["type"] in office_types]
        if len(mains) != 1 or mains[0].get("mode") != "Internal":
            raise package.InspectionError("Expected one internal presentation officeDocument relationship")
        main = mains[0].get("part")
        root = roots.get(main)
        if root is None or not matches(root, "presentation") or types.get(main) != MAIN_TYPE:
            raise package.InspectionError("Expected a PPTX presentation root and content type; macro and template variants are not supported")
        slide_list = next((item for item in root if matches(item, "sldIdLst")), None)
        size = next((item for item in root if matches(item, "sldSz")), None)
        result["canvas"] = dict(size.attrib) if size is not None else None
        seen_ids = set()
        for entry in [] if slide_list is None else slide_list:
            if not matches(entry, "sldId"):
                errors.append("Unexpected element in slide order")
                continue
            if entry.get("id") in seen_ids:
                errors.append("Duplicate slide ID: " + str(entry.get("id")))
            seen_ids.add(entry.get("id"))
            rel = relationships.get(main, {}).get(package.relation_id(entry), {})
            target = rel.get("part")
            slide = roots.get(target)
            if (rel.get("type") not in {uri + "/slide" for uri in package.REL_NAMESPACES}
                    or slide is None or not matches(slide, "sld")):
                errors.append("Missing or invalid ordered slide relationship")
                continue
            counts = Counter(package.local_name(item.tag) for item in slide.iter()
                             if package.namespace(item.tag) in PRESENTATION_NS | DRAWING_NS)
            related = list(relationships.get(target, {}).values())
            notes = [text_runs(roots[item["part"]]) for item in related
                     if item["type"].endswith("/notesSlide") and item.get("part") in roots]
            result["slides"].append({"id": entry.get("id"), "part": target,
                                     "hidden": slide.get("show", "1") in {"0", "false"},
                                     "text": text_runs(slide), "notes": notes,
                                     "objects": {name: counts[name] for name in ("sp", "pic", "graphicFrame", "cxnSp", "tbl")},
                                     "relationships": related})
        # Inspect relationship-bearing attributes as well as relationship targets.
        for name, document in roots.items():
            for element in document.iter():
                for attribute, value in element.attrib.items():
                    if package.namespace(attribute) in package.REL_NAMESPACES and value not in relationships.get(name, {}):
                        errors.append(f"Missing referenced relationship: {name} -> {value}")
        feature_fragments = {"charts": "chart", "notes": "notesSlide", "comments": "comment",
                             "masters": "slideMaster", "layouts": "slideLayout", "themes": "theme",
                             "smartart": "diagram", "embedded_objects": "oleObject",
                             "fonts": "font"}
        for category, fragment in feature_fragments.items():
            result["features"][category] = sorted(name for name, content_type in types.items()
                                                if fragment.lower() in (content_type or "").lower())
        result["features"]["media"] = sorted(name for name, content_type in types.items()
                                              if (content_type or "").lower().startswith(("image/", "audio/", "video/")))
        result["features"]["embedded_packages"] = sorted(name for name in parts
                                                          if "/embeddings/" in name)
        # Binary payloads survive renamed ZIP parts only when their bytes survive.
        result["payload_hashes"] = sorted(result["parts"][name]["sha256"] for name in parts
                                           if not name.endswith((".xml", ".rels")))
        result["features"]["animation_slides"] = [name for name, document in roots.items()
                                                   if any(matches(item, "timing") for item in document.iter())]
    except (package.InspectionError, RecursionError) as exc:
        errors.append(str(exc))
    result["valid"] = not errors
    return result, roots


def compare_presentations(before_path, after_path):
    before, after = inspect_presentation(before_path), inspect_presentation(after_path)
    a, b = before["parts"], after["parts"]
    deltas = []
    for index in range(max(len(before["slides"]), len(after["slides"]))):
        old = before["slides"][index] if index < len(before["slides"]) else {}
        new = after["slides"][index] if index < len(after["slides"]) else {}
        fields = [field for field in ("text", "notes", "hidden", "objects") if old.get(field) != new.get(field)]
        if fields:
            deltas.append({"slide_index": index, "changed_fields": fields, "before": old, "after": new})
    return {"schema": "daodan/pptx-comparison/v1", "valid": before["valid"] and after["valid"],
            "notice": "Deltas require review against authorized edits. Matching inventories do not prove semantic or visual fidelity. Slides are matched by position; reordering shifts comparisons.",
            "before": before, "after": after, "slide_changes": deltas,
            "canvas_changed": before.get("canvas") != after.get("canvas"),
            "removed_parts": sorted(set(a) - set(b)), "added_parts": sorted(set(b) - set(a)),
            "changed_parts": sorted(name for name in set(a) & set(b) if a[name] != b[name]),
            "removed_payload_hashes": list((Counter(before["payload_hashes"]) - Counter(after["payload_hashes"])).elements()),
            "external_relationships_changed": before["external_relationships"] != after["external_relationships"],
            "feature_counts_changed": {key: [len(before["features"].get(key, [])), len(after["features"].get(key, []))]
                                       for key in sorted(set(before["features"]) | set(after["features"]))
                                       if len(before["features"].get(key, [])) != len(after["features"].get(key, []))}}


def normalize_text(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def first_child(element, local, namespaces):
    return next((item for item in element if matches(item, local, namespaces)), None)


def paragraph_text(paragraph):
    pieces = []
    for item in paragraph:
        if matches(item, "AlternateContent", MC_NS):
            item = next(iter(item), item)  # One branch only; Choice and Fallback repeat content.
        if matches(item, "br", DRAWING_NS):
            pieces.append(" ")
        elif not (matches(item, "fld", DRAWING_NS)
                  and (item.get("type") or "").startswith(("slidenum", "datetime"))):
            pieces.extend(text_runs(item))
    return "".join(pieces)


def drawing_texts(root):
    """Yield (kind, raw text) for paragraphs and table cells in document order, groups included."""
    stack = [root]
    while stack:
        element = stack.pop()
        if matches(element, "tbl", DRAWING_NS):
            for cell in element.iter():
                if matches(cell, "tc", DRAWING_NS):
                    yield "table-cell", " ".join(paragraph_text(item) for item in cell.iter()
                                                 if matches(item, "p", DRAWING_NS))
        elif matches(element, "p", DRAWING_NS):
            yield "paragraph", paragraph_text(element)
        else:
            branch = list(element)[:1] if matches(element, "AlternateContent", MC_NS) else list(element)
            stack.extend(reversed(branch))


def chart_label(tx):
    if tx is None:
        return ""
    return " ".join([paragraph_text(item) for item in tx.iter() if matches(item, "p", DRAWING_NS)]
                    + [item.text or "" for item in tx.iter() if matches(item, "v", CHART_NS)])


def chart_texts(root):
    """Chart and axis titles, series names and category labels; never formulas or values."""
    texts = []
    for element in root.iter():
        if matches(element, "title", CHART_NS):
            texts.append(chart_label(first_child(element, "tx", CHART_NS)))
        elif matches(element, "ser", CHART_NS):
            texts.append(chart_label(first_child(element, "tx", CHART_NS)))
            categories = first_child(element, "cat", CHART_NS)
            if categories is not None:
                texts.extend(item.text or "" for item in categories.iter() if matches(item, "v", CHART_NS))
    return texts


def text_items(inspection, roots, deck, skipped):
    items = []

    def add(number, kind, text):
        text = normalize_text(text)
        if text:
            items.append({"slide": number, "kind": kind, "text": text})

    for number, entry in enumerate(inspection["slides"], 1):
        for kind, text in drawing_texts(roots[entry["part"]]):
            add(number, kind, text)
        for relation in entry["relationships"]:
            name = relation["type"].rsplit("/", 1)[-1]
            target = roots.get(relation.get("part"))
            if name == "chart" and target is not None and matches(target, "chartSpace", CHART_NS):
                # Category labels repeat once per series; one item per distinct chart string.
                for text in dict.fromkeys(normalize_text(text) for text in chart_texts(target)):
                    add(number, "chart-text", text)
            elif name == "notesSlide" and target is not None:
                for _, text in drawing_texts(target):
                    add(number, "notes", text)
            elif name in UNREAD_TEXT_PARTS or name == "chart":
                skipped.append({"deck": deck, "slide": number, "part": relation.get("part"),
                                "reason": UNREAD_TEXT_PARTS.get(name, "chart part is missing or not a chartSpace")})
    return items


def read_cuts(path, slide_count, errors):
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
        unknown = sorted(set(entry) - {"text", "slide", "reason"})
        if unknown:
            problems.append(where + "unknown fields: " + ", ".join(unknown))
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            problems.append(where + "reason must be a non-empty string")
        if ("text" in entry) == ("slide" in entry):
            problems.append(where + "give exactly one of text or slide")
        elif "text" in entry:
            text = entry["text"]
            if not isinstance(text, str) or not normalize_text(text):
                problems.append(where + "text must be a non-empty string")
            else:
                cuts.append({"index": index, "text": normalize_text(text), "reason": reason})
        else:
            slide = entry["slide"]
            if isinstance(slide, bool) or not isinstance(slide, int) or not 1 <= slide <= slide_count:
                problems.append(where + f"slide must be a source slide number from 1 to {slide_count}")
            else:
                cuts.append({"index": index, "slide": slide, "reason": reason})
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
    for source in sources:  # Longest first, so a short item cannot split a longer one.
        if budget[0] >= MAX_TEXT_COMPARISONS:
            budget[1] = True
            return False  # Unchecked text is reported as added, never silently accepted.
        budget[0] += 1
        if source in remainder:
            remainder = remainder.replace(source, "\n")
    return not any(character.isalnum() for character in remainder)


def check_coverage(source_path, candidate_path, cuts_path=None):
    source, source_roots = read_presentation(source_path)
    candidate, candidate_roots = read_presentation(candidate_path)
    skipped = []
    source_items = text_items(source, source_roots, "source", skipped)
    candidate_items = text_items(candidate, candidate_roots, "candidate", skipped)
    errors = (["source: " + error for error in source["errors"]]
              + ["candidate: " + error for error in candidate["errors"]])
    cuts = [] if cuts_path is None else read_cuts(cuts_path, len(source["slides"]), errors)

    def group(item):
        return "notes" if item["kind"] == "notes" else "slide"

    pools = {"slide": [], "notes": []}
    for item in candidate_items:
        pools[group(item)].append(item["text"])
    haystacks = {name: "\n".join(texts) for name, texts in pools.items()}
    unique_pools = {name: list(dict.fromkeys(texts)) for name, texts in pools.items()}
    budget = [0, False]
    for item in source_items:
        covering = [cut["index"] for cut in cuts
                    if cut.get("slide") == item["slide"] or cut.get("text") == item["text"]]
        if covering:
            item["cuts"] = covering
        if item["text"] in haystacks[group(item)]:
            item["status"] = "cut-but-present" if covering else "present"
        elif covering:
            item["status"] = "cut"
        else:
            item["status"] = "missing"
            item["closest"], item["similarity"] = closest_text(item["text"], unique_pools[group(item)], budget)
    for cut in cuts:
        covered = [item for item in source_items if cut["index"] in item.get("cuts", ())]
        present = sum(item["status"] == "cut-but-present" for item in covered)
        if not covered:
            still_present = "text" in cut and any(cut["text"] in haystack for haystack in haystacks.values())
        else:
            still_present = present > 0 if "text" in cut else present == len(covered)
        cut["status"] = "cut-but-present" if still_present else "applied" if covered else "unmatched"
        cut["covered_items"], cut["present_items"] = len(covered), present

    sources = {"slide": [], "notes": []}
    for item in source_items:
        sources[group(item)].append(item["text"])
    source_haystacks = {name: "\n".join(texts) for name, texts in sources.items()}
    longest_first = {name: sorted(set(texts), key=len, reverse=True) for name, texts in sources.items()}
    added = [{"slide": item["slide"], "kind": item["kind"], "text": item["text"]} for item in candidate_items
             if not derived_from_source(item["text"], source_haystacks[group(item)],
                                        longest_first[group(item)], budget)]
    counts = Counter(item["status"] for item in source_items)
    valid = not errors
    return {"schema": "daodan/pptx-coverage/v1", "valid": valid, "errors": errors,
            "complete": valid and counts["missing"] == 0,
            "notice": COVERAGE_NOTICE,
            "summary": {"source_items": len(source_items), "present": counts["present"],
                        "cut": counts["cut"], "cut_but_present": counts["cut-but-present"],
                        "unexpected_missing": counts["missing"], "added": len(added),
                        "skipped_parts": len(skipped)},
            "source": {"path": source["path"], "valid": source["valid"], "slides": len(source["slides"])},
            "candidate": {"path": candidate["path"], "valid": candidate["valid"],
                          "slides": len(candidate["slides"])},
            "cuts_file": None if cuts_path is None else str(Path(cuts_path).resolve()),
            "cuts": cuts, "items": source_items, "added": added, "skipped": skipped,
            "comparison_budget_exhausted": budget[1]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("presentation", type=Path)
    compare = commands.add_parser("compare")
    compare.add_argument("before", type=Path)
    compare.add_argument("after", type=Path)
    coverage_help = ("Check that every source text item (paragraphs, table cells, chart text, speaker "
                     "notes) reached the candidate deck, except approved cuts. Structural text "
                     "evidence only, not a visual or fidelity verdict.")
    coverage = commands.add_parser("coverage", help=coverage_help, description=coverage_help)
    coverage.add_argument("source", type=Path)
    coverage.add_argument("candidate", type=Path)
    coverage.add_argument("--cuts", type=Path, help=(
        'JSON list of approved cuts, each {"text": "...", "reason": "..."} (a source item with '
        'exactly that normalized text) or {"slide": N, "reason": "..."} (every item of source slide N)'))
    args = parser.parse_args(argv)
    if args.command == "inspect":
        result = inspect_presentation(args.presentation)
    elif args.command == "compare":
        result = compare_presentations(args.before, args.after)
    else:
        result = check_coverage(args.source, args.candidate, args.cuts)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
