"""The rules and the event reviewed against them are one user operation."""

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_codebase_map_system_map import BENCH, flows

import flow_paths
import mcp_service
import snapshot


class DecisionSaveTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)
        self.project = self.work / "project"
        shutil.copytree(BENCH / "app", self.project)
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        self.service = mcp_service.MapService(self.project)
        self.service.create_run(".", "example", engine=False)
        self.manifest = self.service.root / "runs/example/snapshot/manifest.sqlite"
        self.rules = flows.load_rules(BENCH / "rules.json")
        self.service.flows("example", rules=self.rules)
        self.recorded = self.manifest.with_name("flow-rules.json")

    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = flows.main(["paths", str(self.manifest), *args])
        return status, json.loads(out.getvalue())

    def test_refused_cli_and_service_keep_the_rules_and_existing_map_byte_for_byte(self):
        accepted = self.payment(self.rules)
        self.assertEqual(self.service.flows("example", trace_decision=accepted)["status"], "accepted")
        recorded = self.recorded.read_bytes()
        map_path = self.manifest.with_name("system-map.json")
        original_map = map_path.read_bytes()
        card = next(c for c in flow_paths.page(self.manifest, self.rules)["cards"]
                    if c["card_id"] != accepted["card_id"])
        first = self.service.flows("example", trace_decision={"card_id": card["card_id"], "disposition": "excluded",
                                                             "reason": "Controllo tecnico"})
        self.assertEqual(first["status"], "excluded")
        bad = {"card_id": "missing"}
        supplied, decision = self.work / "rules.json", self.work / "decision.json"
        supplied.write_text(json.dumps({"schema": flows.RULES_SCHEMA, "rules": []}))
        decision.write_text(json.dumps(bad))
        status, answer = self.cli("--rules", str(supplied), "--decision", str(decision))
        self.assertEqual((status, answer["status"]), (1, "refused"))
        self.assertEqual(self.service.flows("example", rules=[], trace_decision=bad)["status"], "refused")
        self.assertEqual(recorded, self.recorded.read_bytes())
        restored = mcp_service.MapService(self.project).flows("example", trace_id=card["card_id"])
        self.assertEqual(restored["review"]["reason"], "Controllo tecnico")
        self.assertEqual(map_path.read_bytes(), original_map)
        self.assertFalse(self.manifest.with_name(flow_paths.PENDING).exists())

    def payment(self, rules):
        cards = flow_paths.page(self.manifest, rules, limit=100)["cards"]
        card = next(c for c in cards if c["handler"] == "web/checkout.ts::onPayClick")
        steps = flow_paths.page(self.manifest, rules, card_id=card["card_id"])["steps"]
        effect = next(step for step in steps if step["to"] == "store:web state/payment" and step["end"] == "effetto")
        chain = [effect["n"]]
        while steps[chain[-1] - 1]["parent"] is not None:
            chain.append(steps[chain[-1] - 1]["parent"])
        return {"card_id": card["card_id"], "steps": chain[::-1], "data": ["pagamento"] * len(chain),
                    "area": "pagamenti e abbonamenti", "name": "Paga ordine", "types": ["funzionale"]}

    def test_interrupted_combined_acceptance_recovers_on_next_cli_read(self):
        proposed = self.rules[:-1]
        decision = self.payment(proposed)
        write = snapshot._write_json_atomic

        def interrupt(path, payload):
            if path == self.recorded:
                raise OSError("simulated interruption before the second write")
            write(path, payload)

        with mock.patch.object(snapshot, "_write_json_atomic", interrupt), self.assertRaises(OSError):
            self.service.flows("example", rules=proposed, trace_decision=decision)
        self.assertTrue(self.manifest.with_name(flow_paths.PENDING).is_file())
        status, detail = self.cli("--id", decision["card_id"])
        self.assertEqual((status, detail["review"]["status"]), (0, "accepted"))
        self.assertEqual(flows.load_rules(self.recorded), proposed)
        self.assertFalse(self.manifest.with_name(flow_paths.PENDING).exists())
        reopened = mcp_service.MapService(self.project)
        self.assertEqual(reopened.flows("example", about="Paga ordine")["flows"][0]["reachability"], "verified")
        self.assertEqual(reopened.flows("example", rules=proposed, trace_decision=decision)["status"], "accepted")

    def test_changed_rules_and_exclusion_are_visible_together_to_a_new_service(self):
        proposed = self.rules[:-1]
        card = flow_paths.page(self.manifest, proposed)["cards"][0]
        result = self.service.flows("example", rules=proposed, trace_decision={
            "card_id": card["card_id"], "disposition": "unresolved", "reason": "Effetto ignoto"})
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(flows.load_rules(self.recorded), proposed)
        review = mcp_service.MapService(self.project).flows("example", trace_id=card["card_id"])["review"]
        self.assertEqual(review, {"status": "unresolved", "reason": "Effetto ignoto"})
