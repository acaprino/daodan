"""Registry of external services and projects: the distributed file and the rules that build it."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import registry_build  # noqa: E402
import service_registry  # noqa: E402
import stack_recognition  # noqa: E402

REGISTRY = ROOT / "daodan/data/service-registry.json"
ADDITIONS = ROOT / "daodan/data/registry-additions.json"
NOTICES = ROOT / "daodan/data/REGISTRY-NOTICES.md"
DATA = REGISTRY.parent


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
        self.assertEqual(self.entries["stripe"]["mark"], "marks/stripe.svg")

    def test_no_entry_comes_from_webappanalyzer(self):
        sources = {source for entry in self.entries.values() for source in entry["from"]}
        self.assertLessEqual(sources, set(registry_build.SOURCES))
        self.assertNotIn("webappanalyzer", json.dumps(self.value).lower())

    def test_a_category_is_the_entry_s_own_field_never_its_name(self):
        for ident, category in (("eslint", "tool"), ("docker", "tool"), ("renovate", "tool"), ("nodejs", "tool"),
                                ("cypressci", "tool"), ("opentelemetry", "library"), ("playwright", "tool")):
            self.assertEqual((ident, self.entries[ident].get("category")), (ident, category))
        self.assertEqual(service_registry.entry_category({"id": "eslint", "kind": "project"}), "framework")
        self.assertEqual(service_registry.entry_category({"id": "playwright", "kind": "service"}), "service")
        self.assertEqual(service_registry.entry_category({"id": "x", "kind": "service", "category": "tool"}), "tool")

    def test_every_recognisable_project_has_its_category_written_and_none_is_a_framework_by_default(self):
        """A model proposed the categories (`REGISTRY-NOTICES.md`); the machine checks the value, these the classes."""
        self.assertEqual([i for i, e in self.entries.items()
                          if e["kind"] == "project" and e.get("signs") and not e.get("category")], [])
        for category, idents in (("framework", ("angular", "django", "express", "nextjs")),
                                 ("library", ("numpy", "boto3", "sqlalchemy", "d3js", "fontawesome")),
                                 ("tool", ("jest", "biomejs", "ansible", "asdf", "alembic")),
                                 ("service", ("kafka", "etcd", "keycloak"))):
            for ident in idents:
                self.assertEqual((ident, self.entries[ident]["kind"], self.entries[ident].get("category")),
                                 (ident, "project", category))

    def test_a_sign_a_catalog_gives_wrongly_is_taken_away_by_an_addition(self):
        self.assertNotIn("passport-google-oauth20", self.entries["gcp"]["signs"]["packages"]["npm"])
        self.assertNotIn("postman-collection", self.entries["postman"]["signs"]["packages"]["npm"])
        signs = {"packages": {"npm": ["googleapis", "passport-google-oauth20"], "pypi": ["x"]}, "patterns": {},
                 "env": ["GOOGLE_CLOUD_PROJECT"], "hosts": [], "files": []}
        entries = {"gcp": {"id": "gcp", "name": "GCP", "kind": "service", "type": "servizio o API", "site": None,
                           "mark": None, "signs": signs, "from": ["stack-analyser"]}}
        registry_build.apply_additions(entries, [{"id": "gcp", "wrong_signs": {
            "packages": {"npm": ["passport-google-oauth20"], "pypi": ["x"]}}, "by": "catalog"}])
        self.assertEqual(entries["gcp"]["signs"]["packages"], {"npm": ["googleapis"]})
        self.assertEqual(entries["gcp"]["from"], ["additions", "stack-analyser"])

    def test_the_built_file_is_what_its_additions_make_of_it(self):
        """The checked-in file agrees with `registry-additions.json` by the build's own merge rule."""
        entries = copy.deepcopy(self.entries)
        registry_build.apply_additions(entries, json.loads(ADDITIONS.read_text(encoding="utf-8"))["entries"])
        self.assertEqual(entries, self.entries)


