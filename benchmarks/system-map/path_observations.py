"""Read candidates and check how exact, sampled and conflicting calls survive decisions and reopening."""

import asyncio
from contextlib import closing
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

from path_reuse import AREA, REPO, RUN, MapService, app_http, app_module, mcp_rows, secret_mask
import code_graph
import dynamic
from dynamic import python as observer
import edge_store


def observed_fixture(manifest):
    """Save a synthetic static result, two observations, and a disagreement at the third call site."""
    with code_graph.Snapshot(manifest) as snap:
        targets = dict(snap.connection.execute("SELECT name,id FROM sem_declarations WHERE file='handlers.py'"))
        holes, static, runtime = [], [], []
        refs = snap.connection.execute("SELECT id,file,caller,l0,c0,last_name FROM sem_references WHERE kind='call'")
        for ref, file, caller, line, col, name in refs:
            place = dict(reference_id=ref, file=file, language="python", kind="call", caller=caller, l0=line, c0=col)
            if name == "clash":
                static.append({**place, "target_id": targets["refund"], "symbol": targets["refund"],
                               "verdict": "project-callable", "confidence": "confirmed", "resolver": "scip-python",
                               "external": None, "payload": {}})
            else:
                holes.append({**place, "class": "no-occurrence", "resolver": "scip-python",
                              "reason": "no static target"})
            if name in ("live", "sample"):
                confidence, target = ("observed", "save") if name == "live" else ("sampled", "also_save")
                runtime.append({**place, "verdict": "project-callable", "symbol": targets[target],
                                "target_id": targets[target], "resolver": f"fixture-{confidence}",
                                "confidence": confidence, "payload": {}})
        coverage = edge_store.language_coverage(code_graph._sites(snap, "python"), static, holes)
        binding = edge_store.store_binding(snap.store, manifest, snap.store.metadata["parser_fingerprint"],
                                           {"python": {"engine": "scip-python", "state": "fresh", "coverage": coverage}}, {})
        out = edge_store.default_edge_store(manifest)
        edge_store.write_edge_store(out, static, binding, holes)
        sites = [{"file": "controls.py", "name": "clash", "line": 4, "column": 4, "role": "call",
                  "callees": [{"file": "handlers.py", "kind": "project", "name": "cancel", "type": "function",
                               "line": 3, "column": 0}]}]
        joined, facts = dynamic.join(snap, "python", sites, static, observer)
        assert facts["conflicts"]["count"] == 1
        code_graph.write_observed(snap, out, "python", runtime + joined, {"resolver": "fixture-observed"})


