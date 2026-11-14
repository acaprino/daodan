"""GitHub Linguist (the Ruby gem): the `github-linguist` CLI for the languages, the gem's classes for the reasons.

`github-linguist --breakdown --json` lists, per language, the files it counts: only programming and markup
languages, the ones its type table says, minus vendored, generated and documentation files. The gem's classes
(`linguist_facts.rb`: LazyBlob over the same repository, the same .gitattributes source) give every file's language
whatever its type and the reason a file is left out. The two are compared; `_raw` says whether they agree.
The fixture must be a Git repository with its files committed: the gem reads the commit, not the folder.
"""
from __future__ import annotations

import json
from pathlib import Path

from _lang import sh

VERSION = "9.7.0"
HELPER = Path(__file__).with_name("linguist_facts.rb")


def run(fixture_dir, work_dir) -> dict:
    cli = sh(["github-linguist", "--breakdown", "--json"], cwd=fixture_dir)
    if cli.returncode != 0:
        raise RuntimeError(f"github-linguist -> {cli.returncode}: {cli.stderr[-500:]}")
    counted = json.loads(cli.stdout) if cli.stdout.strip() else {}
    facts = sh(["ruby", str(HELPER), str(fixture_dir)], cwd=fixture_dir)
    if facts.returncode != 0:
        raise RuntimeError(f"linguist_facts.rb -> {facts.returncode}: {facts.stderr[-500:]}")
    rows = json.loads(facts.stdout)
    languages, excluded, errors = [], [], []
    for row in rows:
        if "error" in row:
            errors.append(f"{row['path']}: {row['error']}")
            continue
        for why in ("vendored", "generated", "documentation", "binary"):
            if row[why]:
                excluded.append({"path": row["path"], "why": why})
                break
        else:
            if row["language"]:
                languages.append({"path": row["path"], "language": row["language"], "type": row["type"]})
    cli_files = {f for entry in counted.values() for f in entry["files"]}
    lib_files = {r["path"] for r in rows if r.get("stats")}
    return {"languages": languages, "excluded": excluded,
            "_raw": {"cli_files": len(cli_files), "cli_equals_library": cli_files == lib_files,
                     "cli_only": sorted(cli_files - lib_files)[:5], "library_only": sorted(lib_files - cli_files)[:5],
                     "errors": errors[:5]}}