class CheckTests(unittest.TestCase):
    ENTRY = {"id": "stripe", "name": "Stripe", "kind": "service", "type": "gateway", "site": "https://stripe.com",
             "mark": None, "signs": {"packages": {"npm": ["stripe"]}, "patterns": {}, "env": ["STRIPE_"],
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
    def test_build_keeps_an_entry_after_its_last_sign_is_removed(self):
        rule = {"tech": "widget", "name": "Widget", "type": "tool", "files": ["unrelated.json"]}
        correction = {"id": "widget", "wrong_signs": {"files": ["unrelated.json"]}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            additions = root / "additions.json"
            additions.write_text(json.dumps({"entries": [correction]}), encoding="utf-8")
            with (patch.object(registry_build, "stack_analyser_rules", return_value=[rule]),
                  patch.object(registry_build, "cncf_items", return_value=[]),
                  patch.object(registry_build, "_tarball", return_value=root),
                  patch.object(registry_build, "simple_icons", return_value=[])):
                (entry,) = registry_build.build(root, additions, root)["entries"]
        self.assertEqual(entry["id"], "widget")
        self.assertIsNone(entry["signs"])

    def test_specfy_file_regexp_does_not_declare_a_file_named_regex(self):
        rule = {"tech": "jest", "name": "Jest", "type": "test", "files": {"regex": r"^jest\.config\."}}
        self.assertEqual(registry_build._from_rule(rule)["signs"]["files"], [])
        rule["files"] = ["jest.config.js"]
        self.assertEqual(registry_build._from_rule(rule)["signs"]["files"], ["jest.config.js"])

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


@pytest.mark.usefixtures("real_stack")
class RecognizeTests(unittest.TestCase):
    FILES = {
        "package.json": '{"name": "root", "private": true, "workspaces": ["web", "packages/*"]}',
        "web/package.json": '{"name": "web", "dependencies": {"stripe": "1", "react": "18", "resend": "workspace:*"}}',
        "packages/resend/package.json": '{"name": "resend", "version": "1.0.0"}',
        "api/requirements.txt": "stripe==7.0\nfastapi>=0.110  # the API\n",
        "api/pay.py": "import os\n\nKEY = os.environ['STRIPE_SECRET_KEY']\n",
        "api/Dockerfile": "FROM python:3.12-slim\n",
        "telemetry/pyproject.toml": '[project]\nname = "telemetry"\ndependencies = ["sentry-sdk"]\n'
                                   '[project.optional-dependencies]\ntracing = ["sentry_sdk>=2"]\n',
        "api/known.json": '{"schema": "daodan/service-registry/v1", "entries": [{"env": ["STRIPE_KEY"]}]}',
        "web/dist.js": "var a=1;" * 2000 + "STRIPE_KEY\n",
    }

    @classmethod
    def setUpClass(cls):
        import subprocess
        import tempfile
        import snapshot
        import service_registry
        cls.work = Path(tempfile.mkdtemp(prefix="registry-"))
        project = cls.work / "project"
        for rel, text in cls.FILES.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
            subprocess.run(command, cwd=project, check=True, capture_output=True)
        manifest = cls.work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(project), "--out", str(manifest), "--no-engine", "--no-index"])
        cls.manifest = manifest

    def setUp(self):
        """What the release recognizes, once for the class: the first test runs it, with the release `real_stack` names."""
        cls = type(self)
        if not hasattr(cls, "record"):
            import technologies
            cls.found = {r["id"]: r for r in stack_recognition.run(cls.manifest)["found"]}
            cls.record = technologies.ensure(cls.manifest)
            cls.units = {u["name"]: u for u in cls.record["units"]}

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.work, True)

    def test_each_sign_says_where_it_is(self):
        signs = {(s["sign"], s["value"], s["path"], s["line"]) for s in self.found["stripe"]["signs"]}
        self.assertEqual(signs, {("package", "stripe", "web/package.json", 1), ("package", "stripe", "api/requirements.txt", 1)})
        self.assertEqual((self.found["stripe"]["source"], self.found["stripe"]["type"]), ("registry", "gateway"))

    def test_packages_files_and_images_are_recognized(self):
        for ident in ("react", "fastapi", "docker"):
            self.assertIn(ident, self.found)
        self.assertIn(("file", "Dockerfile", "api/Dockerfile"),
                      {(s["sign"], s["value"], s["path"]) for s in self.found["docker"]["signs"]})

    def test_a_package_of_the_project_is_not_external(self):
        self.assertNotIn("resend", self.found)

    def test_sentry_has_one_library_and_retains_the_declaration_with_its_version(self):
        unit = self.units["telemetry"]
        self.assertIn("sentry", unit["services"])
        self.assertEqual([(lib["id"], lib["name"], lib["version"], lib["path"], lib["line"]) for lib in unit["libraries"]],
                         [("sentry", "sentry_sdk", ">=2", "telemetry/pyproject.toml", 5)])

    def test_a_unit_holds_the_technologies_its_files_show(self):
        self.assertEqual(self.units["web"]["paths"], ["web"])
        self.assertEqual(self.units["web"]["technologies"], ["nodejs", "react", "stripe"])
        self.assertEqual(self.units["resend"]["technologies"], ["nodejs"])
        self.assertTrue({"docker", "fastapi", "stripe"} <= set(self.units["root"]["technologies"]))
        self.assertNotIn("react", self.units["root"]["technologies"])

    def test_the_record_is_read_while_fresh_and_derived_again_when_the_premap_excludes_a_file(self):
        import technologies
        self.assertEqual(technologies.state(self.manifest), "fresh")
        self.assertEqual(technologies.ensure(self.manifest), self.record)
        self.assertEqual((self.record["target"], self.record["root"] != ""), (".", True))
        ensure = technologies.premap.ensure
        technologies.premap.ensure = lambda manifest: {"excluded": [{"path": "api/requirements.txt", "why": "generated"}]}
        try:
            self.assertEqual(technologies.state(self.manifest), "stale")
            again = technologies.ensure(self.manifest)
        finally:
            technologies.premap.ensure = ensure
            technologies.path(self.manifest).unlink()
        signs = {(s["sign"], s["path"]) for e in again["technologies"] if e["id"] == "stripe" for s in e["signs"]}
        self.assertIn(("package", "api/requirements.txt"), {(s["sign"], s["path"]) for e in self.record["technologies"]
                                                           if e["id"] == "stripe" for s in e["signs"]})
        self.assertNotIn(("package", "api/requirements.txt"), signs)
        self.assertEqual(sorted(p.name for p in Path(self.manifest).parent.glob(".technologies-*")), [])

    def test_a_service_of_the_premap_is_a_sign_at_the_file_declaring_it(self):
        workflow = ".github/workflows/ci.yml"
        found = {r["id"]: r for r in stack_recognition.run(self.manifest, facts={"services": [
            {"name": "db", "image": "postgres:16-alpine", "declared_in": workflow + "#jobs.test.services.db",
             "sources": ["renovate@1"]}]})["found"]}
        self.assertEqual(found["postgresql"]["signs"], [{"sign": "package", "value": "postgres", "path": workflow,
                                                         "line": None, "strength": "declared", "source": "renovate@1"}])


