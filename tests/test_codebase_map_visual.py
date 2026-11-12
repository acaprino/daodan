"""The explorer's envelope `daodan/visual@1`: structure, memberships, states, flows and node types."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import card_store  # noqa: E402
import mcp_service  # noqa: E402
import semantic_store  # noqa: E402
import visual  # noqa: E402
from snapshot_store import open_snapshot, resolve_run_snapshot  # noqa: E402

DECLARED = {"schema": "daodan/declared-modules/v1", "modules": [
    {"name": "runner", "kind": "component", "location": "internal", "responsibility": "Runs the job",
     "members": ["src/app/a.py", "src/app/b.py"], "evidence": ["src/app/a.py"]},
    {"name": "helpers", "kind": "component", "location": "internal", "responsibility": "Shared helpers",
     "members": ["src/app/b.py"], "evidence": ["src/app/b.py"]},
    {"name": "running", "kind": "feature", "location": "internal", "responsibility": "Running a job",
     "members": ["src/app/a.py"], "evidence": ["src/app/a.py"]},
]}


def git_project(project: Path) -> None:
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=project, check=True, capture_output=True)


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="map-visual-")).resolve()
        self.addCleanup(shutil.rmtree, self.project, True)
        files = {
            "src/app/__init__.py": "",
            "src/app/a.py": "from .b import helper\n\n\ndef run():\n    return helper()\n",
            "src/app/b.py": "def helper():\n    return 1\n",
            "pyproject.toml": "[project]\nname = \"demo\"\nversion = \"0.1.0\"\n",
            "codebase-modules.json": json.dumps(DECLARED),
        }
        for rel, text in files.items():
            (self.project / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.project / rel).write_text(text, encoding="utf-8")
        git_project(self.project)
        self.service = mcp_service.MapService(self.project)
        self.service.create_run(".", "r1", engine=False)
        self.envelope = visual.build_envelope(self.project / ".daodan/map/runs/r1")

    def test_structure_states_and_shared_membership(self):
        envelope = self.envelope
        self.assertEqual(envelope["schema"], "daodan/visual@1")
        refs = {entity["ref"]: entity for entity in envelope["entities"]}
        self.assertIn("imports:file:src/app/a.py->file:src/app/b.py", {relation["ref"] for relation in envelope["relations"]})
        logical = [item for item in envelope["memberships"] if item["member"] == "file:src/app/b.py" and item["view"] == "logical"]
        self.assertEqual(sorted(item["group"] for item in logical), ["component:helpers", "component:runner"])
        physical_groups = {item["group"] for item in envelope["memberships"] if item["view"] == "physical"}
        self.assertFalse(any(refs[group]["type"] == "feature" for group in physical_groups))
        for relation in envelope["relations"]:
            self.assertIn(relation["source"], refs, relation)
            self.assertIn(relation["target"], refs, relation)
        self.assertEqual((refs["component:runner"]["provenance"], refs["component:runner"]["status"]), ("declared", "confirmed"))
        self.assertIn("defines:file:src/app/b.py->symbol:src/app/b.py::helper", {relation["ref"] for relation in envelope["relations"]})
        self.assertEqual(refs["symbol:src/app/b.py::helper"]["freshness"], "uncovered")
        self.assertEqual(envelope["flows"], [])
        self.assertTrue(envelope["meta"]["snapshot_digest"])

    def card(self, run_id: str, purpose: str) -> None:
        run = self.project / ".daodan/map/runs" / run_id
        manifest = resolve_run_snapshot(run, json.loads((run / "state.json").read_text(encoding="utf-8")))
        with open_snapshot(manifest) as store:
            semantic_store.upsert_meta_cards(store, card_store.default_cards_path(manifest),
                                             [{"file": "src/app/b.py", "symbol": "helper", "purpose": purpose}])

    def test_a_card_gives_freshness_and_description_and_goes_stale_with_the_body(self):
        self.card("r1", "Returns the constant one.")
        helper = {item["ref"]: item for item in visual.build_envelope(self.project / ".daodan/map/runs/r1")["entities"]}[
            "symbol:src/app/b.py::helper"]
        self.assertEqual((helper["freshness"], helper["description"]), ("fresh", "Returns the constant one."))
        (self.project / "src/app/b.py").write_text("def helper():\n    return 2\n", encoding="utf-8")
        self.service.create_run(".", "r2", engine=False)
        helper = {item["ref"]: item for item in visual.build_envelope(self.project / ".daodan/map/runs/r2")["entities"]}[
            "symbol:src/app/b.py::helper"]
        self.assertEqual(helper["freshness"], "stale_body")

    def test_an_export_is_published_once_per_digest_and_never_rewritten(self):
        run, store_root = self.project / ".daodan/map/runs/r1", self.project / ".daodan/map"
        first = visual.export(run, store_root)
        self.assertEqual(first.parent, store_root / "views" / "r1")
        self.assertEqual(json.loads((first / "visual.json").read_text(encoding="utf-8"))["schema"], "daodan/visual@1")
        written = (first / "visual.json").stat().st_mtime_ns
        self.assertEqual(visual.export(run, store_root), first)
        self.assertEqual((first / "visual.json").stat().st_mtime_ns, written)
        self.card("r1", "Returns the constant one.")
        second = visual.export(run, store_root)
        self.assertNotEqual(second, first)
        self.assertTrue((first / "visual.json").is_file())
        self.assertEqual(sorted(path.name for path in (store_root / "views/r1").iterdir()), sorted([first.name, second.name]))

    def test_an_export_refuses_a_changed_parser_an_unknown_reference_and_moving_cards(self):
        run, store_root = self.project / ".daodan/map/runs/r1", self.project / ".daodan/map"
        with mock.patch.object(visual.snapshot, "parser_fingerprint", return_value="another parser"), \
                self.assertRaisesRegex(ValueError, "refresh"):
            visual.export(run, store_root)
        broken = visual.build_envelope(run)
        broken["relations"].append({"ref": "imports:x", "kind": "imports", "source": "file:src/app/a.py",
                                    "target": "file:nowhere.py", "status": "confirmed", "evidence": []})
        with mock.patch.object(visual, "build_envelope", return_value=broken), \
                self.assertRaisesRegex(ValueError, "unknown entity: file:nowhere.py"):
            visual.export(run, store_root)
        calls = iter(["before", "during", "after"])
        with mock.patch.object(visual, "_cards_digest", side_effect=lambda *_: next(calls)), \
                self.assertRaisesRegex(ValueError, "card store changed"):
            visual.export(run, store_root)
        self.assertFalse((store_root / "views/r1").exists())

    def test_addresses_lose_credentials_query_and_fragment(self):
        self.assertEqual(visual.sanitize_address("https://u:p@host:8443/x?token=1#f"), "https://host:8443/x")
        self.assertEqual(visual.sanitize_address("not a url"), "not a url")
        self.assertEqual(visual.sanitize_address("db password=hunter2"), "")


class FlowEnvelopeTests(unittest.TestCase):
    def test_flows_list_their_steps_and_nodes_carry_type_and_location(self):
        project = Path(tempfile.mkdtemp(prefix="map-visual-flows-")).resolve()
        self.addCleanup(shutil.rmtree, project, True)
        shutil.copytree(ROOT / "benchmarks/flow-model/app", project, dirs_exist_ok=True)
        git_project(project)
        service = mcp_service.MapService(project)
        service.create_run(".", "flows", engine=False)
        rules = json.loads((ROOT / "benchmarks/flow-model/rules.json").read_text(encoding="utf-8"))["rules"]
        rules = [{**rule, "node_type": "database"} if rule.get("store") == "db" else rule for rule in rules]
        service.flows("flows", rules=rules)
        envelope = visual.build_envelope(project / ".daodan/map/runs/flows")
        refs = {entity["ref"]: entity for entity in envelope["entities"]}
        self.assertEqual(len(envelope["flows"]), 6)
        for flow in envelope["flows"]:
            for step in flow["steps"]:
                self.assertIn(step["source"], refs, step)
                self.assertIn(step["target"], refs, step)
            self.assertTrue(set(flow["nodes"]) <= set(refs))
        self.assertEqual(refs["store:db/payments"]["node_type"], "database")
        self.assertNotIn("node_type", refs["store:web state/cart"])
        external = refs["external:card-payment-provider"]
        self.assertEqual((external["location"], external["node_type"]), ("external", "servizio o API"))
        self.assertEqual(refs["symbol:server/payments.py::create_payment"]["node_type"], "servizio o API")
        self.assertEqual(refs["symbol:web/checkout.ts::renderCheckout"]["node_type"], "schermata")
        pay = next(flow for flow in envelope["flows"] if flow["entry"] == "symbol:web/checkout.ts::onPayClick")
        self.assertIn("external:card-payment-provider", pay["nodes"])
        self.assertIn(["shop", "POST", "/payments"], [step.get("route") for step in pay["steps"]])
        with self.assertRaisesRegex(ValueError, "node_type belongs to a store rule"):
            service.flows("flows", rules=[{**rules[0], "node_type": "nave"}])


if __name__ == "__main__":
    unittest.main()
