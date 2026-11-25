"""Registry of external services and projects: the distributed file and the rules that build it."""

import contextlib
import copy
import io
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
import stack_analyser  # noqa: E402
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

    def test_every_entry_says_its_support_from_its_rule_and_the_readers(self):
        self.assertEqual([e["id"] for e in self.value["entries"] if e.get("support") != registry_build.support(e)], [])
        for ident, level in (("nextjs", "full"), ("stripe", "full"), ("boto3", "full"), ("docker", "full"),
                             ("django", "partial"),
                             ("sqlalchemy", "partial"), ("temporal", "none")):
            self.assertEqual((ident, self.entries[ident]["support"]), (ident, level))
        for ident, module in registry_build.READERS.items():
            self.assertTrue((SCRIPTS / module).is_file(), module)
            self.assertIn("stack-analyser", self.entries[ident]["from"], ident)
        wrong = {**self.entries["django"], "support": "full"}
        self.assertIn("django: support is partial", " ".join(registry_build.check(
            {"schema": registry_build.SCHEMA, "entries": [wrong]})))

    def test_it_knows_the_common_ones(self):
        self.assertEqual(self.entries["telegram"]["hosts"], ["api.telegram.org"])
        for ident in ("mongodb", "fastapi", "react", "docker", "stripe"):
            self.assertIn(ident, self.entries)
        self.assertEqual(self.entries["stripe"]["mark"], "marks/stripe.svg")

    def test_no_entry_comes_from_webappanalyzer(self):
        sources = {source for entry in self.entries.values() for source in entry["from"]}
        self.assertLessEqual(sources, set(registry_build.SOURCES))
        self.assertNotIn("webappanalyzer", json.dumps(self.value).lower())

    def test_it_is_the_register_of_names_of_the_release_in_use(self):
        """The rules are the fork's: an entry carries no sign, and the release that made the file is the one pinned."""
        self.assertEqual(self.value["versions"]["stack-analyser"], stack_analyser.VERSION)
        self.assertEqual([i for i, e in self.entries.items() if "signs" in e], [])

    def test_a_category_is_the_entry_s_own_field_never_its_name(self):
        for ident, category in (("eslint", "tool"), ("docker", "tool"), ("renovate", "tool"), ("nodejs", "tool"),
                                ("cypressci", "tool"), ("opentelemetry", "library"), ("playwright", "tool")):
            self.assertEqual((ident, self.entries[ident].get("category")), (ident, category))
        self.assertEqual(service_registry.entry_category({"id": "eslint", "kind": "project"}), "framework")
        self.assertEqual(service_registry.entry_category({"id": "playwright", "kind": "service"}), "service")
        self.assertEqual(service_registry.entry_category({"id": "x", "kind": "service", "category": "tool"}), "tool")

    def test_every_entry_with_a_rule_has_its_category_written_and_none_is_a_framework_by_default(self):
        """The curated one from the additions, else the one of its rule's type (`CATEGORY_OF_TYPE`)."""
        self.assertEqual([i for i, e in self.entries.items() if "stack-analyser" in e["from"] and not e.get("category")], [])
        for category, idents in (("framework", ("angular", "django", "express", "nextjs")),
                                 ("library", ("numpy", "sqlalchemy", "d3js", "fontawesome")),
                                 ("tool", ("jest", "biomejs", "ansible", "asdf", "alembic")),
                                 ("service", ("apache_kafka", "etcd", "keycloak", "boto3"))):  # boto3: the client of a service
            for ident in idents:
                self.assertEqual((ident, self.entries[ident].get("category")), (ident, category))

    def test_a_renamed_rule_leaves_no_entry_under_its_old_id_and_its_curated_data_moves_with_it(self):
        """The fork's renames (`react-email`, `kafka`, `vault`): the old id is no entry, the new one has what was curated."""
        self.assertEqual({"react-email", "kafka", "vault"} & self.entries.keys(), set())
        self.assertEqual(self.entries["reactemail"]["site"], "https://react.email")
        self.assertEqual(self.entries["hashicorp_vault"]["type"], "servizio o API")
        self.assertIn("cncf-landscape", self.entries["apache_kafka"]["from"])

    def test_the_built_file_is_what_its_additions_make_of_it(self):
        """The checked-in file agrees with `registry-additions.json` by the build's own merge rule."""
        entries = copy.deepcopy(self.entries)
        registry_build.apply_additions(entries, json.loads(ADDITIONS.read_text(encoding="utf-8"))["entries"])
        self.assertEqual(entries, self.entries)

    def test_the_additions_hold_no_sign(self):
        records = json.loads(ADDITIONS.read_text(encoding="utf-8"))["entries"]
        self.assertEqual(registry_build.check(self.value, additions=records), [])