HOSTILE = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ed="http://ed.example/ns"
     onload="alert(1)" width="48" height="48" viewBox="0 0 24 24">
  <script>alert(2)</script>
  <metadata>editor junk</metadata>
  <ed:namedview/>
  <foreignObject><iframe xmlns="http://www.w3.org/1999/xhtml" src="http://evil.example/"/></foreignObject>
  <defs><linearGradient id="g"><stop offset="0" stop-color="#fff"/></linearGradient></defs>
  <path id="p" d="M0 0h24v24H0z" fill="url(#g)" onclick="alert(3)" stroke="url(http://evil.example/x#y)"
        style="fill:#c00;background:url(http://evil.example/b.png)"/>
  <use href="http://evil.example/x.svg#a"/><use xlink:href="#p"/>
  <a href="javascript:alert(4)"><circle r="3"/></a>
</svg>"""
TINY = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><path d="M0 0h1z"/></svg>'


class MarkFileTests(unittest.TestCase):
    def test_the_sanitiser_keeps_the_drawing_and_nothing_that_runs_or_fetches(self):
        out = registry_build.clean_svg(HOSTILE)
        for banned in ("script", "onload", "onclick", "foreignObject", "iframe", "evil.example", "javascript", "metadata",
                       "namedview", "alert", "background"):
            self.assertNotIn(banned, out)
        for kept in ('viewBox="0 0 24 24"', 'd="M0 0h24v24H0z"', 'fill="url(#g)"', 'href="#p"', "linearGradient", "#c00"):
            self.assertIn(kept, out)
        self.assertNotIn("width=", out.split(">", 1)[0])
        self.assertEqual(registry_build.clean_svg(out.encode()), out)  # cleaning again changes nothing

    def test_a_brand_colour_goes_on_the_root_so_that_an_image_shows_it(self):
        out = registry_build.clean_svg(TINY, fill="#635BFF")
        self.assertIn('fill="#635BFF"', out.split(">", 1)[0])

    def test_a_file_that_is_not_a_small_plain_drawing_is_refused(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">%s</svg>'
        refused = {
            "a raster": svg % '<image href="data:image/png;base64,AAAA"/>',
            "text needing fonts": svg % "<text>Logo</text>",
            "a style that imports": svg % '<style>@import url("http://evil.example/a.css");</style><path d="M0 0z"/>',
            "an entity": '<!DOCTYPE svg [<!ENTITY a "aaaa">]>' + svg % "<path d='M0 0z'/>",
            "another document": '<html xmlns="http://www.w3.org/1999/xhtml"/>',
            "no size": '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0z"/></svg>',
            "not xml": "<svg",
            "too large": svg % ('<path d="M0 0z"/>' * 5000),
        }
        for why, text in refused.items():
            with self.assertRaises(ValueError, msg=why):
                registry_build.clean_svg(text.encode())
        plain = svg % "<style>.a{fill:#fff}</style><path class='a' d='M0 0z'/>"
        self.assertIn(".a{fill:#fff}", registry_build.clean_svg(plain.encode()))

    def test_check_fails_on_a_mark_file_that_is_missing_orphan_or_not_clean(self):
        entries = [{**CheckTests.ENTRY, "id": f"e{n}", "mark": f"marks/e{n}.svg"} for n in range(1000)]
        value = {"schema": registry_build.SCHEMA, "entries": entries}
        good = registry_build.clean_svg(TINY)
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "marks").mkdir()
            for entry in entries:
                (data / entry["mark"]).write_text(good, encoding="utf-8")
            self.assertEqual(registry_build.check(value, data), [])
            (data / "marks/e1.svg").unlink()
            (data / "marks/stray.svg").write_text(good, encoding="utf-8")
            (data / "marks/e2.svg").write_text(good.replace("<path", "<script/><path"), encoding="utf-8")
            problems = " ".join(registry_build.check(value, data))
            self.assertIn("e1: marks/e1.svg is missing", problems)
            self.assertIn("marks/stray.svg: no entry names this file", problems)
            self.assertIn("e2: marks/e2.svg is not what the sanitiser makes of it", problems)
        entries[0]["mark"] = "../outside.svg"
        self.assertIn("e0: mark is", " ".join(registry_build.check(value)))


class MarkJoinTests(unittest.TestCase):
    ICONS = [{"title": "Stripe", "slug": "stripe", "hex": "635BFF"},
             {"title": "Deep Lake", "slug": "activeloop", "hex": "FFB746",
              "aliases": {"dup": [{"title": "Deep Lake"}], "aka": ["Active Loop"]}},
             {"title": "Acme", "slug": "acme", "hex": "000000", "aliases": {"loc": {"it-IT": "Acme Italia"}}},
             {"title": "Neptune", "slug": "neptune", "hex": "4D5FFF"}]

    def test_names_join_by_case_punctuation_a_company_suffix_and_the_collection_s_own_aliases(self):
        index = registry_build.mark_index(self.ICONS)

        def find(name, ident="x"):
            return (registry_build.simple_icon({"id": ident, "name": name}, index) or {}).get("slug")

        self.assertEqual(find("STRIPE"), "stripe")
        self.assertEqual(find("Stripe, Inc."), "stripe")
        self.assertEqual(find("Acme Italia"), "acme")
        self.assertEqual(find("Active-Loop"), "activeloop")
        self.assertEqual(find("Deep Lake"), "activeloop")
        self.assertEqual(find("anything", "stripe"), "stripe")

    def test_the_name_of_another_vendor_s_product_is_not_the_mark_of_a_service_that_has_it_in_its_name(self):
        index = registry_build.mark_index(self.ICONS)
        self.assertIsNone(registry_build.simple_icon({"id": "aws.neptune", "name": "AWS Neptune"}, index))

    def test_apply_marks_writes_one_clean_file_per_entry_and_removes_the_files_nobody_names(self):
        entries = {"stripe": {"id": "stripe", "name": "Stripe", "mark": "marks/old.svg", "from": ["stack-analyser"]},
                   "nomark": {"id": "nomark", "name": "Nomark", "mark": "marks/stale.svg", "from": ["simple-icons"]},
                   "own": {"id": "own", "name": "Own", "mark": "marks/own.svg", "from": ["additions"]},
                   "packaged": {"id": "packaged", "name": "Packaged", "mark": None, "from": ["additions"]}}
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>Stripe</title><path d="M0 0h24z"/></svg>'
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "marks").mkdir()
            for name in ("stale", "own", "old", "orphan"):
                (data / "marks" / f"{name}.svg").write_text("<svg/>", encoding="utf-8")
            package = {"url": "https://owner.example/p.zip", "sha256": "a" * 64, "member": "A.svg", "terms": "https://owner.example/t"}
            registry_build.apply_marks(entries, self.ICONS, lambda slug: svg, data, {
                "own": {"mark": "marks/own.svg"}, "packaged": {"mark_source": package}, "stripe": {"mark_source": package}})
            self.assertEqual(entries["stripe"]["mark"], "marks/stripe.svg")
            self.assertEqual(entries["stripe"]["from"], ["simple-icons", "stack-analyser"])
            self.assertIn('fill="#635BFF"', (data / "marks/stripe.svg").read_text(encoding="utf-8"))
            self.assertIsNone(entries["nomark"]["mark"])
            self.assertEqual(entries["nomark"]["from"], [])
            self.assertEqual(entries["own"]["mark"], "marks/own.svg")
            self.assertEqual((entries["packaged"]["mark"], entries["packaged"]["mark_source"]), (None, package))
            self.assertNotIn("mark_source", entries["stripe"])  # a file and a package are two cases, never both
            self.assertEqual(sorted(p.name for p in (data / "marks").iterdir()), ["own.svg", "stripe.svg"])


class DistributedMarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.entries = cls.value["entries"]

    def test_every_mark_is_a_clean_file_in_the_plugin_and_every_file_is_named_by_an_entry(self):
        self.assertEqual(registry_build.check(self.value, DATA), [])

    def test_the_recognisable_services_that_have_a_mark_do_not_drop_below_432(self):
        """Count marked services using the category the module stack actually reports."""
        with_mark = [e for e in self.entries if service_registry.entry_category(e) == "service" and e["signs"] and e["mark"]]
        self.assertGreaterEqual(len(with_mark), 432)

    def test_a_shipped_mark_that_is_not_of_simple_icons_says_where_it_comes_from(self):
        """An owner's file: its URL and the day. A drawing of Daodan's: that it is Daodan's and the day. Both are named
        in the notices."""
        notices = NOTICES.read_text(encoding="utf-8")
        shipped = [r for r in json.loads(ADDITIONS.read_text(encoding="utf-8"))["entries"] if r.get("mark")]
        self.assertEqual(sum(r["by"] == "daodan" for r in shipped), 90)
        for record in shipped:
            source = record["mark_origin"]
            self.assertRegex(source["date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIn(f"`{record['id']}`", notices)
            if record["by"] == "daodan":
                self.assertEqual(source["drawn_by"], "Daodan", record["id"])
            else:
                self.assertTrue(source["url"].startswith("https://"), record["id"])
                self.assertIn(source["url"], notices)
            self.assertNotIn("simple-icons", next(e for e in self.entries if e["id"] == record["id"])["from"])
        packages = {r["mark_source"]["url"]: r["mark_source"] for r in json.loads(ADDITIONS.read_text(encoding="utf-8"))["entries"]
                    if r.get("mark_source")}
        for url, package in packages.items():
            for field in ("url", "sha256", "terms"):
                self.assertIn(package[field], notices, f"{field} of {url}")


class MarkFileOfAnEntryTests(unittest.TestCase):
    """`service_registry.mark_file`: the file a page shows for an entry, shipped or taken out of the owner's package."""

    def setUp(self):
        import hashlib
        import io
        import zipfile
        import preparation
        self.preparation, self.tmp = preparation, tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.calls = []
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr("Icons/Compute/Lambda.svg", HOSTILE)
            package.writestr("Icons/Big.svg", b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'>" + b"<g/>" * 40000 + b"</svg>")
        self.archive = Path(self.tmp.name) / "owner-package.zip"
        self.archive.write_bytes(buffer.getvalue())
        self.sha = hashlib.sha256(buffer.getvalue()).hexdigest()
        self.entry = {"id": "aws.lambda", "mark": None, "mark_source": {
            "url": "https://owner.example/owner-package.zip", "sha256": self.sha, "member": "Icons/Compute/Lambda.svg",
            "terms": "https://owner.example/terms"}}
        self.fetched = preparation.fetched
        preparation.fetched = self.fake
        self.addCleanup(setattr, preparation, "fetched", self.fetched)

    def fake(self, url, sha256, name):
        self.calls.append((url, sha256, name))
        return self.archive

    def with_source(self, **change):
        return {**self.entry, "mark_source": {**self.entry["mark_source"], **change}}

    def test_a_shipped_mark_is_the_file_in_the_plugin(self):
        path = service_registry.mark_file({"id": "stripe", "mark": "marks/stripe.svg", "mark_source": None})
        self.assertEqual(path, DATA / "marks/stripe.svg")
        self.assertIsNone(service_registry.mark_file({"id": "x", "mark": "marks/not-there.svg"}))
        self.assertIsNone(service_registry.mark_file({"id": "x", "mark": None}))

    def test_a_package_mark_is_downloaded_through_the_verified_download_and_comes_out_clean(self):
        path = service_registry.mark_file(self.entry)
        self.assertEqual(self.calls, [("https://owner.example/owner-package.zip", self.sha, "owner-package.zip")])
        self.assertEqual(path.parent.parent, self.archive.parent)  # beside the package in the shared cache
        text = path.read_text(encoding="utf-8")
        self.assertEqual(registry_build.clean_svg(HOSTILE), text)
        for banned in ("script", "onload", "evil.example"):
            self.assertNotIn(banned, text)
        self.assertEqual(service_registry.mark_file(self.entry), path)  # again: the file is there

    def test_any_failure_is_no_mark_never_an_error(self):
        import container

        def refused(url, sha256, name):
            raise container.Gap("could not be downloaded", "check the network")

        cases = {
            "member that leaves the package": self.with_source(member="../Lambda.svg"),
            "member that is not there": self.with_source(member="Icons/Nothing.svg"),
            "member that is too large": self.with_source(member="Icons/Big.svg"),
            "member that is not an svg": self.with_source(member="Icons/Compute/Lambda.png"),
            "package that is not the one pinned": self.with_source(sha256="0" * 64),
            "package without a member": {**self.entry, "mark_source": {"url": "https://owner.example/p.zip"}},
        }
        for why, entry in cases.items():
            self.assertIsNone(service_registry.mark_file(entry), why)
        self.preparation.fetched = refused
        self.assertIsNone(service_registry.mark_file(self.entry), "download that fails")
        self.archive.write_bytes(b"not a zip")
        self.preparation.fetched = self.fake
        self.assertIsNone(service_registry.mark_file(self.with_source(sha256=__import__("hashlib").sha256(b"not a zip").hexdigest())), "not a zip")


class PackageMarkTests(unittest.TestCase):
    def test_check_knows_the_two_shapes_and_refuses_both_at_once_and_an_unsafe_member(self):
        package = {"url": "https://owner.example/p.zip", "sha256": "a" * 64, "member": "Icons/A.svg",
                   "terms": "https://owner.example/terms"}

        def problems(**change):
            entries = [{**CheckTests.ENTRY, "id": f"e{n}", "mark": None} for n in range(1000)]
            entries[0].update({"mark_source": package, **change})
            return " ".join(registry_build.check({"schema": registry_build.SCHEMA, "entries": entries}))

        self.assertEqual(problems(), "")
        self.assertIn("e0: mark and mark_source are two cases", problems(mark="marks/e0.svg"))
        for bad in ({**package, "member": "../A.svg"}, {**package, "member": "/etc/a.svg"}, {**package, "sha256": "xyz"},
                    {**package, "url": "http://owner.example/p.zip"}, {**package, "terms": "owner terms"}, {"url": "https://a.b/c"}):
            self.assertIn("e0: mark_source is", problems(mark_source=bad))

    def test_add_package_mark_records_the_hash_of_the_package_and_keeps_nothing_of_it(self):
        import io
        import zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr("Icons/A.svg", registry_build.clean_svg(TINY))
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            entries = [{**CheckTests.ENTRY, "id": f"e{n}", "mark": None} for n in range(1000)]
            entries[0]["id"] = "aws.x"
            registry = {"schema": registry_build.SCHEMA, "entries": entries}
            (data / "service-registry.json").write_text(json.dumps(registry), encoding="utf-8")
            (data / "registry-additions.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
            (data / "p.zip").write_bytes(buffer.getvalue())
            args = ("aws.x", "https://owner.example/p.zip", data / "p.zip", "Icons/A.svg", "https://owner.example/terms",
                    data / "service-registry.json", data / "registry-additions.json")
            self.assertEqual(registry_build.add_package_mark(*args), 0)
            written = json.loads((data / "service-registry.json").read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(written["mark_source"]["member"], "Icons/A.svg")
            self.assertEqual(len(written["mark_source"]["sha256"]), 64)
            self.assertFalse((data / "marks").exists())
            self.assertEqual(registry_build.add_package_mark("aws.x", args[1], args[2], "Icons/Nothing.svg", *args[4:]), 1)

    def test_a_mark_daodan_drew_takes_the_place_of_the_package_and_says_so(self):
        """A service whose mark was fetched from its owner's package gets a file Daodan drew: the entry names the file
        and no package, and the additions keep one record of its mark, Daodan's, with the day and no owner's URL."""
        import io
        import zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr("Icons/A.svg", registry_build.clean_svg(TINY))
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            entries = [{**CheckTests.ENTRY, "id": f"e{n}", "mark": None} for n in range(1000)]
            entries[0]["id"] = "aws.x"
            files = (data / "service-registry.json", data / "registry-additions.json")
            files[0].write_text(json.dumps({"schema": registry_build.SCHEMA, "entries": entries}), encoding="utf-8")
            files[1].write_text(json.dumps({"entries": []}), encoding="utf-8")
            (data / "p.zip").write_bytes(buffer.getvalue())
            (data / "drawn.svg").write_bytes(TINY)
            self.assertEqual(registry_build.add_package_mark("aws.x", "https://owner.example/p.zip", data / "p.zip",
                                                             "Icons/A.svg", "https://owner.example/terms", *files), 0)
            self.assertEqual(registry_build.add_mark("aws.x", data / "drawn.svg", None, None, *files, own=True), 0)
            written = json.loads(files[0].read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual((written["id"], written["mark"], written.get("mark_source")), ("aws.x", "marks/aws.x.svg", None))
            self.assertTrue((data / "marks/aws.x.svg").is_file())
            records = [r for r in json.loads(files[1].read_text(encoding="utf-8"))["entries"] if r["id"] == "aws.x"]
            self.assertEqual([(r["by"], r.get("mark"), "mark_source" in r, sorted(r["mark_origin"])) for r in records],
                             [("daodan", "marks/aws.x.svg", False, ["date", "drawn_by"])])


class NewServiceFromAMarkTests(unittest.TestCase):
    ICONS = MarkJoinTests.ICONS
    OWNERS = {"acme": {"github.com/acme"}, "acme-py": {"github.com/acme"}, "acme-known": {"github.com/acme"},
              "acme-other": {"github.com/other"}}
    CHECK = {"owners": lambda eco, name: NewServiceFromAMarkTests.OWNERS.get(name), "site": lambda url: "ok" in url}

    def test_the_prompt_lists_the_marks_that_have_no_entry_and_no_other(self):
        registry = {"entries": [{"id": "stripe", "name": "Stripe", "kind": "service", "from": []}]}
        prompt = registry_build.model_input(registry, self.ICONS)
        lines = prompt.splitlines()
        self.assertIn("Acme", lines)
        self.assertNotIn("Stripe", lines)

    def test_a_new_entry_is_kept_with_packages_of_one_owner_and_no_package_another_entry_has(self):
        entries = {"known": {"id": "known", "name": "Known", "signs": {"packages": {"npm": ["acme-known"]}}}}

        def one(**change):
            proposal = {"id": "acme", "name": "Acme", "kind": "service", "type": "servizio o API", "site": "https://ok.example",
                        "packages": {"npm": ["acme"], "pypi": ["acme-py"]}}
            return registry_build.accept([{**proposal, **change}], entries, self.CHECK)

        kept, refused = one()
        self.assertEqual((kept[0]["id"], kept[0]["signs"]["packages"], refused), ("acme", {"npm": ["acme"], "pypi": ["acme-py"]}, []))
        kept, refused = one(packages={"npm": ["acme"], "pypi": ["acme-other"]})
        self.assertEqual(kept[0]["signs"]["packages"], {"npm": ["acme"]})
        self.assertIn("another owner", " ".join(refused))
        kept, refused = one(packages={"npm": ["acme-known"]})
        self.assertEqual(kept, [])
        self.assertIn("already has", " ".join(refused))
        kept, refused = one(site="https://down.example")
        self.assertEqual(kept, [])


def test_a_record_that_only_adds_to_an_entry_may_come_before_the_one_that_makes_it():
    """`build` applies the additions in the order of their file, by id and by `by`: a `catalog` record that only gives
    a category comes before the `model` record that makes the entry, and the entry is made all the same."""
    entries: dict = {}
    registry_build.apply_additions(entries, [
        {"id": "new", "category": "library", "by": "catalog"},
        {"id": "new", "name": "New", "kind": "project", "type": "altro", "site": "https://new.example",
         "signs": {"packages": {"npm": ["new"]}}, "by": "model"}])
    assert (entries["new"]["name"], entries["new"]["category"]) == ("New", "library")
    assert entries["new"]["signs"]["packages"] == {"npm": ["new"]}
