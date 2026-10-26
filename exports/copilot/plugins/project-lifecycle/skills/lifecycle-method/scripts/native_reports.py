"""Provenance wrappers for existing native specialist reports."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

WORKSPACE_DISPOSITIONS = {
    "KEEP": "retain",
    "KEEP+IGNORE": "correct",
    "REMOVE": "retire",
    "REMOVE+IGNORE": "retire",
    "UNIGNORE": "correct",
    "REVIEW": "clarify",
    "REPORT-ONLY": "clarify",
}


def workspace_decision(disposition: str) -> dict:
    if disposition not in WORKSPACE_DISPOSITIONS:
        raise ValueError(f"Unknown native workspace disposition: {disposition}")
    return {"native_disposition": disposition, "decision": WORKSPACE_DISPOSITIONS[disposition],
            "executable": disposition not in {"REVIEW", "REPORT-ONLY", "KEEP"}}


def wrap(report: Path, *, role: str, role_version: str, input_sha256: str,
         status: str, scope: dict, gaps: list) -> dict:
    if status not in {"pending", "running", "delivered", "failed"}:
        raise ValueError("Invalid delivery status")
    if len(input_sha256) != 64 or any(c not in "0123456789abcdef" for c in input_sha256):
        raise ValueError("Invalid input fingerprint")
    report = Path(report)
    raw = None
    if report.is_file():
        raw = {"path": str(report), "sha256": hashlib.sha256(report.read_bytes()).hexdigest()}
    elif status == "delivered":
        raise ValueError("A delivered worker must provide its report")
    return {"wrapper_version": "daodan/native-result/v1", "role": role,
            "role_version": role_version, "input_sha256": input_sha256,
            "scope": scope, "status": status, "raw_report": raw, "gaps": gaps}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True,
                        help="JSON role/version/input/scope/status/gaps; no invented defaults")
    args = parser.parse_args()
    try:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        result = wrap(args.report, **metadata)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Native result refused: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