def test_every_rule_of_the_release_has_a_registry_entry(real_stack):
    """What the fork recognizes the registry names: its id, name, type and hosts, from the release in use."""
    entries = {e["id"]: e for e in json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]}
    rules = stack_analyser.catalogue()
    assert len(rules) > 1000
    assert [r["tech"] for r in rules if r["tech"] not in entries] == []
    for rule in rules:
        entry = entries[rule["tech"]]
        assert "stack-analyser" in entry["from"], rule["tech"]
        assert entry.get("hosts") == (rule.get("hosts") or None), rule["tech"]
        assert entry.get("category"), rule["tech"]


def test_the_table_of_categories_has_every_type_of_the_catalogue(real_stack):
    types = {rule["type"] for rule in stack_analyser.catalogue()}
    assert sorted(types - set(registry_build.CATEGORY_OF_TYPE)) == []
    assert set(registry_build.CATEGORY_OF_TYPE.values()) <= set(registry_build.CATEGORIES)


class CheckTests(unittest.TestCase):
    ENTRY = {"id": "stripe", "name": "Stripe", "kind": "service", "type": "gateway", "site": "https://stripe.com",
             "mark": None, "hosts": ["api.stripe.com"], "from": ["stack-analyser"]}

    def problems(self, change, size=1000, additions=None):
        entries = []
        for number in range(size):
            entry = copy.deepcopy(self.ENTRY)
            entry["id"] = f"e{number}"
            entries.append(entry)
        change(entries)
        return registry_build.check({"schema": registry_build.SCHEMA, "entries": entries}, additions=additions)

    def test_each_rule_names_what_breaks_it(self):
        self.assertEqual(self.problems(lambda e: None), [])
        self.assertIn("1000", " ".join(self.problems(lambda e: None, size=999)))
        self.assertIn("e0: the id repeats", " ".join(self.problems(lambda e: e[1].update(id="e0"))))
        self.assertIn("type", " ".join(self.problems(lambda e: e[0].update(type="pagamento"))))
        self.assertIn("hosts", " ".join(self.problems(lambda e: e[0].update(hosts=[]))))
        self.assertIn("hosts", " ".join(self.problems(lambda e: e[0].update(hosts="api.stripe.com"))))
        self.assertEqual(self.problems(lambda e: e[0].pop("hosts")), [])
        self.assertIn("kind", " ".join(self.problems(lambda e: e[0].update(kind="vendor"))))

    def test_a_sign_is_refused_in_an_entry_and_in_the_additions(self):
        """The rules are the fork's: the registry names, it does not recognize."""
        self.assertIn("e0: no signs", " ".join(self.problems(lambda e: e[0].update(signs={"packages": {"npm": ["stripe"]}}))))
        self.assertIn("e0: no signs", " ".join(self.problems(lambda e: e[0].update(signs=None))))
        for field in ("signs", "wrong_signs"):
            found = self.problems(lambda e: None, additions=[{"id": "stripe", "by": "catalog", field: {"files": ["x"]}}])
            self.assertEqual(found, [f"additions: stripe has {field}, the rules are the fork's"])
        self.assertEqual(self.problems(lambda e: None, additions=[{"id": "stripe", "category": "service", "by": "catalog"}]), [])


