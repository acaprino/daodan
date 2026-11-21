"""The explorer's envelope `daodan/visual@1`: structure, memberships, states, flows and node types."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "daodan/core"
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


def test_payload_bytes_for_ten_distinct_inspectors_and_one_source_edit(tmp_path, monkeypatch):
    import app as launcher
    import pytest
    import store_graph
    from collections import Counter

    project = tmp_path / "project"
    project.mkdir()
    files = {project / f"file{i}.py": f"def item{i}():\n    return {i}\n".encode() for i in range(10)}
    for path, data in files.items():
        path.write_bytes(data)
    git_project(project)
    service = mcp_service.MapService(project)
    service.create_run(".", "ten", engine=False)
    app = launcher.App(tmp_path / "app", environment={})
    app.service, app.context = service, {"run_id": "ten", "path": str(project)}
    store_graph._file_identity.cache_clear()
    original = Path.open
    reads = Counter()

    def counted(path, *args, **kwargs):
        handle = original(path, *args, **kwargs)
        if path in files and "r" in handle.mode:
            read = handle.read

            def read_payload(*size):
                data = read(*size)
                reads[path.name] += len(data)
                return data
            handle.read = read_payload
        return handle

    monkeypatch.setattr(Path, "open", counted)
    cacheable = all(store_graph.source_stamp(path)[1] and store_graph.source_stamp(path)[4] for path in files)
    try:
        first, *other = files
        app.symbols({"file": "file:" + first.name})
        expected = {path.name: len(data) for path, data in files.items()}
        if cacheable:
            assert reads == expected
        reads.clear()
        for path in other:
            app.symbols({"file": "file:" + path.name})
        if cacheable:
            assert not reads
        reads.clear()
        app.symbols({"file": "file:" + first.name})
        if cacheable:
            assert not reads
        # The edited file can supply incoming calls to a different inspector that is already kept.
        changed = other[-1]
        changed.write_bytes(files[changed].replace(b"return 9", b"return 0"))
        with pytest.raises(ValueError, match="identity changed"):
            app.symbols({"file": "file:" + first.name})
        if cacheable:
            assert reads == {changed.name: len(files[changed])}
    finally:
        app.close()


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

    def test_the_technologies_of_the_stack_step_and_of_each_build_unit(self):
        (self.project / "requirements.txt").write_text("fastapi==0.110\n", encoding="utf-8")
        git_project(self.project)
        self.service.create_run(".", "r2", engine=False)
        envelope = visual.build_envelope(self.project / ".daodan/map/runs/r2")
        found = {item["id"]: item for item in envelope["technologies"]}
        self.assertEqual((found["fastapi"]["name"], found["fastapi"]["paths"]), ("FastAPI", ["requirements.txt"]))
        unit = next(entity for entity in envelope["entities"] if entity["ref"].startswith("build:"))
        self.assertIn("fastapi", unit["technologies"])

    def test_structure_states_and_shared_membership(self):
        envelope = self.envelope
        self.assertEqual(envelope["schema"], "daodan/visual@1")
        refs = {entity["ref"]: entity for entity in envelope["entities"]}
        self.assertIn("imports:file:src/app/a.py->file:src/app/b.py", {relation["ref"] for relation in envelope["relations"]})
        # a call the snapshot resolved to a callable of another file is a relation between the two files
        called = next(relation for relation in envelope["relations"]
                      if relation["ref"] == "calls:file:src/app/a.py->file:src/app/b.py")
        self.assertEqual((called["source"], called["target"], called["counts"], called["evidence"]),
                         ("file:src/app/a.py", "file:src/app/b.py", {"calls": 1}, [{"path": "src/app/a.py", "line": 5}]))
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

    def test_inspecting_another_file_reuses_hashes_and_detects_a_changed_source(self):
        import store_graph
        run = self.project / ".daodan/map/runs/r1"
        unrelated = self.project / "codebase-modules.json"
        visual.file_symbols(run, "src/app/a.py")
        reads = []
        original = Path.read_bytes

        def counted(path):
            reads.append(path)
            return original(path)

        with mock.patch.object(Path, "read_bytes", counted):
            visual.file_symbols(run, "src/app/b.py")
        if store_graph.source_stamp(unrelated)[4]:
            self.assertNotIn(unrelated, reads)
        stamp = unrelated.stat()
        data = original(unrelated).replace(b"Runs the job", b"Runs the app")
        self.assertNotEqual(data, original(unrelated))
        unrelated.write_bytes(data)
        os.utime(unrelated, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, "identity changed"):
            visual.file_symbols(run, "src/app/a.py")

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


class LinkRelationTests(unittest.TestCase):
    """A deduced link is a relation between the files of its two sides, which the graph lifts to their groups."""

    @classmethod
    def setUpClass(cls):
        pets = ROOT / "benchmarks/connection-points/fixtures/pets"
        cls.project = Path(tempfile.mkdtemp(prefix="map-visual-links-")).resolve()
        shutil.copytree(pets / "app", cls.project, dirs_exist_ok=True)
        files = {"web/package.json": '{"name": "web", "version": "1.0.0"}\n',
                 "server/pyproject.toml": '[project]\nname = "server"\nversion = "0.1.0"\n',
                 "worker/pyproject.toml": '[project]\nname = "worker"\nversion = "0.1.0"\n',
                 "server/cache.py": 'def remember(dogs):\n    cache.set("dogs", dogs)\n',
                 "worker/job.py": 'def report():\n    return cache.get("dogs")\n'}
        for rel, text in files.items():
            (cls.project / rel).parent.mkdir(parents=True, exist_ok=True)
            (cls.project / rel).write_text(text, encoding="utf-8")
        git_project(cls.project)
        service = mcp_service.MapService(cls.project)
        service.create_run(".", "links", engine=False)
        run = cls.project / ".daodan/map/runs/links"
        cls.before = visual.build_envelope(run)
        rules = json.loads((pets / "rules.json").read_text(encoding="utf-8"))["rules"]
        rules += [{"written": "cache.set", "in": ["server"], "link": "scrive", "store": "cache", "key": "arg0"},
                  {"written": "cache.get", "in": ["worker"], "link": "legge", "store": "cache", "key": "arg0"}]
        service.flows("links", rules=rules)
        cls.after = visual.build_envelope(run)
        visual.validate_envelope(cls.after)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.project, True)

    def deduced(self, envelope):
        return {item["key"]: item for item in envelope["relations"] if item.get("origin") == "dedotto"}

    def group_of(self, graph, path):
        return next(node["id"] for node in graph["nodes"] if path in node["files"])

    def test_a_route_call_is_a_relation_with_its_key_both_sides_and_a_count(self):
        found = self.deduced(self.after)
        dog = found["api GET /api/dogs/{}"]
        self.assertEqual({k: dog[k] for k in ("kind", "source", "target", "status", "link_type", "counts")},
                         {"kind": "calls", "source": "file:web/api.ts", "target": "file:server/app.py",
                          "status": "confirmed", "link_type": "rest", "counts": {"calls": 1}})
        self.assertEqual(dog["evidence"], [{"path": "web/api.ts", "line": 10}, {"path": "server/app.py", "line": 11}])
        self.assertIn("api GET /api/dogs", found)
        graph = visual_app_graph(self.after)
        web, server = self.group_of(graph, "web/api.ts"), self.group_of(graph, "server/app.py")
        self.assertNotEqual(web, server)
        edge = next(edge for edge in graph["edges"] if (edge["source"], edge["target"], edge["status"]) == (web, server, "confirmed"))
        self.assertEqual(edge["counts"], {"calls": 2})
        self.assertIn({"kind": "calls", "path": "web/api.ts", "line": 10, "key": "api GET /api/dogs/{}"}, edge["evidence"])
        self.assertIn({"kind": "calls", "path": "server/app.py", "line": 11, "key": "api GET /api/dogs/{}"}, edge["evidence"])

    def test_without_modules_the_relation_is_between_directories_and_a_store_is_no_group(self):
        kept = [item for item in self.after["entities"] if item["type"] in ("file", "directory", "symbol", "store")]
        store = {"ref": "store:cache/cats", "type": "store", "name": "cache/cats"}
        graph = visual_app_graph({**self.after, "entities": [*kept, store]})
        self.assertEqual(graph["grouping"], "directories")
        self.assertIn(("directory:web", "directory:server", {"calls": 2}),
                      [(edge["source"], edge["target"], edge["counts"]) for edge in graph["edges"]])

    def test_without_rules_no_relation_is_deduced_and_the_graph_is_the_same(self):
        self.assertEqual(self.deduced(self.before), {})
        plain = [item for item in self.after["relations"] if item.get("origin") != "dedotto"]
        self.assertEqual(visual_app_graph({**self.after, "relations": plain})["edges"], visual_app_graph(self.before)["edges"])

    def test_an_uncertain_link_is_a_relation_marked_uncertain_never_counted_as_certain(self):
        breed = self.deduced(self.after)["api GET /api/breeds/{}"]
        self.assertEqual((breed["status"], breed["counts"], breed["target"]), ("uncertain", {"calls": 1}, "file:server/app.py"))
        self.assertEqual(breed["evidence"], [{"path": "web/api.ts", "line": 15}, {"path": "server/app.py", "line": 16},
                                             {"path": "server/app.py", "line": 21}])
        graph = visual_app_graph(self.after)
        web, server = self.group_of(graph, "web/api.ts"), self.group_of(graph, "server/app.py")
        between = {edge["status"]: edge["counts"] for edge in graph["edges"] if (edge["source"], edge["target"]) == (web, server)}
        self.assertEqual(between, {"confirmed": {"calls": 2}, "uncertain": {"calls": 1}})
        self.assertNotIn("api GET /api/health", self.deduced(self.after))  # a route nobody calls is a single side

    def test_a_store_written_in_one_module_and_read_in_another_is_a_relation(self):
        dogs = self.deduced(self.after)["cache/dogs"]
        self.assertEqual({k: dogs[k] for k in ("kind", "source", "target", "status", "link_type", "counts", "evidence")},
                         {"kind": "reads", "source": "file:worker/job.py", "target": "file:server/cache.py",
                          "status": "confirmed", "link_type": "store", "counts": {"reads": 1},
                          "evidence": [{"path": "worker/job.py", "line": 2}, {"path": "server/cache.py", "line": 2}]})
        graph = visual_app_graph(self.after)
        worker, server = self.group_of(graph, "worker/job.py"), self.group_of(graph, "server/cache.py")
        self.assertIn((worker, server, {"reads": 1}), [(e["source"], e["target"], e["counts"]) for e in graph["edges"]])


class ServiceNodeTests(unittest.TestCase):
    """A service the stack recognises is an external node with its name, type and mark, used by the files that show
    it; a framework is the stack of a module, not a node, and a service only mentioned in a line is no node."""

    MANIFEST = ('{\n  "name": "shop",\n  "version": "1.0.0",\n  "dependencies": {\n    "express": "^4.18.0",\n'
                '    "stripe": "^14.0.0",\n    "@adobe/aio-lib-analytics": "^3.0.0"\n  }\n}\n')

    @classmethod
    def setUpClass(cls):
        cls.project = Path(tempfile.mkdtemp(prefix="map-visual-services-")).resolve()
        files = {"package.json": cls.MANIFEST,
                 "src/pay.js": 'const stripe = require("stripe")(process.env.STRIPE_SECRET_KEY);\nmodule.exports = stripe;\n',
                 "src/config.js": "module.exports = { key: process.env.FIREBASE_API_KEY };\n"}
        for rel, text in files.items():
            (cls.project / rel).parent.mkdir(parents=True, exist_ok=True)
            (cls.project / rel).write_text(text, encoding="utf-8")
        git_project(cls.project)
        mcp_service.MapService(cls.project).create_run(".", "services", engine=False)
        run = cls.project / ".daodan/map/runs/services"
        import technologies
        cls.stack = technologies.ensure(resolve_run_snapshot(run, json.loads((run / "state.json").read_text(encoding="utf-8"))))
        cls.envelope = visual.build_envelope(run)
        visual.validate_envelope(cls.envelope)
        cls.refs = {item["ref"]: item for item in cls.envelope["entities"]}
        cls.line = cls.MANIFEST.splitlines().index('    "stripe": "^14.0.0",') + 1

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.project, True)

    def test_a_declared_service_is_an_external_node_used_by_the_file_that_declares_it(self):
        stripe = self.refs["external:stripe"]
        self.assertEqual({k: stripe.get(k) for k in ("type", "name", "location", "node_type", "mark", "provenance")},
                         {"type": "external", "name": "Stripe", "location": "external", "node_type": "gateway",
                          "mark": "stripe", "provenance": "registry"})
        self.assertEqual(stripe["evidence"], [{"path": "package.json", "line": self.line}])
        stack_entry = next(item for item in self.envelope["technologies"] if item["id"] == "stripe")
        self.assertEqual(stack_entry["paths"], ["package.json"])
        uses = {item["ref"]: item for item in self.envelope["relations"] if item["kind"] == "uses"}
        declared = uses["uses:file:package.json->external:stripe"]
        self.assertEqual((declared["status"], declared["counts"], declared["evidence"]),
                         ("confirmed", {"uses": 1}, [{"path": "package.json", "line": self.line}]))
        # a line that names it, in a file that does not declare it, is a use the graph keeps uncertain
        mentioned = uses["uses:file:src/pay.js->external:stripe uncertain"]
        self.assertEqual((mentioned["status"], mentioned["evidence"]), ("uncertain", [{"path": "src/pay.js", "line": 1}]))

    def test_the_app_graph_draws_the_node_beside_the_groups_used_by_the_group_of_each_file(self):
        graph = visual_app_graph(self.envelope)
        self.assertEqual(graph["grouping"], "directories")  # an external node is no group of files
        nodes = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual({k: nodes["external:stripe"][k] for k in ("name", "kind", "location", "node_type", "mark", "files")},
                         {"name": "Stripe", "kind": "external", "location": "external", "node_type": "gateway",
                          "mark": "stripe", "files": []})
        uses = {(edge["source"], edge["target"], edge["status"]): edge for edge in graph["edges"] if "uses" in edge["counts"]}
        self.assertEqual(uses[("directory:.", "external:stripe", "confirmed")]["evidence"],
                         [{"kind": "uses", "path": "package.json", "line": self.line}])
        self.assertEqual(uses[("directory:src", "external:stripe", "uncertain")]["counts"], {"uses": 1})

    def test_an_entry_without_a_mark_is_a_node_all_the_same_with_no_image_to_ask(self):
        adobe = self.refs["external:adobe.analytics"]
        self.assertEqual((adobe["name"], adobe["location"], adobe.get("mark")), ("Adobe Analytics", "external", None))
        self.assertIn("uses:file:package.json->external:adobe.analytics", {item["ref"] for item in self.envelope["relations"]})

    def test_a_framework_or_a_library_is_no_node(self):
        externals = {ref for ref, item in self.refs.items() if item["type"] == "external"}
        self.assertIn("express", {item["id"] for item in self.envelope["technologies"]})  # the stack has it
        self.assertEqual(externals, {"external:stripe", "external:adobe.analytics"})

    def test_a_service_only_mentioned_in_a_line_is_no_node(self):
        self.assertIn("firebase", {item["id"] for item in self.stack["mentioned"]})  # the stack keeps it apart
        self.assertNotIn("external:firebase", self.refs)
        self.assertNotIn("firebase", {item["target"].removeprefix("external:") for item in self.envelope["relations"]})


def visual_app_graph(envelope):
    import app_view
    return app_view.graph(envelope)


if __name__ == "__main__":
    unittest.main()
