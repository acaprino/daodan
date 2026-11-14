"""go-enry, the Go port of Linguist: the `enry` CLI for the languages, its library functions for the reasons.

`enry -json -all <dir>` walks the folder and prints language -> files. It leaves out silently what its library
calls vendored, documentation, configuration and dot files, and never looks at .gitattributes or generated
files (a TODO in its source). `enry_facts` (a small Go program built against the same library) prints those
predicates per file, plus `IsGenerated` and `IsBinary`, so that the left-out files get a reason. Built from the
default `go install`: Go regexps (RE2), without the oniguruma tag.
"""
from __future__ import annotations

import json

from _lang import sh

VERSION = "v2.9.6"


def run(fixture_dir, work_dir) -> dict:
    cli = sh(["enry", "-json", "-all", "."], cwd=fixture_dir)
    if cli.returncode != 0:
        raise RuntimeError(f"enry -> {cli.returncode}: {cli.stderr[-500:]}")
    listing = json.loads(cli.stdout) if cli.stdout.strip() else {}
    facts = sh(["enry_facts", str(fixture_dir)], cwd=fixture_dir)
    if facts.returncode != 0:
        raise RuntimeError(f"enry_facts -> {facts.returncode}: {facts.stderr[-500:]}")
    rows = {r["path"]: r for r in json.loads(facts.stdout)}
    excluded, silent = [], 0
    for path, row in sorted(rows.items()):
        row["binary"] = row["binary"] or row["image"]
        for why in ("vendored", "generated", "documentation", "binary"):
            if row[why]:
                excluded.append({"path": path, "why": why})
                break
        else:
            silent += row["configuration"] or row["dot_file"]
    left = {e["path"] for e in excluded}
    languages = [{"path": path, "language": language} for language, paths in listing.items() for path in paths
                 if path not in left]
    return {"languages": languages, "excluded": excluded,
            "_raw": {"left_out_as_configuration_or_dot_file": silent}}
