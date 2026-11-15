"""Source: go-enry, the Go port of GitHub Linguist, for the language of every file and the files to leave out.

`commands` describes one `daodan-enry .` at the project's root in Daodan's container: `enry_facts.go` beside
this file, built with go-enry at `VERSION`, prints per file its language and go-enry's own predicates
(vendored, documentation, configuration, dot file, generated, binary). `read` keeps the files outside dot
folders: an excluded entry for each file go-enry calls vendored, generated, documentation or binary (the first
that holds), and per language the count of the others, in Linguist's spelling, with the language's `type` as
go-enry gives it (programming, data, markup, prose); an answer without it states none.
"""
from __future__ import annotations

import collections
import json

NAME, VERSION, RANK = "go-enry", "v2.9.6", "scanner"
WHY = ("vendored", "generated", "documentation", "binary")


def commands(context):
    if not context.inventory.files:
        return None
    return [{"tool": "daodan-enry", "argv": ["daodan-enry", "."], "cwd": ".", "env": {}, "network": "none"}]


def read(context, commands, results):
    [result] = results
    if result["returncode"] != 0:
        return {"facts": {}, "gaps": [{"kind": "model_failed", "path": ".",
                                       "detail": f"daodan-enry: {(result['stderr'] or '').strip()[-400:]}"}]}
    reasons, counts, types = {}, collections.Counter(), {}
    for row in json.loads(result["stdout"]):
        path = row["path"]
        if any(part.startswith(".") for part in path.split("/")[:-1]):
            continue  # a dot folder is outside the map's perimeter
        reasons[path] = next((reason for reason in WHY if row.get(reason)), None)
        if reasons[path] is None and row.get("language"):
            counts[row["language"]] += 1
            if row.get("type"):
                types[row["language"]] = row["type"]
    # A folder whose every file has one reason is one entry, `folder/`; the files of a mixed folder stay apart.
    under: dict[str, set] = collections.defaultdict(set)
    for path, why in reasons.items():
        parts = path.split("/")
        for depth in range(1, len(parts)):
            under["/".join(parts[:depth])].add(why)
    excluded = {}
    for path, why in sorted(reasons.items()):
        if why is None:
            continue
        parts, entry = path.split("/"), path
        for depth in range(1, len(parts)):
            if under["/".join(parts[:depth])] == {why}:
                entry = "/".join(parts[:depth]) + "/"
                break
        excluded[entry] = why
    return {"facts": {"languages": [{"language": name, "files": n, **({"type": types[name]} if name in types else {})}
                                    for name, n in sorted(counts.items())],
                      "excluded": [{"path": path, "why": why} for path, why in excluded.items()]}}
