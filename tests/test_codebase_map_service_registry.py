"""Registry of external services and projects: the distributed file and the rules that build it."""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import registry_build  # noqa: E402

REGISTRY = ROOT / "plugins/codebase-map/skills/map/data/service-registry.json"


class DistributedRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.entries = {e["id"]: e for e in cls.value["entries"]}

    def test_the_file_passes_the_check(self):
        self.assertEqual(registry_build.check(self.value), [])
        self.assertGreaterEqual(len(self.entries), 1000)

    def test_it_knows_the_common_ones(self):
        self.assertEqual(self.entries["stripe"]["signs"]["packages"]["pypi"], ["stripe"])
        for ident in ("mongodb", "fastapi", "react", "docker"):
            self.assertIn(ident, self.entries)
        self.assertEqual(self.entries["stripe"]["icon"], "stripe")

    def test_no_entry_comes_from_webappanalyzer(self):
        sources = {source for entry in self.entries.values() for source in entry["from"]}
        self.assertLessEqual(sources, set(registry_build.SOURCES))
        self.assertNotIn("webappanalyzer", json.dumps(self.value).lower())


class CheckTests(unittest.TestCase):
    ENTRY = {"id": "stripe", "name": "Stripe", "kind": "service", "type": "gateway", "site": "https://stripe.com",
             "icon": "stripe", "signs": {"packages": {"npm": ["stripe"]}, "patterns": {}, "env": ["STRIPE_"],
                                         "hosts": [], "files": []}, "from": ["stack-analyser"]}

    def problems(self, change, size=1000):
        entries = []
        for number in range(size):
            entry = copy.deepcopy(self.ENTRY)
            entry["id"] = f"e{number}"
            entries.append(entry)
        change(entries)
        return registry_build.check({"schema": registry_build.SCHEMA, "entries": entries})

    def test_each_rule_names_what_breaks_it(self):
        self.assertEqual(self.problems(lambda e: None), [])
        self.assertIn("1000", " ".join(self.problems(lambda e: None, size=999)))
        self.assertIn("e0: the id repeats", " ".join(self.problems(lambda e: e[1].update(id="e0"))))
        self.assertIn("type", " ".join(self.problems(lambda e: e[0].update(type="pagamento"))))
        self.assertIn("signs", " ".join(self.problems(lambda e: e[0].update(signs={"packages": {}, "patterns": {},
                                                                                 "env": [], "hosts": [], "files": []}))))
        self.assertEqual(self.problems(lambda e: e[0].update(signs=None)), [])
        self.assertIn("kind", " ".join(self.problems(lambda e: e[0].update(kind="vendor"))))


class DeriveTests(unittest.TestCase):
    def test_candidates_drop_a_scope_a_prefix_and_a_suffix(self):
        self.assertEqual(registry_build.candidates("stripe"), ["stripe"])
        self.assertEqual(registry_build.candidates("@google/genai"), ["google-genai", "google"])
        self.assertEqual(registry_build.candidates("pusher-js"), ["pusher-js", "pusher"])
        self.assertEqual(registry_build.candidates("node-mysql"), ["node-mysql", "mysql"])

    def test_a_go_module_is_one_with_its_own_go_mod(self):
        self.assertTrue(registry_build.real_go_mod(b"module github.com/stripe/stripe-go/v76\n\ngo 1.15\n"))
        self.assertFalse(registry_build.real_go_mod(b"module github.com/withastro/astro\n"))

    def test_a_package_found_for_several_entries_speaks_for_none(self):
        found = [{"id": "azure.sql", "signs": {"packages": {"pypi": ["azure"]}}},
                 {"id": "azure.mysql", "signs": {"packages": {"pypi": ["azure"], "go": ["github.com/x/y"]}}},
                 {"id": "stripe", "signs": {"packages": {"pypi": ["stripe"]}}}]
        self.assertEqual(registry_build.unambiguous(found),
                         [{"id": "azure.mysql", "signs": {"packages": {"go": ["github.com/x/y"]}}},
                          {"id": "stripe", "signs": {"packages": {"pypi": ["stripe"]}}}])

    def test_derive_starts_from_the_catalogs_not_from_its_last_run(self):
        entry = {"id": "stripe", "signs": {"packages": {"npm": ["stripe"], "pypi": ["stripe"], "go": ["github.com/stripe/stripe-go"]}}}
        last = [{"id": "stripe", "signs": {"packages": {"pypi": ["stripe"]}}, "by": "derive"}]
        self.assertEqual(registry_build.catalog_packages(entry, last), {"npm": ["stripe"], "go": ["github.com/stripe/stripe-go"]})

    def test_a_model_proposal_keeps_only_what_the_machine_verifies(self):
        entries = {"mongodb": {"id": "mongodb", "name": "MongoDB", "site": "https://www.mongodb.com/",
                               "signs": {"packages": {"npm": ["mongodb"], "rubygems": ["mongo"]}}}}
        owners = {("npm", "mongodb"): {"github.com/mongodb"}, ("pypi", "pymongo"): {"github.com/mongodb"},
                  ("pypi", "mongoengine"): {"github.com/mongoengine"}, ("pypi", "fastapi"): {"github.com/fastapi"}}
        check = {"owners": lambda eco, name: owners.get((eco, name)), "site": lambda url: url != "https://nowhere.example"}
        kept, refused = registry_build.accept([
            {"id": "mongodb", "packages": {"pypi": ["pymongo", "mongoengine"], "rubygems": ["mongoid"]}},
            {"id": "fastapi", "name": "FastAPI", "kind": "project", "type": "altro", "site": "https://fastapi.tiangolo.com",
             "packages": {"pypi": ["fastapi"]}},
            {"id": "ghost-sdk", "name": "Ghost", "kind": "project", "type": "altro", "site": "https://nowhere.example",
             "packages": {"pypi": ["nope"]}}], entries, check)
        self.assertEqual(kept[0], {"id": "mongodb", "signs": {"packages": {"pypi": ["pymongo"]}}, "by": "model"})
        self.assertEqual(kept[1]["signs"]["packages"], {"pypi": ["fastapi"]})
        self.assertEqual(len(kept), 2)
        self.assertTrue(any("mongoengine" in r for r in refused) and any("ghost-sdk" in r for r in refused))

    def test_the_owner_of_two_repositories(self):
        self.assertEqual(registry_build.owner("git+https://github.com/stripe/stripe-node.git"), "github.com/stripe")
        self.assertEqual(registry_build.owner("https://github.com/Stripe/stripe-python"), "github.com/stripe")
        self.assertEqual(registry_build.owner("git@github.com:getsentry/sentry-javascript.git"), "github.com/getsentry")
        self.assertIsNone(registry_build.owner("https://stripe.com"))


if __name__ == "__main__":
    unittest.main()
