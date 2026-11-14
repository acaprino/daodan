"""Baseline, read only: Daodan's service registry, called the way `system_brief.py` calls it.

`snapshot.py write <dir> --out manifest.sqlite --no-engine --no-index`, then `service_registry.recognize(manifest)`
(`plugins/codebase-map/skills/map/scripts/service_registry.py` with `data/service-registry.json`). The registry
knows names, a kind (`service` or `project`) and a type, not frameworks: `frameworks` is not given. Services are the
recognised entries of kind `service`; the kind of the answer is the registry type (RANK_KINDS translates it); the
evidence is the first sign's file. Every recognised entry, `project` ones included, is in `detail.ids`, for the
comparison with the stack-analyser CLI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import _fw

VERSION = "service-registry v1 (stack-analyser 1.27.6, simple-icons 16.37.0, cncf-landscape 75b47639)"
SCRIPTS = Path(os.environ.get("PM_PLUGIN_SCRIPTS") or
               (next((p / "plugins/codebase-map/skills/map/scripts" for p in Path(__file__).resolve().parents
                      if (p / "plugins/codebase-map/skills/map/scripts").is_dir()), "/daodan/map/scripts")))
RANK_KINDS = {"database": "database", "coda": "queue", "autenticazione": "authentication", "gateway": "gateway",
              "servizio o API": "service"}


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir).resolve(), Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    manifest = work / "manifest.sqlite"
    code, out, err = _fw.execute([sys.executable, SCRIPTS / "snapshot.py", "write", root, "--out", manifest,
                                  "--no-engine", "--no-index"], work)
    if code != 0:
        raise RuntimeError(f"snapshot.py exited {code}: {(err or out)[-600:]}")
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import service_registry
    found = service_registry.recognize(manifest)
    services = []
    for entry in found:
        if entry["kind"] != "service":
            continue
        paths = [s["path"] for s in entry["signs"] if s["path"]]
        kind = RANK_KINDS.get(entry["type"])
        services.append({"name": entry["name"], **({"kind": kind} if kind else {}),
                         **({"evidence": paths[0]} if paths else {})})
    return {"services": services,
            "detail": {"ids": sorted(e["id"] for e in found),
                       "entries": {e["id"]: {"kind": e["kind"], "type": e["type"],
                                             "signs": sorted({f"{s['sign']}:{s['value']}@{s['path']}" for s in e["signs"]})[:6]}
                                   for e in found}}}
