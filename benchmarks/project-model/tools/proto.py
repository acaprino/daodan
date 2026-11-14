"""proto: `proto status --json`. One entry per tool, the winning source by proto's precedence; the versions are
resolved through the network (the command fails when it is blocked). Standard library only."""
from __future__ import annotations

import json

from _versions import canon, rel, sh

VERSION = "0.64.0"


def run(fixture_dir, work_dir) -> dict:
    r = sh(["proto", "status", "--json"], fixture_dir, {"NO_COLOR": "1"}, timeout=180)
    text = r["out"].strip()
    if not text.startswith("{"):
        if "no_configured_tools" in r["err"] + text or (r["rc"] == 0 and not text):
            return {"toolchains": []}  # proto's own answer for a project that declares nothing
        raise RuntimeError(f"proto exit {r['rc']}: {(r['err'] or text).strip()[-400:]}")
    seen, toolchains = set(), []
    for tool, e in json.loads(text).items():
        path = rel(e.get("config_source") or "", fixture_dir)
        if path is None or e.get("config_version") is None:
            continue
        item = {"tool": canon(tool), "version": e["config_version"], "declared_in": path}
        key = (item["tool"], item["version"], item["declared_in"])
        if key not in seen:  # proto lists java as java, jdk and jre
            seen.add(key)
            toolchains.append(item)
    return {"toolchains": toolchains}
