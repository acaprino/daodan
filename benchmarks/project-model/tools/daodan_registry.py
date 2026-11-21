"""Read-only benchmark of the shipped service registry.

`snapshot.py write <dir> --out manifest.sqlite --no-engine --no-index`, then `service_registry.recognize(manifest)`
(`daodan/core/service_registry.py` with `data/service-registry.json`). The registry
reports its services with a declared sign, following the stack's project-level rule. The evidence is the
first declaration's file when available. The historical comparison leaves frameworks unscored and retains
every registry match, including mentions, in `detail`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import _fw

VERSION = "service-registry v1 (stack-analyser 1.27.6, simple-icons 16.37.0, cncf-landscape 75b47639)"
SCRIPTS = Path(os.environ.get("PM_PLUGIN_SCRIPTS") or
               (next((p / "daodan/core" for p in Path(__file__).resolve().parents
                      if (p / "daodan/core").is_dir()), "/daodan/map/core")))
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
    return normalise(service_registry.recognize(manifest))


def normalise(found: list[dict]) -> dict:
    services = []
    for entry in found:
        if entry["kind"] != "service":
            continue
        declared = [s for s in entry["signs"] if s["strength"] == "declared"]
        if not declared:
            continue
        evidence = next((s["path"] for s in declared if s["path"]), None)
        kind = RANK_KINDS.get(entry["type"])
        services.append({"name": entry["name"], **({"kind": kind} if kind else {}),
                         **({"evidence": evidence} if evidence else {})})
    return {"services": services,
            "detail": {"ids": sorted(e["id"] for e in found),
                       "entries": {e["id"]: {"kind": e["kind"], "type": e["type"],
                                             "signs": sorted({f"{s['sign']}:{s['value']}@{s['path']}" for s in e["signs"]})[:6]}
                                   for e in found}}}
