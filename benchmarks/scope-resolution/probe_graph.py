"""Probe Task 2: risolubilità degli archi del grafo sulla mini-app reale.

Crea il run "probe-1" su app/ e registra in results/probe-graph.md le chiamate
dei file chiave (catena C5, dispatch C2, alias gateway, send_via C6) con il
loro stato di resolution, più la query di modulo "shipping" (C3).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "plugins" / "codebase-map" / "skills" / "map" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from mcp_service import MapService  # noqa: E402

FENCE = "```"
# I path del manifest sono relativi alla radice del repository git, non al target.
PREFIX = "benchmarks/scope-resolution/app/"


def main() -> int:
    svc = MapService(project_root=HERE / "app")
    try:
        svc.create_run(target=".", run_id="probe-1")
        created = "OK"
    except ValueError as exc:
        created = f"esistente: {exc}"
    report = [f"# Probe graph (Task 2) — create_run: {created}", "",
              f"I path sono repo-relativi (prefix `{PREFIX}`).", ""]
    key_files = tuple(PREFIX + rel for rel in (
        "packages/orders/service.py", "packages/orders/api.py",
        "packages/payments/gateway.py", "packages/orders/notifications.py"))
    for path in key_files:
        packet = svc.graph("probe-1", paths=[path], hops=1)
        calls = [{"caller": c.get("caller"), "parts": c.get("parts"),
                  "resolution": c.get("resolution"), "target": c.get("target_id")}
                 for c in packet.get("calls", [])]
        report += [f"## {path} (hops=1)", "", FENCE + "json",
                   json.dumps(calls, indent=1), FENCE, ""]
    mod = svc.modules("probe-1", query="shipping")
    summary = {"status": mod.get("status"), "reason": mod.get("reason"),
               "names": [c.get("name") for c in mod.get("candidates", [])],
               "files": [f for c in mod.get("candidates", []) for f in c.get("files", [])]}
    report += ["## modules(query='shipping')", "", FENCE + "json",
               json.dumps(summary, indent=1), FENCE, ""]
    (HERE / "results" / "probe-graph.md").write_text("\n".join(report), encoding="utf-8")
    print("scritto results/probe-graph.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
