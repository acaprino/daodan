"""The routes Noir finds in the container. The pre-map binds them and their gaps to its snapshot."""
from __future__ import annotations

import json
from pathlib import Path


NAME, VERSION, RANK = "noir", "1.5.0", "scanner"
# The release asset's digest from api.github.com/repos/owasp-noir/noir/releases/tags/v1.5.0.
DOWNLOAD = (f"https://github.com/owasp-noir/noir/releases/download/v{VERSION}/noir-v{VERSION}-linux-x86_64",
            "4e176c92ee16f60fafd3be7ea6f605d82d3f27c39704a3f875cbed5bd050dc70", "noir")


def commands(context):
    from container import WORKDIR
    if context.inventory.files:
        return [{"tool": NAME, "argv": [NAME, "scan", WORKDIR, "-f", "json", "--no-log"],
                 "cwd": ".", "env": {}, "network": "none"}]


def read(context, commands, results):
    import entries
    [result] = results
    if result["returncode"] != 0:
        raise ValueError(f"Noir exited with {result['returncode']}: {result['stderr'].strip()[-400:]}")
    report = json.loads(result["stdout"])
    if not isinstance(report.get("endpoints"), list):
        raise ValueError("the Noir report has no endpoints array")
    candidates, gaps = [], []
    if report.get("errors"):
        gaps.append({"kind": "model_partial", "detail": f"Noir reported {len(report['errors'])} scan errors"})
    for item in entries.noir(report, result["root"], gaps=gaps):
        file = item["symbol"].split("::", 1)[0]
        header = context.inventory.headers.get(file)
        if header is None:
            gaps.append({"kind": "outside_snapshot", "path": file, "detail": "Noir cites a file outside the snapshot"})
            continue
        # Reads once per file (also shared with the other pre-map readers), verifies the snapshot hash.
        context.inventory.text(file)
        _, _, number = item["site"].rpartition(":")
        if number.isdecimal() and not 1 <= int(number) <= header["lines"]:
            gaps.append({"kind": "model_partial", "path": file, "detail": f"Noir cites an absent line: {number}"})
            continue
        candidates.append(item)
    return {"facts": {"noir_entries": candidates}, "gaps": gaps}


def unavailable(error):
    return {"source": f"{NAME}@{VERSION}", "kind": "noir_unavailable", "detail": str(error),
            "remedy": "refresh the pre-map in Daodan's container"}


def from_record(report):
    source = f"{NAME}@{VERSION}"
    if not any(s["source"] == source for s in report["sources"]):
        return [], [unavailable("this pre-map has no Noir run")]
    return [{"handler": None, **row} for row in report.get("noir_entries", [])], [g for g in report["gaps"] if g["source"] == source]


def evidence(manifest: Path) -> tuple[list, list]:
    """Read the persisted candidates without running an analyzer. Legacy and stale reports explain their gap."""
    from premap.flow_entries import read_record
    try:
        return from_record(read_record(Path(manifest)))
    except (OSError, KeyError, TypeError, ValueError) as error:
        return [], [unavailable(error)]


def recorded(manifest: Path) -> list[dict]:
    return evidence(manifest)[0]
