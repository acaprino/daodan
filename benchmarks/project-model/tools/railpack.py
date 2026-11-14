"""Railpack: `railpack info --format json`. It reports only the versions of the provider it detects (the
language it would build) and one source per package; a package left at Railpack's own default is not a
declaration and is not reported. Standard library only."""
from __future__ import annotations

import json
import re
from pathlib import Path

from _versions import canon, sh

VERSION = "0.43.0"


def _file(source: str, root) -> str | None:
    for candidate in (source, re.split(r"[\s(]", source)[0]):
        if candidate and (Path(root) / candidate).is_file():
            return candidate
    return None


def run(fixture_dir, work_dir) -> dict:
    r = sh(["railpack", "info", "--format", "json", "."], fixture_dir, {"NO_COLOR": "1"}, timeout=180)
    try:
        data = json.loads(r["out"])
    except ValueError:
        raise RuntimeError(f"railpack exit {r['rc']}: {r['err'].strip()[-400:]}") from None
    if not data.get("success"):
        msgs = "; ".join(str(x.get("Msg")) for x in data.get("logs") or [])
        raise RuntimeError(f"railpack: no plan ({msgs[:300]})")
    toolchains = []
    for name, p in (data.get("resolvedPackages") or {}).items():
        source = str(p.get("source") or "")
        if not p.get("requestedVersion") or source.lower().startswith(("default", "railpack_")) or not source:
            continue
        item = {"tool": canon(name), "version": p["requestedVersion"], "via": source}
        path = _file(source, fixture_dir)
        if path:
            item["declared_in"] = path
        toolchains.append(item)
    return {"toolchains": toolchains}
