"""Tests for the shared verified lexical + Jedi edge view (P1)."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_edges
import snapshot
from snapshot_store import open_snapshot


class Definition:
    def __init__(self, module_path, name, *, kind="function", line=2, column=8):
        self.module_path = module_path
        self.name = name
        self.type = kind
        self.line = line
        self.column = column


class StubEngine:
    name = "stub"

    def __init__(self, answers=None, ready=True, reason="", implementations=None):
        self.answers = dict(answers or {})
        self.implemented = dict(implementations or {})
        self.ready = ready
        self.reason = reason
        self.asked = []

    def probe(self):
        return (True, "") if self.ready else (False, self.reason)

    def identity(self):
        return "stub@1.0"

    def definitions(self, path, line, column):
        self.asked.append((Path(path).name, line, column))
        answer = self.answers.get((Path(path).name, line))
        if isinstance(answer, list):
            return answer
        return [] if answer is None else [answer]

    def implementations(self, path, line, column):
        answer = self.implemented.get((Path(path).name, line))
        if isinstance(answer, list):
            return answer
        return [] if answer is None else [answer]


class EdgeViewTests(unittest.TestCase):
    SOURCES = {
        "app/contracts.py": (
            "from typing import Protocol\n"
            "from abc import ABC, abstractmethod\n\n"
            "class RunnerProtocol(Protocol):\n"
            "    def run(self) -> int:\n"
            "        ...\n\n"
            "class AbstractRunner(ABC):\n"
            "    @abstractmethod\n"
            "    def execute(self) -> int:\n"
            "        raise NotImplementedError\n"
        ),
        "app/tool.py": (
            "class ConcreteRunner:\n"
            "    def run(self) -> int:\n"
            "        return 1\n\n"
            "def helper_fn() -> int:\n"
            "    return 2\n"
        ),
        "app/use.py": (
            "from app.tool import helper_fn\n\n"
            "def call_all(proto_runner, abs_runner, concrete_runner, mystery):\n"
            "    a = helper_fn()\n"
            "    b = proto_runner.run()\n"
            "    c = abs_runner.execute()\n"
            "    d = concrete_runner.run()\n"
            # Named after a project method, so the engine is asked and answers ambiguously.
            "    e = mystery.run()\n"
            "    return a + b + c + d + e\n"
        ),
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        self.root.mkdir()
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.write_snapshot(self.root, self.manifest)
        self.edges = self.root.parent / "engine-edges.sqlite"

    def test_load_edge_view_merges_lexical_and_confirmed_engine_edges_and_distinguishes_target_kinds(self):
        import edge_view

        manifest_digest_before = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        engine = StubEngine(answers={
            ("use.py", 5): Definition(self.root / "app/contracts.py", "run", line=5, column=8),
            ("use.py", 6): Definition(self.root / "app/contracts.py", "execute", line=10, column=8),
            ("use.py", 7): Definition(self.root / "app/tool.py", "run", line=2, column=8),
            ("use.py", 8): [
                Definition(self.root / "app/tool.py", "run", line=2, column=8),
                Definition(self.root / "app/tool.py", "helper_fn", line=5, column=4),
            ],
        })
        report = resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None, stride=1, out=self.edges)
        self.assertTrue(report["available"])
        self.assertEqual((report["confirmed_edges"], report["candidates"]), (3, 1))

        with open_snapshot(self.manifest) as store:
            view = edge_view.load_edge_view(store, engine_store=self.edges)

        self.assertEqual(view["schema"], edge_view.EDGE_VIEW_SCHEMA)
        self.assertEqual(view["version"], edge_view.EDGE_VIEW_VERSION)
        self.assertEqual(view["coverage"]["status"], "complete")
        self.assertEqual(view["profile"]["engine"], "stub@1.0")
        self.assertEqual(view["conflicts"], [])

        by_line = {ref["span"][0]: ref for ref in view["references"] if ref["file"] == "app/use.py"}
        # Line 4: lexical call to helper_fn()
        self.assertEqual(by_line[4]["resolution"], "resolved")
        self.assertEqual(by_line[4]["resolver"], "builtin-lexical")
        self.assertEqual(by_line[4]["target_kind"], "concrete")

        # Line 5: protocol method target
        self.assertEqual(by_line[5]["resolution"], "resolved")
        self.assertEqual(by_line[5]["resolver"], "stub@1.0")
        self.assertEqual(by_line[5]["target_kind"], "protocol")

        # Line 6: abstract / interface method target
        self.assertEqual(by_line[6]["resolution"], "resolved")
        self.assertEqual(by_line[6]["resolver"], "stub@1.0")
        self.assertEqual(by_line[6]["target_kind"], "interface")

        # Line 7: concrete class method target
        self.assertEqual(by_line[7]["resolution"], "resolved")
        self.assertEqual(by_line[7]["resolver"], "stub@1.0")
        self.assertEqual(by_line[7]["target_kind"], "concrete")

        # Line 8: ambiguous engine candidate stays unresolved in effective references
        self.assertEqual(by_line[8]["resolution"], "unresolved")
        self.assertIsNone(by_line[8]["target_id"])
        self.assertEqual(by_line[8]["engine_candidate"]["verdict"], "ambiguous-target")

        self.assertEqual(hashlib.sha256(self.manifest.read_bytes()).hexdigest(), manifest_digest_before)

    def test_load_edge_view_distinguishes_missing_empty_sampled_and_rejected_stores(self):
        import edge_view

        with open_snapshot(self.manifest) as store:
            missing_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(missing_view["coverage"]["status"], "missing_store")

        resolve_edges.resolve_edges(self.manifest, engine=StubEngine(), limit=1, stride=2, out=self.edges)
        with open_snapshot(self.manifest) as store:
            sampled_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(sampled_view["coverage"]["status"], "sampled")
        self.assertTrue(sampled_view["coverage"]["sampled"])

        resolve_edges.resolve_edges(self.manifest, engine=StubEngine(), limit=None, stride=1, out=self.edges)
        with open_snapshot(self.manifest) as store:
            empty_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(empty_view["coverage"]["status"], "completed_empty")
        self.assertFalse(empty_view["coverage"]["sampled"])

        self.edges.write_bytes(b"corrupted")
        with open_snapshot(self.manifest) as store:
            rejected_view = edge_view.load_edge_view(store, engine_store=self.edges)
        self.assertEqual(rejected_view["coverage"]["status"], "rejected_store")
        self.assertTrue(rejected_view["gaps"])

    def test_cli_compact_mode_and_report_out_write_full_report_to_file_and_summary_to_stdout(self):
        report_file = self.root.parent / "full-engine-report.json"
        engine = StubEngine(answers={
            ("use.py", 7): Definition(self.root / "app/tool.py", "run", line=2, column=8),
        })
        stdout = io.StringIO()
        with mock.patch.object(resolve_edges, "JediEngine", return_value=engine):
            with contextlib.redirect_stdout(stdout):
                code = resolve_edges.main([
                    str(self.manifest),
                    "--out", str(self.edges),
                    "--report-out", str(report_file),
                    "--compact",
                ])
        self.assertEqual(code, 0)
        compact = json.loads(stdout.getvalue())
        full = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertTrue(compact["available"])
        self.assertEqual(compact["confirmed_edges"], 1)
        self.assertEqual(compact["report_out"], report_file.as_posix())
        self.assertNotIn("file_environments", compact)
        self.assertIn("verdicts", full)
        self.assertEqual(full["confirmed_edges"], 1)


class MethodTargetTests(unittest.TestCase):
    """An engine edge to a method, or to the method an interface declares, reaches the view."""

    SOURCES = {
        "app/contracts.ts": "export interface Checkout {\n  start(plan: string): void;\n}\n",
        "app/shop.ts": "export class Shop {\n  open(): number {\n    return 1;\n  }\n}\n",
        "app/use.ts": ('import { Shop } from "./shop";\n'
                       'import type { Checkout } from "./contracts";\n\n'
                       "export function buy(shop: Shop, checkout: Checkout): number {\n"
                       '  checkout.start("pro");\n'
                       "  return shop.open();\n"
                       "}\n"),
    }

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve() / "proj"
        for rel, text in self.SOURCES.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        manifest, edges = root.parent / "manifest.sqlite", root.parent / "engine-edges.sqlite"
        snapshot.write_snapshot(root, manifest)
        engine = StubEngine(answers={
            ("use.ts", 5): Definition(root / "app/contracts.ts", "start", line=2, column=2),
            ("use.ts", 6): Definition(root / "app/shop.ts", "open", line=2, column=2),
        })
        engine.languages = ("typescript",)
        report = resolve_edges.resolve_edges(manifest, engine=engine, limit=None, stride=1, out=edges)
        self.assertEqual(report["confirmed_edges"], 2)
        self.root, self.manifest, self.edges = root, manifest, edges

    def test_a_method_and_a_contract_method_are_resolved_targets(self):
        import edge_view

        with open_snapshot(self.manifest) as store:
            view = edge_view.load_edge_view(store, engine_store=self.edges)
        by_line = {ref["span"][0]: ref for ref in view["references"] if ref["file"] == "app/use.ts"}
        self.assertEqual((by_line[5]["resolution"], by_line[5]["target_kind"]), ("resolved", "interface"))
        self.assertTrue(by_line[5]["target_id"].startswith("app/contracts.ts::"))
        self.assertEqual((by_line[6]["resolution"], by_line[6]["target_kind"]), ("resolved", "concrete"))
        self.assertTrue(by_line[6]["target_id"].startswith("app/shop.ts::"))
        self.assertEqual(view["coverage"]["resolution"]["engine_confirmed"], 2)

    def test_graph_from_a_method_file_keeps_its_incoming_calls(self):
        import source_reader

        for path, name in (("app/shop.ts", "open"), ("app/contracts.ts", "start")):
            with self.subTest(path=path), open_snapshot(self.manifest) as store:
                packet = source_reader.graph_packet(store, [path], hops=1, engine_store=self.edges)
                method = next(item for item in packet["declarations"] if item["name"] == name)
                self.assertEqual(method["kind"], "method")
                self.assertEqual([call["target_id"] for call in packet["calls"]], [method["id"]])
                self.assertEqual(packet["calls"][0]["file"], "app/use.ts")

    def test_file_analysis_and_usages_keep_confirmed_method_calls(self):
        import store_consumers

        for path, name in (("app/shop.ts", "open"), ("app/contracts.ts", "start")):
            with self.subTest(path=path), open_snapshot(self.manifest) as store:
                with store_consumers.consumer_reader(store, engine_store=self.edges) as db:
                    analysis, _, _ = store_consumers.file_analysis(store, db, path)
                    self.assertEqual(analysis["counts"]["incoming_calls"], 1)
                    self.assertIn(name, [item["name"] for item in analysis["declarations"]])
                with store_consumers.consumer_reader(store, engine_store=self.edges) as db:
                    usages = store_consumers.find_usages(store, db, [name], self.root / path, self.root)
                    self.assertEqual(len(usages[name].usages), 1)
                    self.assertEqual(usages[name].usages[0].precision, "resolved-static")


class ImplementationTests(unittest.TestCase):
    """Where the definition is the method an interface declares, the engine is asked where it is implemented."""

    SOURCES = {
        "app/contracts.ts": "export interface Checkout {\n  start(plan: string): void;\n}\n",
        "app/web.ts": ('import type { Checkout } from "./contracts";\n'
                       "export class WebCheckout implements Checkout {\n  start(plan: string): void {\n    return;\n  }\n}\n"),
        "app/mobile.ts": ('import type { Checkout } from "./contracts";\n'
                          "export class MobileCheckout implements Checkout {\n  start(plan: string): void {\n    return;\n  }\n}\n"),
        "app/use.ts": ('import type { Checkout } from "./contracts";\n\n'
                       "export function buy(checkout: Checkout, other: Checkout, third: Checkout): void {\n"
                       '  checkout.start("pro");\n'
                       '  other.start("base");\n'
                       '  third.start("team");\n'
                       "}\n"),
    }

    def test_one_implementation_is_the_target_and_several_keep_the_contract(self):
        import edge_view

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve() / "proj"
        for rel, text in self.SOURCES.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        manifest, edges = root.parent / "manifest.sqlite", root.parent / "engine-edges.sqlite"
        snapshot.write_snapshot(root, manifest)
        contract = Definition(root / "app/contracts.ts", "start", line=2, column=2)
        web = Definition(root / "app/web.ts", "start", line=3, column=2)
        mobile = Definition(root / "app/mobile.ts", "start", line=3, column=2)
        vendor = root.parent / "vendor/checkout.ts"
        vendor.parent.mkdir()
        vendor.write_text("export class VendorCheckout {\n  start(plan: string): void {}\n}\n", encoding="utf-8")
        outside = Definition(vendor, "start", line=2, column=2)
        engine = StubEngine(answers={("use.ts", 4): contract, ("use.ts", 5): contract, ("use.ts", 6): contract},
                            implementations={("use.ts", 4): web, ("use.ts", 5): [web, mobile],
                                             ("use.ts", 6): [web, outside]})
        engine.languages = ("typescript",)
        report = resolve_edges.resolve_edges(manifest, engine=engine, limit=None, stride=1, out=edges)
        self.assertEqual(report["confirmed_edges"], 3)
        with open_snapshot(manifest) as store:
            view = edge_view.load_edge_view(store, engine_store=edges)
        by_line = {ref["span"][0]: ref for ref in view["references"] if ref["file"] == "app/use.ts"}
        # An implementation outside the project cannot be excluded: the contract stays the target.
        self.assertTrue(by_line[6]["target_id"].startswith("app/contracts.ts::"))
        self.assertEqual(by_line[6]["target_kind"], "interface")
        self.assertTrue(by_line[4]["target_id"].startswith("app/web.ts::"))
        self.assertEqual(by_line[4]["target_kind"], "concrete")
        self.assertTrue(by_line[5]["target_id"].startswith("app/contracts.ts::"))
        self.assertEqual(by_line[5]["target_kind"], "interface")


class IndexStoreTests(unittest.TestCase):
    """The store written from the graph of `fixtures/code-graph/ts`, read through the view: one source per reference."""

    RESOLVER = "scip-typescript@0.5.2"
    ENDS = json.loads((Path(__file__).resolve().parent / "fixtures/code-graph/ts-ends.json").read_text(encoding="utf-8"))
    UNCERTAIN = "call src/web/tag.ts:5 closeTag"  # marked uncertain below, as an adapter's refine would

    @classmethod
    def setUpClass(cls):
        import shutil
        import code_graph
        import importlib
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name).resolve()
        shutil.copytree(Path(__file__).resolve().parent / "fixtures/code-graph/ts", root / "ts")
        cls.manifest, cls.edges = root / "manifest.sqlite", root / "engine-edges.sqlite"
        snapshot.write_snapshot(root / "ts", cls.manifest)
        adapter = importlib.import_module("indexers.typescript")
        site = cls.UNCERTAIN.split(" ")[1]

        def refine(_index, graph):
            for edge in graph["edges"]:
                if edge["site"] == site:
                    edge["uncertain"] = {"reason": "test-overload", "candidates": [edge["to"]]}

        with code_graph.Snapshot(cls.manifest) as snap:
            index = code_graph.Index(snap.root)
            index.load(root / "ts/index.scip")
            hops = adapter.hops(index)
            traversal = code_graph.Traversal(index, snap, hops)
            built = {language: code_graph.build(index, snap, language, hops, {"name": "scip-typescript",
                                                                              "version": "0.5.2"},
                                                None, traversal, refine=refine)
                     for language in ("javascript", "typescript")}
            code_graph.write_store(snap, cls.edges, built, cls.RESOLVER)
        with open_snapshot(cls.manifest) as store:
            cls.view = __import__("edge_view").load_edge_view(store, engine_store=cls.edges)
            cls.stored, _binding, cls.reason = resolve_edges.read_edge_store(cls.edges, store)
            cls.refs = {row[0]: row[1] for row in store.connection.execute(
                "SELECT r.id, r.kind FROM sem_references r JOIN sem_coverage c ON c.file=r.file "
                "WHERE r.kind IN ('call','read') AND c.language IN ('javascript','typescript')")}
        cls.holes = resolve_edges.read_edge_holes(cls.edges)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def record(self, site):
        kind, place, name = site.split(" ", 2)
        rel, line = place.rsplit(":", 1)
        found = [ref for ref in self.view["references" if kind == "call" else "reads"]
                 if ref["file"] == rel and ref["span"][0] == int(line) and ".".join(ref.get("parts") or []) == name]
        self.assertEqual(len(found), 1, site)
        return found[0]

    def test_every_expected_call_and_read_has_its_one_answer(self):
        self.assertIsNone(self.reason)
        lexical = {"call src/api/jobs.js:18 makeHandler", "call src/web/useCheckout.js:4 startCheckout",
                   "read src/web/App.jsx:14 handleClose"}
        for site, want in sorted(self.ENDS.items()):
            if site == self.UNCERTAIN:
                continue
            with self.subTest(site=site):
                ref, end = self.record(site), want["end"]
                if isinstance(end, list):
                    # Several ends: the contract the call names; its two implementations are no single target.
                    # The lexical resolver's same answer is no second source: it stays first in the provenance.
                    target = end[0]
                    self.assertEqual((ref["resolution"], ref["target_id"]), ("resolved", target))
                    sources = [resolve_edges.resolution.LEXICAL_RESOLVER] * (site in lexical) + [self.RESOLVER]
                    self.assertEqual((ref["resolver"], ref["provenance"]), (sources[0], sources))
                elif end.startswith("external"):
                    manager, package = end.split(" ")[1:]
                    self.assertEqual((ref["resolution"], ref["target_id"], ref["resolver"]),
                                     ("unresolved", None, self.RESOLVER))
                    self.assertEqual(ref["external"], {"manager": manager, "package": package.rsplit("@", 1)[0],
                                                       "version": package.rsplit("@", 1)[1]})
                elif end == "dangling-local":
                    self.assertEqual((ref["resolution"], ref["hole"], ref["resolver"]),
                                     ("unresolved", "dangling-local", resolve_edges.resolution.LEXICAL_RESOLVER))
                else:
                    self.assertEqual((ref["resolution"], ref["reason"], ref["resolver"]),
                                     ("unresolved", "project-value", self.RESOLVER))
        self.assertEqual(self.record("call src/web/store.ts:15 store.save")["target_kind"], "interface")

    def test_an_uncertain_end_is_a_candidate_and_no_target(self):
        ref = self.record(self.UNCERTAIN)
        self.assertEqual((ref["resolution"], ref["target_id"]), ("unresolved", None))
        self.assertEqual((ref["engine_candidate"]["verdict"], ref["engine_candidate"]["target_id"]),
                         ("test-overload", self.ENDS[self.UNCERTAIN]["end"][0]))
        self.assertIn(ref["engine_candidate"], self.view["candidates"])

    def test_the_store_holds_every_reference_and_the_sites_the_snapshot_does_not_list(self):
        answered = {edge["reference_id"] for edge in self.stored} | {hole["reference_id"] for hole in self.holes}
        self.assertEqual(set(self.refs) - answered, set())
        self.assertTrue(any(edge["reference_id"] is None and edge["kind"] == "unknown" for edge in self.stored))
        self.assertEqual({edge["kind"] for edge in self.stored if edge["reference_id"]}, {"call", "read"})
        self.assertTrue(all(edge["resolver"] == self.RESOLVER for edge in self.stored))

    def test_the_store_wins_over_a_different_lexical_target_and_the_difference_is_counted(self):
        import edge_view
        self.assertEqual(self.view["coverage"]["lexical_disagreements"], 0)
        ref = self.record("call src/api/jobs.js:18 makeHandler")
        other = self.record("call src/web/useCheckout.js:4 startCheckout")["target_id"]
        changed = Path(self.temp.name) / "changed.sqlite"
        changed.write_bytes(self.edges.read_bytes())
        connection = sqlite3.connect(changed)
        connection.execute("UPDATE edges SET target_id=? WHERE reference_id=?", (other, ref["id"]))
        connection.commit()
        connection.close()
        with open_snapshot(self.manifest) as store:
            view = edge_view.load_edge_view(store, engine_store=changed)
        moved = {item["id"]: item for item in view["references"]}[ref["id"]]
        self.assertEqual((moved["target_id"], moved["resolver"], moved["provenance"]),
                         (other, self.RESOLVER, [self.RESOLVER]))
        self.assertEqual(moved["lexical_target_id"], ref["target_id"])
        self.assertEqual(view["coverage"]["lexical_disagreements"], 1)
        self.assertEqual(view["conflicts"], [])

    def test_a_read_the_store_answers_reaches_the_effective_references(self):
        import semantic_store
        site = "read src/web/App.jsx:13 pay"
        read = self.record(site)
        self.assertEqual((read["lexical_resolution"], read["resolution"]), ("unresolved", "resolved"))
        with open_snapshot(self.manifest) as store, semantic_store.semantic_reader(store) as db:
            semantic_store.install_edge_view(db, store, engine_store=self.edges)
            row = db.execute("SELECT target_id, resolution FROM effective_references WHERE id=?", (read["id"],)).fetchone()
        self.assertEqual(tuple(row), (self.ENDS[site]["end"][0], "resolved"))

    def test_a_store_of_schema_4_is_refused_and_the_lexical_answers_stand(self):
        import edge_view
        from snapshot_store import _pack
        old = Path(self.temp.name) / "schema-4.sqlite"
        old.write_bytes(self.edges.read_bytes())
        connection = sqlite3.connect(old)
        connection.execute("UPDATE meta SET value=? WHERE key='schema'", (_pack(4),))
        connection.commit()
        connection.close()
        with open_snapshot(self.manifest) as store:
            self.assertEqual(resolve_edges.read_edge_store(old, store)[2], "engine edge store schema 4 is not 5")
            view = edge_view.load_edge_view(store, engine_store=old)
        self.assertEqual(view["coverage"]["status"], "rejected_store")
        ref = {item["id"]: item for item in view["references"]}[self.record("call src/api/jobs.js:18 makeHandler")["id"]]
        self.assertEqual(ref["provenance"], [resolve_edges.resolution.LEXICAL_RESOLVER])


if __name__ == "__main__":
    unittest.main()