class BuildTests(unittest.TestCase):
    RULES = [{"tech": "widget", "name": "Widget", "type": "linter", "files": ["unrelated.json"],
              "dependencies": [{"type": "npm", "name": "widget"}]},
             {"tech": "payhub", "name": "PayHub", "type": "payment", "hosts": ["api.payhub.test"]},
             {"tech": "kernel", "name": "Kernel", "type": "framework"}]

    def build(self, records, rules=None, items=()):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            additions = root / "additions.json"
            additions.write_text(json.dumps({"entries": records}), encoding="utf-8")
            with (patch.object(registry_build.stack_analyser, "catalogue", return_value=self.RULES if rules is None else rules),
                  patch.object(registry_build, "cncf_items", return_value=list(items)),
                  patch.object(registry_build, "_tarball", return_value=root),
                  patch.object(registry_build, "simple_icons", return_value=[])):
                return registry_build.build(root, additions, root)

    def test_an_entry_is_made_of_a_rule_with_its_hosts_its_category_and_no_sign(self):
        value = self.build([])
        entries = {e["id"]: e for e in value["entries"]}
        self.assertEqual(entries["widget"], {"id": "widget", "name": "Widget", "kind": "project", "type": "altro",
                                             "site": None, "mark": None, "from": ["stack-analyser"], "category": "tool",
                                             "support": "full"})
        self.assertEqual((entries["payhub"]["kind"], entries["payhub"]["type"], entries["payhub"]["category"],
                          entries["payhub"]["hosts"]), ("service", "gateway", "service", ["api.payhub.test"]))
        self.assertNotIn("hosts", entries["kernel"])
        self.assertEqual(value["versions"]["stack-analyser"], stack_analyser.VERSION)
        self.assertEqual([i for i, e in entries.items() if "signs" in e], [])

    def test_the_curated_category_is_kept_and_the_table_decides_only_where_there_is_none(self):
        entries = {e["id"]: e for e in self.build([{"id": "widget", "category": "library", "by": "catalog"}])["entries"]}
        self.assertEqual((entries["widget"]["category"], entries["kernel"]["category"]), ("library", "framework"))

    def test_an_entry_the_fork_has_no_rule_for_stays_as_a_name(self):
        record = {"id": "legacy", "name": "Legacy", "kind": "project", "type": "altro", "site": "https://legacy.test",
                  "category": "tool", "by": "model"}
        entry = next(e for e in self.build([record], rules=[])["entries"] if e["id"] == "legacy")
        self.assertEqual((entry["from"], entry["category"], "hosts" in entry), (["additions"], "tool", False))

    def test_a_cncf_item_the_additions_name_for_an_entry_joins_it(self):
        """A name the CNCF Landscape writes otherwise than the rule (`Kafka`, `Apache Kafka`) joins the entry whose record
        names it (`cncf`), instead of making an entry of its own."""
        item = {"name": "Wdgt", "category": "App Definition", "subcategory": "Streaming & Messaging",
                "homepage_url": "https://widget.test"}
        entries = {e["id"]: e for e in self.build([{"id": "widget", "cncf": "Wdgt", "by": "catalog"}], items=[item])["entries"]}
        self.assertNotIn("wdgt", entries)
        self.assertEqual((entries["widget"]["site"], entries["widget"]["from"]),
                         ("https://widget.test", ["additions", "cncf-landscape", "stack-analyser"]))

    def test_a_type_the_table_does_not_know_stops_the_build_with_its_name(self):
        with self.assertRaisesRegex(ValueError, "gizmo"):
            self.build([], rules=[{"tech": "x", "name": "X", "type": "gizmo"}])

    def test_the_commands_that_wrote_signs_are_gone(self):
        for command in ("derive", "verify-additions", "model-input", "accept"):
            with self.subTest(command), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                registry_build.main([command])
        for name in ("_COLLECT", "stack_analyser_rules", "derive", "accept", "verify_additions", "model_input", "STACK_ANALYSER"):
            self.assertFalse(hasattr(registry_build, name), name)


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
        # the release reads each file by itself (no line) and is given the pre-map's declarations: both stay, each with
        # its source (the source's name, the label up to `@`)
        signs = {(s["sign"], s["value"], s["path"], s["line"], s["source"].partition("@")[0])
                 for s in self.found["stripe"]["signs"]}
        self.assertEqual(signs, {("package", "stripe", "web/package.json", 1, "modules.py"),
                                 ("package", "stripe", "web/package.json", None, "stack-analyser"),
                                 ("package", "stripe", "api/requirements.txt", 1, "requirements"),
                                 ("package", "stripe", "api/requirements.txt", None, "stack-analyser")})
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
        with_mark = [e for e in self.entries if service_registry.entry_category(e) == "service"
                     and "stack-analyser" in e["from"] and e["mark"]]
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


def test_a_record_that_only_adds_to_an_entry_may_come_before_the_one_that_makes_it():
    """`build` applies the additions in the order of their file, by id and by `by`: a `catalog` record that only gives
    a category comes before the `model` record that makes the entry, and the entry is made all the same."""
    entries: dict = {}
    registry_build.apply_additions(entries, [
        {"id": "new", "category": "library", "by": "catalog"},
        {"id": "new", "name": "New", "kind": "project", "type": "altro", "site": "https://new.example",
         "by": "model"}])
    assert (entries["new"]["name"], entries["new"]["category"]) == ("New", "library")
