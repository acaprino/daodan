"""Measure the public paths operation on a freshly analyzed flow-model and on its reopened snapshot."""

from __future__ import annotations

import asyncio
from collections import Counter
from contextlib import closing, contextmanager
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "benchmarks" / "flow-model"
sys.path.insert(0, str(REPO / "daodan" / "core"))

from mcp_service import MapService
import app as app_module
import mcp_server
import secret_mask

RUN = "paths"
FLOW = "Registrazione del pagamento"
AREA = "pagamenti e abbonamenti"
# Count calls, not inferred cache hits. All the target's execution and installation phases go through its container.
CALLS = {("entries", "_syntax"): "ast_inventories", ("flows", "link_facts"): "link_builds",
         ("snapshot", "write_snapshot"): "snapshots_built", ("engine_pass", "run_pass"): "engine_passes",
         ("container", "run_in_container"): "container_runs", ("container", "run_commands"): "container_commands",
         ("engine_tools", "download"): "tool_downloads", ("flow_paths", "_inventory"): "path_inventories",
         ("flow_paths", "_steps"): "path_expansions", ("flow_paths", "_build_graph"): "graph_preparations"}
COLUMNS = ["source_opens", "source_directory_listings", "snapshot_connections", "card_cache_connections",
           "flow_links_reads", "system_map_reads", "tree_parses", "package_manager_processes", *CALLS.values()]


def started(args) -> str:
    """The name of the program a `subprocess.Popen` audit event starts. Windows gives no executable and one
    command line: its first word, quoted or not (an audit hook must not raise on a line it cannot split)."""
    line = args[0] or (args[1] if isinstance(args[1], str) else args[1][0])
    if not args[0]:
        line = line[1:].partition('"')[0] if line.startswith('"') else (line.split(None, 1) or [""])[0]
    return Path(line).stem


class Measure:
    """The audit hook sees real file opens/listings. SQLite has its own event, outside Python's file-open API."""

    def __init__(self, app: Path, manifest: Path):
        self.source = os.fspath(app)
        self.manifest = os.fspath(manifest)
        self.card_cache = os.fspath(manifest.with_name("trace-cards.sqlite"))
        self.json_files = {os.fspath(manifest.with_name(file)): metric for file, metric in
                           (("flow-links.json", "flow_links_reads"), ("system-map.json", "system_map_reads"))}
        self.counts = None
        sys.addaudithook(self.audit)

    def audit(self, event, args):
        if self.counts is None:
            return
        if event == "subprocess.Popen" and started(args) in {"npm", "pnpm", "yarn", "pip", "uv", "cargo"}:
            self.counts["package_manager_processes"] += 1
        # A store opened read-only is named by its URI, whose separators are not Windows's.
        if event == "sqlite3.connect" and (self.manifest in str(args[0]) or Path(self.manifest).as_uri() in str(args[0])):
            self.counts["snapshot_connections"] += 1
        if event == "sqlite3.connect" and (self.card_cache in str(args[0])
                                           or Path(self.card_cache).as_uri() in str(args[0])):
            self.counts["card_cache_connections"] += 1
        if event == "open" and isinstance(args[0], str) and args[1] and "r" in args[1] and args[0] in self.json_files:
            self.counts[self.json_files[args[0]]] += 1
        if event not in ("open", "os.scandir", "os.listdir") or not isinstance(args[0], str):
            return
        path = args[0]
        if path == self.source or path.startswith(self.source + os.sep):
            self.counts["source_opens" if event == "open" else "source_directory_listings"] += 1

    def profile(self, frame, event, arg):
        if event == "call":
            metric = CALLS.get((frame.f_globals.get("__name__"), frame.f_code.co_name))
            if metric:
                self.counts[metric] += 1
        elif event == "c_call" and getattr(arg, "__name__", "") == "parse":
            if type(getattr(arg, "__self__", None)).__module__ == "tree_sitter":
                self.counts["tree_parses"] += 1

    @contextmanager
    def phase(self):
        counts = Counter(dict.fromkeys(COLUMNS, 0))
        self.counts = counts
        previous = sys.getprofile()
        sys.setprofile(self.profile)
        try:
            yield counts
        finally:
            sys.setprofile(previous)
            self.counts = None


def pay_card(service: MapService) -> tuple[dict, dict]:
    page = service.flows(RUN, trace_offset=0, limit=100)
    entry = next(row for row in page["cards"] if row["handler"] == "app/web/checkout.ts::onPayClick")
    return entry, service.flows(RUN, trace_id=entry["card_id"])


async def mcp_rows(project: Path, arguments: dict):
    from mcp import Client

    async with Client(mcp_server.create_server(project)) as client:
        response = await client.call_tool("codebase_map_flows", {"run_id": RUN, **arguments})
        assert not response.is_error, response.content
        return response.structured_content or json.loads(response.content[0].text)


@contextmanager
def app_http(app):
    with app.serve(token="fixture") as server:
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            with closing(http.client.HTTPConnection(*server.server_address, timeout=10)) as connection:
                def get(path):
                    connection.request("GET", path, headers={"X-Daodan-Token": "fixture"})
                    response = connection.getresponse()
                    assert response.status == 200, response.status
                    return json.load(response)
                yield get
        finally:
            server.shutdown()
            thread.join()


