"""System brief of the flow-model fixture: what the analysis steps produced, grouped for who proposes the map."""

import copy
import json
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
import test_codebase_map_mcp as mcp_tests  # noqa: E402  the module, so that its tests are not collected twice
import system_brief  # noqa: E402

PAY, CREATE, RETRY, ORDERS = ("web/checkout.ts::onPayClick", "server/payments.py::create_payment",
                              "server/jobs.py::retry_declined", "server/orders.py::list_orders")


def text(value):
    return system_brief._text(value, system_brief.LIMIT, system_brief.HOLDERS)[0]


class BriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture(cls)
        cls.brief = system_brief.brief(cls.manifest, cls.rules)
        cls.text = text(cls.brief)

    @classmethod
    def tearDownClass(cls):
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
        self.assertIn("card payment provider [", self.text)  # an id the registry does not have is not printed

    def test_the_text_keeps_within_the_cap(self):
        small, truncated = system_brief._text(self.brief, len(self.text) - 1, system_brief.HOLDERS)
        self.assertLessEqual(len(small), len(self.text) - 1)
        self.assertEqual(truncated, 2)
        self.assertIn("- 2 more groups, fewest entry points: G1 store:db/payments (4), "
                      "G2 module:card payment provider (3)", small)
        self.assertIn("- 4 more entry points, by directory: server 3, web 1", small)
        self.assertIn("E5 web/cart.ts::toggleTheme [azione] at web/cart.ts:18, alone", small)
        self.assertLessEqual(len(system_brief._text(self.brief, 600, system_brief.HOLDERS)[0]), 600)

    def test_a_header_says_how_to_read_and_what_is_not_found(self):
        header = self.text.split("\n## ")[0].splitlines()
        self.assertEqual(header[0], "# System brief")
        self.assertLess(len(header), 10)
        self.assertIn("`entry points 0` means the machine found none", "\n".join(header))

    def test_sections_have_fixed_labels_and_one_numbered_item_per_line(self):
        sections = {part.split("\n")[0]: part.split("\n")[1:] for part in self.text.split("\n## ")[1:]}
        self.assertEqual(list(sections), ["Steps", "Counts", "Modules", "Directories", "Externals",
                                          "Entry points", "Groups"])  # an empty section is left out
        self.assertEqual(sections["Counts"][0], "entry points 6")
        self.assertEqual(sections["Modules"], ["M1 app (source-tree, 23 files)",
                                               "M2 card payment provider (component, 0 files)",
                                               "M3 payment (feature, 4 files)"])
        self.assertEqual(sections["Directories"][1], "D2 admin (3 files)")
        self.assertEqual(sections["Externals"], ["X1 card payment provider [altro] from modules: server/gateway.py"])
        self.assertEqual(sections["Entry points"], [
            "E1 admin/orders.py::list_all_orders [rotta] at admin/orders.py:6, alone",
            "E2 server/jobs.py::retry_declined [lavoro pianificato] at server/jobs.py:5",
            "E3 server/orders.py::list_orders [rotta] at server/orders.py:10",
            "E4 server/payments.py::create_payment [rotta] at server/payments.py:16",
            "E5 web/cart.ts::toggleTheme [azione] at web/cart.ts:18, alone",
            "E6 web/checkout.ts::onPayClick [azione] at web/checkout.ts:22"])
        self.assertEqual(sections["Groups"], ["G1 store:db/payments (4): E2, E3, E4, E6",
                                              "G2 module:card payment provider (3): E2, E4, E6"])

    def test_a_group_past_the_holders_counts_its_entry_points_by_directory(self):
        text = system_brief._text(self.brief, system_brief.LIMIT, 3)[0]
        self.assertIn("G1 store:db/payments (4): by directory server 3, web 1", text)
        self.assertIn("G2 module:card payment provider (3): E2, E4, E6", text)
        self.assertNotIn("E3 ", text)  # named by no line, so counted
        self.assertIn("- 1 more entry points, by directory: server 1", text)

    def test_an_answer_at_full_cap_keeps_under_the_limit(self):
        groups = [{"resource": f'store:db/k{i}é"', "entries": [f"app/a{i}.py::f", f"app/b{i}.py::g"],
                   "by_directory": {"app": 2}} for i in range(3000)]  # escapes and non-ASCII cost in JSON
        value = {**self.brief, "groups": groups, "alone": [],
                 "entry_points": [{"symbol": s, "kinds": ["rotta"], "site": s.split("::")[0] + ":1"}
                                  for g in groups for s in g["entries"]]}
        answer = system_brief.fit(value, {"status": "ok", "run_id": "r" * 128, "brief": "", "truncated": 0,
                                          "format": "x" * 9000 + "\n" * 500})
        self.assertLessEqual(len(json.dumps(answer)), system_brief.LIMIT)
        self.assertGreater(len(json.dumps(answer)), system_brief.LIMIT * 0.95)  # the room left goes to the brief
        self.assertGreater(answer["truncated"], 0)


