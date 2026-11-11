"""Flows of the fixture in benchmarks/flow-model: deduced links, traces and units against expected.json."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
BENCH = ROOT / "benchmarks/flow-model"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import flows  # noqa: E402
import snapshot  # noqa: E402


class FlowFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-model-")).resolve()
        app = cls.work / "app"
        shutil.copytree(BENCH / "app", app)
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            subprocess.run(command, cwd=app, check=True, capture_output=True)
        cls.manifest = cls.work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(app), "--out", str(cls.manifest), "--no-engine", "--no-index"])
        cls.links = flows.link_facts(cls.manifest, flows.load_rules(BENCH / "rules.json"))
        cls.expected = json.loads((BENCH / "expected.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def deduced(self, kind):
        return {(edge["from"], edge["to"]) for edge in self.links["edges"]
                if edge["type"] == kind and edge["origin"] != "diretto"}

    def test_stores_pair_writers_and_readers_by_key(self):
        stores = {name: {k: sorted(v) for k, v in store.items()} for name, store in self.expected["stores"].items()}
        self.assertEqual(self.links["stores"], stores)

    def test_routes_match_service_method_and_path(self):
        routes = {(r["caller"], r["handler"]) for r in self.expected["routes"]}
        self.assertEqual(self.deduced("chiama"), routes)

    def test_actions_entries_external_node_and_gaps(self):
        self.assertEqual(self.deduced("attiva"), {(a["in"], a["handler"]) for a in self.expected["actions"]})
        entries = {}
        for entry in self.links["entries"]:
            entries.setdefault({"rotta": "route", "lavoro pianificato": "scheduled", "azione": "action"}[entry["kind"]],
                               []).append(entry["symbol"])
        self.assertEqual({k: sorted(v) for k, v in entries.items()},
                         {k: sorted(v) for k, v in self.expected["entry_points"].items()})
        for node in self.expected["external_nodes"]:
            self.assertIn((node["reached_by"], f"module:{node['module']}"), self.deduced("usa"))
        self.assertEqual([(g["symbol"], "not a literal" in g["reason"]) for g in self.links["gaps"]],
                         [(g["symbol"], True) for g in self.expected["gaps"]])

    def test_no_link_between_independent_fields_or_homonymous_routes(self):
        for source, target in self.expected["forbidden_links"]:
            flow = flows.trace(self.links, source, "from")
            self.assertNotIn(target, flow["nodes"], f"{source} reaches {target}")

    def test_display_reaches_the_service_store_through_the_route(self):
        case = self.expected["cross_layer"]
        flow = flows.trace(self.links, case["from"], "to")
        self.assertIn(f"store:{case['store']}", flow["nodes"])
        self.assertIn(case["through_route"], [edge.get("route") for edge in flow["edges"]])
        self.assertTrue(flow["complete"])

    def test_feature_entry_points_chain_and_cycle(self):
        through = flows.trace(self.links, self.expected["call_chain"][0], "through")
        for entry in self.expected["features"]["payment"]["entry_points"]:
            self.assertIn(entry, through["entries"])
        calls = {(e["from"], e["to"]) for e in self.links["edges"] if e["type"] == "chiama"}
        chain = self.expected["call_chain"]
        self.assertTrue(all(pair in calls for pair in zip(chain, chain[1:])))
        first, second = self.expected["cycle"]
        self.assertTrue({(first, second), (second, first)} <= calls)

    def test_a_stop_leaves_the_flow_incomplete(self):
        start = "web/checkout.ts::onPayClick"
        self.assertEqual(flows.trace(self.links, start, "from", max_edges=2)["stopped"], "budget")
        self.assertFalse(flows.trace(self.links, start, "from", boundary=["web"])["complete"])
        self.assertFalse(flows.trace(self.links, "web/debug.ts::probe", "from")["complete"])

    def test_units_keep_writers_with_readers_and_assign_every_file(self):
        sizes = flows.file_sizes(self.manifest)
        for limit in (120_000, 1_500):
            result = flows.units(self.links, sizes, ["."], limit)
            self.assertEqual((result["assigned"], result["files"]), (len(sizes), len(sizes)))
            for store in self.links["stores"].values():
                block = {s.split("::")[0] for s in store["writes"] + store["reads"]}
                self.assertTrue(any(block <= set(unit["files"]) for unit in result["units"]), block)
        self.assertEqual(flows.units(self.links, sizes, ["."], 1_500), flows.units(self.links, sizes, ["."], 1_500))


if __name__ == "__main__":
    unittest.main()
