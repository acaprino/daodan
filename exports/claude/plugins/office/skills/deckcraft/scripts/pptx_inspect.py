"""Read and compare PPTX packages independently of the presentation engine.

Reuse Office's bounded ZIP/XML reader. Never extract packages, fetch links or
render slides. Deltas are evidence to review, not an automatic fidelity verdict.
"""

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


_READER = Path(__file__).resolve().parents[2] / "xlsx/scripts/xlsx_inspect.py"
_SPEC = importlib.util.spec_from_file_location("office_pptx_package_reader", _READER)
package = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(package)
PRESENTATION_NS = {"http://schemas.openxmlformats.org/presentationml/2006/main",
                   "http://purl.oclc.org/ooxml/presentationml/main"}
DRAWING_NS = {"http://schemas.openxmlformats.org/drawingml/2006/main",
             "http://purl.oclc.org/ooxml/drawingml/main"}
MAIN_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"


def matches(element, local, namespaces=PRESENTATION_NS):
    return package.namespace(element.tag) in namespaces and package.local_name(element.tag) == local


def text_runs(root):
    return [element.text or "" for element in root.iter() if matches(element, "t", DRAWING_NS)]


def inspect_presentation(path):
    result = {"schema": "daodan/pptx-inspection/v1", "path": str(Path(path).resolve()),
              "valid": False, "errors": [], "parts": {}, "slides": [],
              "external_relationships": [], "features": {}, "payload_hashes": [],
              "visual_review": "unverified: no rendering performed"}
    errors = result["errors"]
    try:
        parts = package.read_package(path)
        result["parts"] = {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                           for name, data in sorted(parts.items())}
        roots, budget = {}, [0]
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
    return result


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("presentation", type=Path)
    compare = commands.add_parser("compare")
    compare.add_argument("before", type=Path)
    compare.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    result = (inspect_presentation(args.presentation) if args.command == "inspect"
              else compare_presentations(args.before, args.after))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