class AnswerSizeTests(unittest.TestCase):
    """No answer of `codebase_map_flows` passes the host's limit: one the host does not show is lost to the model."""

    setUpClass = classmethod(mcp_tests.SystemMapServiceTests.setUpClass.__func__)
    tearDownClass = classmethod(mcp_tests.SystemMapServiceTests.tearDownClass.__func__)

    def test_brief_map_and_about_answers_keep_under_the_limit_with_the_data_before_the_format(self):
        brief = self.service.flows("system", brief=True)
        self.assertEqual(list(brief)[-1], "format")  # the data first, the format and its «Sequence» last
        answers = {"brief": brief, "map": self.service.flows("system", map=self.map),
                   "about": self.service.flows("system", about="Pagare un ordine")}
        for name, answer in answers.items():
            with self.subTest(answer=name):
                self.assertLessEqual(len(json.dumps(answer)), system_brief.LIMIT)



class DeclaredTests(unittest.TestCase):
    def test_a_technology_of_a_target_inside_the_repository_cites_its_path_from_the_root(self):
        work = Path(tempfile.mkdtemp(prefix="brief-"))
        self.addCleanup(shutil.rmtree, work, True)
        project = work / "project"
        (project / "server").mkdir(parents=True)
        (project / "server/pyproject.toml").write_text('[project]\nname = "server"\ndependencies = ["fastapi"]\n', encoding="utf-8")
        (project / "server/app.py").write_text("print('hi')\n", encoding="utf-8")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
            subprocess.run(command, cwd=project, check=True, capture_output=True)
        manifest = work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(project / "server"), "--out", str(manifest), "--no-engine", "--no-index"])
        fastapi = next(e for e in system_brief.brief(manifest, [])["externals"] if e["id"] == "fastapi")
        self.assertEqual((fastapi["from"], fastapi["paths"]), (["registry"], ["server/pyproject.toml"]))

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
        value = system_brief.brief(manifest, [])
        declared = {(d["kind"], d["name"]): d for d in value["declared"]}
        self.assertEqual((declared[("service", "db")]["image"], declared[("service", "db")]["file"]),
                         ("postgres", "docker-compose.yml"))
        self.assertIn(("service", "web"), declared)
        self.assertEqual(declared[("base image", "node")]["file"], "Dockerfile")
        self.assertEqual(value["runtime_files"], ["Dockerfile", "docker-compose.yml"])
        postgres = next(e for e in value["externals"] if e["id"] == "postgresql")
        self.assertEqual(postgres["from"], ["registry"])
        self.assertIn("docker-compose.yml", postgres["paths"])
        self.assertIn(f"{postgres['name']} id postgresql [", text(value))  # the mapper copies it as `registry`
        self.assertIn("\n## Runtime files\nR1 Dockerfile\nR2 docker-compose.yml\n## Declared\n"
                      "S1 base image node in Dockerfile:1\nS2 service web in docker-compose.yml:2\n"
                      "S3 service db (postgres) in docker-compose.yml:4", text(value))


if __name__ == "__main__":
    unittest.main()
