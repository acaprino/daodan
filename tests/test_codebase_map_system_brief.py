"""System brief of the flow-model fixture: what the analysis steps produced, grouped for who proposes the map."""

import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_codebase_map_system_map import fixture  # noqa: E402
import flows  # noqa: E402
import snapshot  # noqa: E402
import system_brief  # noqa: E402

PAY, CREATE, RETRY, ORDERS = ("web/checkout.ts::onPayClick", "server/payments.py::create_payment",
                              "server/jobs.py::retry_declined", "server/orders.py::list_orders")


def unavailable(*_):
    return {"status": "unavailable", "reason": "not in tests"}


class BriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture(cls)
        cls.run_stack = system_brief.stack_analyser.run
        system_brief.stack_analyser.run = unavailable
        cls.brief = system_brief.brief(cls.manifest, cls.rules)

    @classmethod
    def tearDownClass(cls):
        system_brief.stack_analyser.run = cls.run_stack
        shutil.rmtree(cls.work, True)

    def groups(self, value):
        return {g["resource"]: g["entries"] for g in value["groups"]}

    def test_one_candidate_group_per_shared_resource(self):
        self.assertEqual(self.groups(self.brief), {"store:db/payments": sorted([PAY, CREATE, RETRY, ORDERS]),
                                                   "module:card payment provider": sorted([PAY, CREATE, RETRY])})
        self.assertEqual(self.brief["alone"], ["admin/orders.py::list_all_orders", "web/cart.ts::toggleTheme"])

    def test_a_resource_everyone_touches_adds_a_group_and_changes_no_other(self):
        links = copy.deepcopy(flows.cached_links(self.manifest, self.rules))
        for entry in links["entries"]:
            links["edges"].append({"from": entry["symbol"], "to": "store:app/session", "type": "scrive",
                                   "origin": "dedotto", "site": entry["site"]})
        cached = system_brief.flows.cached_links
        system_brief.flows.cached_links = lambda *_: links
        try:
            wider = system_brief.brief(self.manifest, self.rules)
        finally:
            system_brief.flows.cached_links = cached
        self.assertEqual(len(wider["groups"]), 3)
        for group in self.brief["groups"]:
            self.assertIn(group, wider["groups"])
        self.assertEqual(wider["alone"], [])

    def test_the_steps_that_did_not_run_are_declared(self):
        self.assertEqual((self.brief["steps"]["statico"], self.brief["steps"]["inferenza"], self.brief["steps"]["dinamico"]),
                         (True, True, False))

    def test_externals_say_their_source(self):
        external = next(e for e in self.brief["externals"] if e["name"] == "card payment provider")
        self.assertEqual(external["from"], ["modules"])
        self.assertEqual(self.brief["stack_analyser"]["status"], "unavailable")

    def test_the_text_keeps_within_the_cap(self):
        self.assertLessEqual(len(self.brief["text"]), system_brief.CAP)
        self.assertEqual(self.brief["truncated"], 0)
        self.assertIn("store:db/payments", self.brief["text"])
        small = system_brief.brief(self.manifest, self.rules, cap=600)
        self.assertLessEqual(len(small["text"]), 600)
        self.assertGreater(small["truncated"], 0)


class DeclaredTests(unittest.TestCase):
    def test_compose_declares_services_and_the_image_is_recognized(self):
        work = Path(tempfile.mkdtemp(prefix="brief-"))
        self.addCleanup(shutil.rmtree, work, True)
        project = work / "project"
        project.mkdir()
        (project / "docker-compose.yml").write_text(
            "services:\n  web:\n    build: .\n  db:\n    image: postgres:16\n", encoding="utf-8")
        (project / "Dockerfile").write_text("FROM node:22-alpine AS build\n", encoding="utf-8")
        (project / "app.py").write_text("print('hi')\n", encoding="utf-8")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
            subprocess.run(command, cwd=project, check=True, capture_output=True)
        manifest = work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(project), "--out", str(manifest), "--no-engine", "--no-index"])
        run = system_brief.stack_analyser.run
        system_brief.stack_analyser.run = unavailable
        try:
            value = system_brief.brief(manifest, [])
        finally:
            system_brief.stack_analyser.run = run
        declared = {(d["kind"], d["name"]): d for d in value["declared"]}
        self.assertEqual((declared[("service", "db")]["image"], declared[("service", "db")]["file"]),
                         ("postgres", "docker-compose.yml"))
        self.assertIn(("service", "web"), declared)
        self.assertEqual(declared[("base image", "node")]["file"], "Dockerfile")
        self.assertEqual(value["runtime_files"], ["Dockerfile", "docker-compose.yml"])
        postgres = next(e for e in value["externals"] if e["id"] == "postgresql")
        self.assertEqual(postgres["from"], ["registry"])
        self.assertIn("docker-compose.yml", postgres["paths"])


if __name__ == "__main__":
    unittest.main()