def verify(work):
    project = work / "project"
    project.mkdir()
    (project / "controls.py").write_text('@trigger("refresh")\ndef dispatch(live, sample, clash):\n'
                                         '    live("payments")\n    sample("orders")\n    clash("refunds")\n')
    (project / "handlers.py").write_text("def save(key): pass\ndef also_save(key): pass\n"
                                         "def refund(key): pass\ndef cancel(key): pass\n")
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    service = MapService(project)
    service.create_run(".", RUN, engine=False)
    manifest = service.root / "runs" / RUN / "snapshot" / "manifest.sqlite"
    observed_fixture(manifest)

    def cli(operation, *arguments, exit_code=0):
        run = subprocess.run([sys.executable, "-m", "daodan", "flows", operation, str(manifest), *arguments],
                             cwd=REPO, capture_output=True, text=True)
        assert run.returncode == exit_code, (run.stdout, run.stderr)
        return json.loads(run.stdout)

    def mcp(**arguments):
        return asyncio.run(mcp_rows(project, arguments))

    with closing(app_module.App(work / "app", environment={})) as app:
        app.service, app.context = service, {"run_id": RUN}
        # The scanner integration with its real executable has its own Modal test.
        with patch.object(secret_mask, "masked", side_effect=lambda text, name: {"text": text, "found": 0, "kinds": []}):
            tool = next(t["call"] for t in app._tools() if t["name"] == "codebase_map_flows")
            assert not manifest.with_name("flow-rules.json").exists()
            rows = cli("candidates")["candidates"]
            assert rows == mcp(entry_offset=0)["candidates"] == tool({"entry_offset": 0})["candidates"]
            candidate = next(row for row in rows if row["symbol"] == "controls.py::dispatch")
            assert candidate["status"] == "candidate"
            forms = service.flows(RUN, shape_offset=0)
            question = next(q for q in forms["questions"] if q["shape"] == candidate["shape"])
            service.flows(RUN, shape_answers={"id": forms["id"], "answers": {str(question["row"]): "comando"}})
            names = ("save", "also_save", "refund")
            service.flows(RUN, rules=[{"callee": f"handlers.py::{name}", "link": "scrive", "store": "db",
                                       "key": "arg0"} for name in names])
            card = next(row for row in cli("paths")["cards"] if row["handler"] == candidate["symbol"])
            card_id = card["card_id"]
            steps = cli("paths", "--id", card_id)["steps"]
            assert steps == mcp(trace_id=card_id)["steps"]
            with app_http(app) as get:
                assert steps == get(f"/api/app/paths?id={card_id}")["steps"]

            targets = {s["to"]: s for s in steps if s.get("to")}
            for name, line, confidence, resolver in (("save", 3, "observed", "fixture-observed"),
                                                    ("also_save", 4, "sampled", "fixture-sampled")):
                s = targets[f"handlers.py::{name}"]
                assert (s["site"], s["confidence"], s["resolver"]) == (f"controls.py:{line}", confidence, resolver)
            assert targets["handlers.py::save"]["end"] is None
            assert targets["handlers.py::also_save"]["end"] == "lacuna"
            assert all(s["from"] != "handlers.py::also_save" for s in steps)
            for target in ("handlers.py::refund", "handlers.py::cancel"):
                assert targets[target]["conflict"] and targets[target]["end"] == "lacuna"

            admitted = "Pagamento registrato"
            for name, key, status in ((admitted, "payments", "accepted"), ("Ordini incerti", "orders", "refused"),
                                      ("Rimborso incerto", "refunds", "refused")):
                step = targets[f"store:db/{key}"]
                assert step["end"] == ("effetto" if status == "accepted" else "lacuna")
                decision = {"card_id": card_id, "name": name, "steps": [step["n"]], "area": AREA,
                            "types": ["funzionale"], "data": ["identificativo"]}
                file = work / "decision.json"
                file.write_text(json.dumps(decision), encoding="utf-8")
                assert cli("paths", "--decision", str(file), exit_code=int(status == "refused"))["status"] == status
                assert mcp(trace_decision=decision)["status"] == tool({"trace_decision": decision})["status"] == status
            # Reopen a new service and require the same evidence and only the exact admitted flow on every adapter.
            app.service = MapService(project)
            reopened_tool = next(t["call"] for t in app._tools() if t["name"] == "codebase_map_flows")
            with app_http(app) as get:
                assert get(f"/api/app/paths?id={card_id}")["steps"] == steps
            found = cli("paths", "--about", AREA)["flows"]
            assert found == mcp(about=AREA)["flows"] == reopened_tool({"about": AREA})["flows"]
            flow, = found
            assert flow["name"] == admitted and flow["fresh"] and flow["reachability"] == "verified"
    return {"candidate": candidate["shape"], "handler": candidate["symbol"], "observed": "handlers.py::save",
            "sampled_stop": targets["handlers.py::also_save"]["reason"], "conflicting_targets": ["refund", "cancel"],
            "accepted_effects": ["payments"], "refused_effects": ["orders", "refunds"],
            "interfaces": ["CLI", "MCP SDK", "app tool", "app HTTP (read)"]}


if __name__ == "__main__":
    os.environ["DAODAN_CONTAINER"] = "off"
    with tempfile.TemporaryDirectory(prefix="daodan-observations-") as temp:
        print(json.dumps(verify(Path(temp).resolve()), ensure_ascii=False, indent=2))
