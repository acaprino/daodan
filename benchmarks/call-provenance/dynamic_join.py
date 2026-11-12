"""Joins the call sites observed in a test run with the engine's verdicts, call by call.

    python dynamic_join.py <positions.json.gz> <engine-count.json> <observed dir> <out.json> [sites.json]

`positions` holds every call reference of the snapshot (file, language, l0, c0, l1, c1,
name, lexical resolution, engine verdict), written by benchmarks/flow-model/modal_engine_count.py.
`observed dir` holds the observed-*.json files of dynamic_map.js; `sites.json`, from
`dynamic_map.js --sites`, gives each site the number of same-name sites in its function.
A site matches a reference at the end of the callee (1-based line, byte column) with
the same name. Only references the engine was asked about and left unresolved change
state; a reference never asked keeps it.

Two counts. Strict: a site alone with its name in its function, whose callees all have
a source URL. Loose: every matched site, a callee without URL counted as external.
A site of dynamic_record.js is exact: it counts in both.
A callee without URL is a native builtin or code created at runtime, such as the named
wrappers of jest-mock: it can stand for a mocked project function.
"""
from __future__ import annotations

import collections
import glob
import gzip
import json
import os
import sys

UNRESOLVED = {"unresolved", "ambiguous-target", "project-not-a-symbol"}
# Callees of the test harness stand for a mocked function, not for the real destination.
HARNESS = ("jest", "@jest/", "expect", "pretty-format", "babel-", "@babel/")


def classify(callees: list[dict]) -> str:
    if not callees:
        return "none"
    if any(c["kind"] == "package" and (c.get("module") or "").startswith(HARNESS) for c in callees):
        return "harness"
    if any(c["kind"] == "project" for c in callees):
        return "project" if all(c["kind"] == "project" for c in callees) else "mixed"
    return "nourl" if any(c["kind"] == "builtin" for c in callees) else "external"


def observed_sites(directory: str) -> dict:
    """Sites of every shard, keyed by the callee's end; a site seen in several shards keeps all callees."""
    sites: dict[tuple, dict] = {}
    for path in sorted(glob.glob(os.path.join(directory, "observed-*.json"))):
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
            for site in data["sites"]:
                key = (site["file"], site["line"] + 1, site["column"] + len(site["name"].encode("utf-8")), site["name"])
                known = sites.setdefault(key, {"file": site["file"], "name": site["name"], "callees": {},
                                               "exact": bool(data.get("exact"))})
                for callee in site["callees"]:
                    known["callees"][(callee["kind"], callee.get("file") or callee.get("module"),
                                      callee["name"], callee["line"])] = callee
    return sites


def ratio(resolved: int, resolvable: int) -> dict:
    return {"resolved": resolved, "resolvable": resolvable,
            "ratio": round(resolved / resolvable, 4) if resolvable else None}


def main(positions_path: str, count_path: str, observed_dir: str, out_path: str, sites_path: str = "") -> None:
    with gzip.open(positions_path, "rt", encoding="utf-8") as stream:
        positions = json.load(stream)
    with open(count_path, encoding="utf-8") as stream:
        count = json.load(stream)
    same_name = {}
    if sites_path:
        with open(sites_path, encoding="utf-8") as stream:
            same_name = json.load(stream)
    sites = observed_sites(observed_dir)
    executed = {site["file"] for site in sites.values()}
    by_key = collections.defaultdict(list)
    for row in positions:
        by_key[(row["file"], row["l1"], row["c1"], row["name"])].append(row)

    per_language: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    names = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    for key, site in sites.items():
        callees = list(site["callees"].values())
        if not callees:
            continue
        rows = by_key.get(key)
        if not rows:
            per_language["(no reference)"]["observed_sites_unmatched"] += 1
            continue
        observed = classify(callees)
        shared = same_name.get("|".join(str(part) for part in key))
        unique = shared == 1 or site["exact"]
        for row in rows:
            tally = per_language[row["language"]]
            verdict = row["verdict"] or ""
            proven = row["resolution"] == "resolved" or verdict.startswith("edge")
            tally[f"observed_{observed}"] += 1
            tally["sites_unique" if unique else "sites_shared_name" if shared else "sites_not_in_sites_file"] += 1
            if verdict in UNRESOLVED:
                key_name = f"gain_{observed}" if observed in ("project", "external", "nourl") else f"kept_{observed}"
                if key_name.startswith("gain"):
                    area = "test" if "/tests/" in row["file"] or "/test/" in row["file"] else "source"
                    tally[f"{key_name}_{area}"] += 1
                    if unique:
                        tally[f"{key_name}_unique"] += 1
                    names[(row["language"], key_name)][row["name"]] += 1
            elif verdict == "external-definition":
                key_name = ("agree_external" if observed == "external" else
                            "contradiction_external_vs_project" if observed == "project" else f"external_{observed}")
            elif proven:
                key_name = ("agree_project" if observed == "project" else
                            "contradiction_project_vs_external" if observed == "external" else f"proven_{observed}")
            else:
                key_name = f"never_asked_{observed}"
            tally[key_name] += 1
            if key_name.startswith("contradiction"):
                if unique:
                    tally[f"{key_name}_unique"] += 1
                examples[(row["language"], key_name)].append(
                    {"file": row["file"], "line": row["l0"], "name": row["name"], "verdict": verdict,
                     "resolution": row["resolution"], "same_name_sites": shared,
                     "callees": [[c["kind"], c.get("file") or c.get("module"), c["name"]] for c in callees][:4]})

    languages = (count.get("resolution") or {}).get("by_language") or {}
    result = {"positions": len(positions), "observed_sites_with_callee": sum(1 for s in sites.values() if s["callees"]),
              "files_executed": len(executed), "sites_file": bool(same_name), "languages": {}}
    for language, tally in sorted(per_language.items()):
        entry = {"counts": dict(sorted(tally.items())),
                 "contradictions": {key: rows for (lang, key), rows in sorted(examples.items()) if lang == language}}
        base = languages.get(language)
        if base:
            resolved, resolvable = base["resolved"], base["resolvable"]
            asked = [row for row in positions if row["language"] == language and (row["verdict"] or "") in UNRESOLVED]
            entry.update({
                "before": ratio(resolved, resolvable),
                "strict": ratio(resolved + tally["gain_project_unique"], resolvable - tally["gain_external_unique"]),
                "loose": ratio(resolved + tally["gain_project"],
                               resolvable - tally["gain_external"] - tally["gain_nourl"]),
                "asked_unresolved": len(asked),
                "asked_unresolved_in_executed_files": sum(1 for row in asked if row["file"] in executed),
                "files_with_calls": len({row["file"] for row in positions if row["language"] == language}),
                "files_executed": len({row["file"] for row in positions if row["language"] == language
                                       and row["file"] in executed}),
                "top_gains": {key: names[(language, key)].most_common(12)
                              for key in ("gain_external", "gain_nourl", "gain_project")}})
        result["languages"][language] = entry
    with open(out_path, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    for language, entry in result["languages"].items():
        if "before" in entry:
            print(language, json.dumps({k: entry[k] for k in ("before", "strict", "loose")}))
    print("sites with callee", result["observed_sites_with_callee"], "files executed", len(executed))


if __name__ == "__main__":
    main(*sys.argv[1:6])