def adapters(project, manifest, card_id, expected, rejected):
    for entry, cwd in ((["-m", "daodan", "flows"], REPO), ([str(REPO / "daodan/core/flows.py")], project.parent)):
        cli = subprocess.run([sys.executable, *entry, "paths", str(manifest), "--id", card_id],
                             cwd=cwd, check=True, capture_output=True, text=True)
        assert json.loads(cli.stdout)["steps"] == expected
    cli = [sys.executable, "-m", "daodan", "flows", "paths", str(manifest)]
    decision = project.parent / "rejected.json"
    decision.write_text(json.dumps(rejected), encoding="utf-8")
    denied = subprocess.run([*cli, "--decision", str(decision)], cwd=REPO, capture_output=True, text=True)
    assert denied.returncode == 1 and json.loads(denied.stdout)["status"] == "refused", denied
    about = subprocess.run([*cli, "--about", FLOW], cwd=REPO, capture_output=True, text=True, check=True)
    assert json.loads(about.stdout)["flows"][0]["reachability"] == "verified"
    effects = subprocess.run([*cli, "--effects"], cwd=REPO, capture_output=True, text=True, check=True)
    inventory = json.loads(effects.stdout)
    assert inventory["status"] == "ok" and inventory["writes"] > 0
    effect_fields = ("effects", "writes", "reached", "without_entry")
    with closing(app_module.App(project.parent / "app-work", environment={})) as app:
        app.service, app.context = MapService(project), {"run_id": RUN}
        with app_http(app) as get:
            assert get(f"/api/app/paths?id={card_id}")["steps"] == expected
            shown = get("/api/app/paths?effects=1")
            assert all(shown[k] == inventory[k] for k in effect_fields)
        # This benchmark uses the same no-finding scanner fixture as the app tests; the real binary runs on Modal.
        with patch.object(secret_mask, "masked", side_effect=lambda text, name: {"text": text, "found": 0, "kinds": []}):
            tool = next(t for t in app._tools() if t["name"] == "codebase_map_flows")
            assert tool["call"]({"trace_id": card_id})["steps"] == expected
            assert asyncio.run(mcp_rows(project, {"trace_id": card_id}))["steps"] == expected
            shown = asyncio.run(mcp_rows(project, {"effect_offset": 0}))
            assert all(shown[k] == inventory[k] for k in effect_fields)


def measure(work: Path) -> dict:
    project = work / "project"
    shutil.copytree(FIXTURE / "app", project / "app")
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    service = MapService(project)
    service.create_run("app", RUN, engine=False)
    manifest = service.root / "runs" / RUN / "snapshot" / "manifest.sqlite"
    rules = json.loads((FIXTURE / "rules.json").read_text())["rules"]
    meter = Measure(project / "app", manifest)
    with meter.phase() as link:
        service.flows(RUN, rules=[{**rule, "callee": "app/" + rule["callee"]} for rule in rules])
    with meter.phase() as cold:
        card, answer = pay_card(service)
    steps = {step["n"]: step for step in answer["steps"]}
    effect = next(s for s in steps.values() if s["to"] == "store:web state/payment" and s["type"] == "scrive")
    chain = [effect["n"]]
    while (parent := steps[chain[-1]].get("parent")) is not None:
        chain.append(parent)
    chain.reverse()
    assert len(chain) >= 2
    # The checkout and the theme both touch the same web state store. Only the payment key follows this action.
    assert all(s["to"] != "store:web state/theme" for s in steps.values())
    decision = {"card_id": card["card_id"], "steps": chain, "name": FLOW, "area": AREA, "types": ["funzionale"],
                "data": ["identificativo e stato del pagamento"] * len(chain)}
    report = service.flows(RUN, trace_decision=decision)
    assert report["status"] == "accepted", report
    false = {**decision, "steps": [effect["n"]], "data": ["stato del pagamento"]}
    refusal = service.flows(RUN, trace_decision=false)
    assert refusal["status"] == "refused", refusal
    reopened = MapService(project)
    with meter.phase() as hot:
        reopened_card, reopened_answer = pay_card(reopened)
    assert reopened_card["card_id"] == card["card_id"] and reopened_answer["steps"] == answer["steps"]
    assert reopened_answer["review"] == reopened_card["review"] == {"status": "accepted", "flow": report["id"]}
    with meter.phase() as read_map:
        found = reopened.flows(RUN, about=FLOW)
    recorded, = found["flows"]
    assert recorded["reachability"] == "verified" and recorded["fresh"], recorded
    saved = json.loads(manifest.with_name("system-map.json").read_text(encoding="utf-8"))
    trace = next(flow["trace"] for flow in saved["flows"] if flow["id"] == report["id"])
    assert trace["card_id"] == card["card_id"] and trace["entry"]["symbol"] == card["handler"]
    assert trace["steps"] == [{key: value for key, value in steps[n].items() if key not in {"n", "parent", "end"}}
                              for n in chain]
    assert cold["path_inventories"] == cold["path_expansions"] == cold["graph_preparations"] == 1
    for action in ("path_inventories", "path_expansions", "graph_preparations", "source_opens", "source_directory_listings",
                   "package_manager_processes", "ast_inventories", "tree_parses", "link_builds", "snapshots_built", "engine_passes",
                   "container_runs", "container_commands", "tool_downloads"):
        assert not hot[action], (action, hot)
    adapters(project, manifest, card["card_id"], answer["steps"], false)
    return {"fixture": "flow-model", "steps_to_payment": chain, "refused": refusal["reason"],
            "adapters": ["CLI", "MCP SDK", "app HTTP", "app tool"], "link_rules": link,
            "first_paths": cold, "second_paths": hot, "reopen_map": read_map}


if __name__ == "__main__":
    os.environ["DAODAN_CONTAINER"] = "off"
    with tempfile.TemporaryDirectory(prefix="daodan-paths-") as temp:
        print(json.dumps(measure(Path(temp).resolve()), indent=2, ensure_ascii=False))
