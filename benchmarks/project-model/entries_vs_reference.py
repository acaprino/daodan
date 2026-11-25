"""How many of the entries of a reference's flows the entries of an analysis stand for (plan task 11.5).

    python benchmarks/project-model/entries_vs_reference.py <reference.json> <explore result.json>

A reference flow starts at an `attiva` arrow: a control, cited as `file:line`. The cite is covered by a static entry when
one sits in the same file within `NEAR` lines of it or the cite falls in the lines of the function it starts from
(`static_spans`), and by an observed entry (the controls the exploration pressed,
`against_static.links` of `modal_explore.py`) when the cite falls in the lines its handler spans (an inline arrow) or within
`NEAR` lines of a place the code names an observed handler (`onSubmit={handleSubmit}`: `observed_binding_sites`). The
reference is read from the path given; no reference is kept in the repository.
"""
from __future__ import annotations

import collections
import json
import sys

NEAR = 2  # the lines between a cite and the binding a static reader reports


def cites(reference: dict) -> dict[str, str]:
    """The `file:line` each flow's first control is cited at, with the flow's name (the first flow that cites it)."""
    found: dict[str, str] = {}
    for flow in reference["flows"]:
        for arrow in flow["arrows"]:
            if arrow["kind"] == "attiva" and ":" in arrow["cite"]:
                found.setdefault(arrow["cite"], flow["name"])
    return found


def compare(reference: dict, links: dict) -> dict:
    """`{cites, static, observed, both, none, by_folder}`: how many cites there are and how many only a static entry covers,
    only an observed one, both, or neither, and the same per top folder."""
    static = [site.rpartition(":") for site in links["static_sites"]]
    held = links.get("static_spans", [])
    spans = links["observed_spans"]
    bound = [site.rpartition(":") for site in links.get("observed_binding_sites", [])]
    kinds, by_folder = collections.Counter(), collections.defaultdict(collections.Counter)
    for cite in cites(reference):
        file, _, line = cite.rpartition(":")
        at = int(line) if line.isdecimal() else None
        if at is None:
            continue
        by_static = any(f == file and l.isdecimal() and abs(int(l) - at) <= NEAR for f, _, l in static) or \
            any(s["file"] == file and s["line"] <= at <= s["end"] for s in held)
        by_browser = any(s["file"] == file and s["line"] <= at <= s["end"] for s in spans) or \
            any(f == file and l.isdecimal() and abs(int(l) - at) <= NEAR for f, _, l in bound)
        kind = "both" if by_static and by_browser else "static" if by_static else "observed" if by_browser else "none"
        kinds[kind] += 1
        by_folder[file.split("/")[0]][kind] += 1
    return {"cites": sum(kinds.values()), "static": kinds["static"], "observed": kinds["observed"], "both": kinds["both"],
            "none": kinds["none"],
            "by_folder": {folder: dict(count) for folder, count in sorted(by_folder.items())}}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as reference, open(sys.argv[2], encoding="utf-8") as result:
        print(json.dumps(compare(json.load(reference), json.load(result)["against_static"]["links"]), indent=1))
