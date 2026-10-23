"""The optional engine pass: probing, grading against this snapshot, declared coverage."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_edges
import snapshot
from snapshot_store import _unpack, open_snapshot


class Definition:
    """The path, name, kind and exact position exposed by Jedi's answer."""

    def __init__(self, module_path, name, *, kind="function", line=2, column=8):
        self.module_path = module_path
        self.name = name
        self.type = kind
        self.line = line
        self.column = column


class StubEngine:
    """An engine whose every answer is scripted, so grading is tested without jedi."""

    name = "stub"

    def __init__(self, answers=None, ready=True, reason=""):
        self.answers = dict(answers or {})
        self.ready = ready
        self.reason = reason
        self.asked = []
        self.added_sys_path = ["<project>", "<venv-site-packages>"]
        self.unusable = []

    def probe(self):
        return (True, "") if self.ready else (False, self.reason)

    def identity(self):
        return "stub@1.0"

    def definitions(self, path, line, column):
        self.asked.append((Path(path).name, line, column))
        answer = self.answers.get((Path(path).name, line))
        return [] if answer is None else [answer]


class ResolveEdgesTests(unittest.TestCase):
    SOURCES = {
        # `helper.run()` leaves the lexical resolver with an unknown receiver, which
        # is exactly the population an engine is asked about.
        "app/use.py": "class User:\n    def go(self, helper):\n        return helper.run()\n",
        "app/tool.py": "class Tool:\n    def run(self):\n        return 1\n\n\ndef free():\n    return 2\n",
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

    def run_engine(self, engine, limit=None, **kwargs):
        return resolve_edges.resolve_edges(self.manifest, engine=engine, limit=limit,
                                           stride=1, out=self.edges, **kwargs)

    def references(self):
        with open_snapshot(self.manifest) as store:
            return [(row[0], row[1], _unpack(row[2])) for row in store.connection.execute(
                "SELECT id, resolution, payload FROM sem_references WHERE kind='call' ORDER BY id")]

    def stored_edges(self):
        with open_snapshot(self.manifest) as store:
            return resolve_edges.read_edge_store(self.edges, store)

    def unresolved_run_reference(self):
        for identity, resolution, payload in self.references():
            if payload["file"] == "app/use.py" and resolution == "unresolved" \
                    and payload["parts"] == ["helper", "run"]:
                return identity, payload
        raise AssertionError("the unknown-receiver call was not recorded")

    def test_every_reference_names_its_resolver_before_any_engine_runs(self):
        rows = self.references()
        self.assertTrue(rows)
        self.assertEqual({payload.get("resolver") for _id, _res, payload in rows},
                         {resolve_edges.resolution.LEXICAL_RESOLVER})

    def test_a_project_symbol_the_lexical_resolver_missed_becomes_a_confirmed_edge(self):
        _identity, before = self.unresolved_run_reference()
        self.assertEqual(before["reason"], "unknown-receiver")
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "run")})
        report = self.run_engine(engine)
        self.assertTrue(report["available"], report)
        self.assertEqual((report["confirmed_edges"], report["candidates"]), (1, 0))
        # The probe lands on the callee name, not on the receiver.
        line = self.SOURCES["app/use.py"].split("\n")[before["span"][0] - 1]
        self.assertEqual(engine.asked,
                         [("use.py", before["span"][0], line.index("helper") + len("helper."))])
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(reason, reason)
        self.assertEqual(len(edges), 1)
        edge = edges[0]
        self.assertEqual((edge["verdict"], edge["confidence"], edge["resolver"]),
                         ("edge-call", "confirmed", "stub@1.0"))
        self.assertTrue(edge["target_id"].startswith("app/tool.py::"), edge["target_id"])
        # The stored payload qualifies its caller already; qualifying it twice
        # produced `app/use.py::app/use.py::function@2:4` in a real jedi run.
        self.assertTrue(edge["caller"].startswith("app/use.py::function@"), edge["caller"])
        self.assertEqual(edge["caller"].count("::"), 1, edge["caller"])
        self.assertEqual(binding["engine"], "stub@1.0")
        self.assertEqual((binding["confirmed"], binding["candidates"]), (1, 0))
        # The snapshot is evidence: the lexical row is exactly what it was.
        after = dict((identity, (resolution, payload)) for identity, resolution, payload
                     in self.references())[_identity]
        self.assertEqual(after[0], "unresolved")
        self.assertEqual(after[1]["reason"], "unknown-receiver")
        self.assertEqual(after[1]["resolver"], resolve_edges.resolution.LEXICAL_RESOLVER)
        self.assertNotIn("confidence", after[1])

    def test_the_snapshot_bytes_are_never_modified_by_an_engine_pass(self):
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "run")})
        digest_before = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        self.run_engine(engine)
        self.assertEqual(hashlib.sha256(self.manifest.read_bytes()).hexdigest(), digest_before)

    def test_stale_source_is_refused_before_the_engine_is_asked(self):
        source = self.root / "app/use.py"
        source.write_text(source.read_text().replace("helper.run()", "other_.run()"),
                          encoding="utf-8")
        self.edges.write_bytes(b"preserve previous output")
        engine = StubEngine()
        report = self.run_engine(engine)
        self.assertFalse(report["available"], report)
        self.assertIn("source differs from snapshot: app/use.py", report["reason"])
        self.assertEqual(report["stage"], "before-inference")
        self.assertEqual(engine.asked, [])
        self.assertEqual(self.edges.read_bytes(), b"preserve previous output")

    def test_an_indirect_dependency_change_prevents_a_new_store(self):
        _identity, before = self.unresolved_run_reference()
        owner = self

        class ChangingEngine(StubEngine):
            def definitions(self, path, line, column):
                (owner.root / "app/tool.py").write_text("changed during inference\n",
                                                        encoding="utf-8")
                return super().definitions(path, line, column)

        engine = ChangingEngine({("use.py", before["span"][0]):
                                 Definition(self.root / "app/tool.py", "run")})
        self.edges.write_bytes(b"preserve previous output")
        report = self.run_engine(engine)
        self.assertFalse(report["available"], report)
        self.assertIn("app/tool.py", report["reason"])
        self.assertEqual(report["stage"], "after-inference")
        self.assertEqual(self.edges.read_bytes(), b"preserve previous output")

    def test_output_cannot_replace_the_manifest_or_an_inventoried_source(self):
        for destination in (self.manifest, self.root / "app/tool.py"):
            with self.subTest(destination=destination):
                original = destination.read_bytes()
                engine = StubEngine()
                report = resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None,
                                                     stride=1, out=destination)
                self.assertFalse(report["available"], report)
                self.assertIn("overwrite snapshot evidence", report["reason"])
                self.assertEqual(destination.read_bytes(), original)
                self.assertEqual(engine.asked, [])

    def test_an_output_hardlink_to_source_is_refused(self):
        original = (self.root / "app/tool.py").read_bytes()
        try:
            os.link(self.root / "app/tool.py", self.edges)
        except OSError as error:
            self.skipTest(f"hardlinks unavailable: {error}")
        report = self.run_engine(StubEngine())
        self.assertFalse(report["available"], report)
        self.assertIn("overwrite snapshot evidence", report["reason"])
        self.assertEqual(self.edges.read_bytes(), original)

    def test_a_linked_output_parent_is_refused(self):
        directory = self.root.parent / "linked-output"
        try:
            directory.symlink_to(self.root, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"directory symlinks unavailable: {error}")
        report = resolve_edges.resolve_edges(self.manifest, engine=StubEngine(), limit=None,
                                             stride=1, out=directory / "new-edges.sqlite")
        self.assertFalse(report["available"], report)
        self.assertIn("symlink or reparse path", report["reason"])
        self.assertFalse((self.root / "new-edges.sqlite").exists())

    def test_a_matching_name_at_a_different_position_is_no_confirmed_target(self):
        _identity, before = self.unresolved_run_reference()
        for definition in (Definition(self.root / "app/tool.py", "run", line=3),
                           Definition(self.root / "app/tool.py", "run", column=4),
                           Definition(self.root / "app/tool.py", "run", kind="instance")):
            with self.subTest(definition=vars(definition)):
                report = self.run_engine(StubEngine({("use.py", before["span"][0]): definition}))
                self.assertEqual((report["confirmed_edges"], report["candidates"]), (0, 1))

    def test_multiple_engine_targets_are_a_candidate_instead_of_a_first_answer_edge(self):
        owner = self

        class MultipleEngine(StubEngine):
            def definitions(self, path, line, column):
                return [Definition(owner.root / "app/tool.py", "run"),
                        Definition(owner.root / "app/tool.py", "free", line=6, column=4)]

        report = self.run_engine(MultipleEngine())
        self.assertEqual((report["confirmed_edges"], report["candidates"]), (0, 1))
        edges, _binding, reason = self.stored_edges()
        self.assertIsNone(reason)
        self.assertEqual(edges[0]["verdict"], "ambiguous-target")

    def test_identical_engine_answers_can_converge_on_one_declaration(self):
        owner = self

        class DuplicateEngine(StubEngine):
            def definitions(self, path, line, column):
                return [Definition(owner.root / "app/tool.py", "run"),
                        Definition(owner.root / "app/tool.py", "run")]

        report = self.run_engine(DuplicateEngine())
        self.assertEqual((report["confirmed_edges"], report["candidates"]), (1, 0))

    def test_same_named_methods_arrive_at_the_exact_declaration(self):
        tool = self.root / "app/tool.py"
        tool.write_text(tool.read_text() + "\nclass Other:\n    def run(self):\n        return 3\n",
                        encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        _identity, before = self.unresolved_run_reference()
        report = self.run_engine(StubEngine({("use.py", before["span"][0]):
                                             Definition(tool, "run", line=10)}))
        self.assertEqual(report["confirmed_edges"], 1, report)
        edges, _binding, reason = self.stored_edges()
        self.assertIsNone(reason)
        self.assertEqual(edges[0]["target_id"], "app/tool.py::function@10:4")

    def test_unicode_before_the_callee_uses_character_columns(self):
        source = 'class User:\n    def go(self, helper):\n        marker = "é"; return helper.run()\n'
        (self.root / "app/use.py").write_text(source, encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine({("use.py", before["span"][0]):
                             Definition(self.root / "app/tool.py", "run")})
        report = self.run_engine(engine)
        self.assertEqual(report["confirmed_edges"], 1, report)
        self.assertEqual(engine.asked[0][2], source.splitlines()[2].index("run"))

    def test_a_multiline_callee_is_probed_on_its_final_line(self):
        source = "class User:\n    def go(self, helper):\n        return (helper\n                .run)()\n"
        (self.root / "app/use.py").write_text(source, encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        engine = StubEngine({("use.py", 4): Definition(self.root / "app/tool.py", "run")})
        report = self.run_engine(engine)
        self.assertEqual(report["confirmed_edges"], 1, report)
        self.assertEqual(engine.asked, [("use.py", 4, source.splitlines()[3].index("run"))])

    def test_a_failed_atomic_write_preserves_output_and_other_partial_files(self):
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine({("use.py", before["span"][0]):
                             Definition(self.root / "app/tool.py", "run")})
        self.edges.write_bytes(b"old output")
        partial = self.edges.with_name(self.edges.name + ".partial")
        partial.write_bytes(b"another invocation")
        with mock.patch.object(resolve_edges.os, "replace", side_effect=OSError("cannot replace")):
            report = self.run_engine(engine)
        self.assertFalse(report["available"], report)
        self.assertEqual(report["stage"], "write")
        self.assertIn("cannot replace", report["reason"])
        self.assertEqual(self.edges.read_bytes(), b"old output")
        self.assertEqual(partial.read_bytes(), b"another invocation")
        self.assertEqual(list(self.edges.parent.glob(".engine-edges.sqlite.*.partial")), [])

    def test_class_inference_does_not_land_on_a_same_named_method(self):
        tool = self.root / "app/tool.py"
        tool.write_text(tool.read_text() + "\nclass run:\n    pass\n", encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        _identity, before = self.unresolved_run_reference()
        report = self.run_engine(StubEngine({("use.py", before["span"][0]):
                                             Definition(tool, "run", kind="class", line=9, column=6)}))
        self.assertEqual(report["confirmed_edges"], 1, report)
        edges, _binding, reason = self.stored_edges()
        self.assertIsNone(reason)
        self.assertEqual((edges[0]["target_id"], edges[0]["verdict"]),
                         ("app/tool.py::class@9:0", "edge-instantiation"))

    def test_an_async_declaration_uses_its_name_position(self):
        tool = self.root / "app/tool.py"
        tool.write_text("class Tool:\n    async def run(self):\n        return 1\n",
                        encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        _identity, before = self.unresolved_run_reference()
        report = self.run_engine(StubEngine({("use.py", before["span"][0]):
                                             Definition(tool, "run", line=2, column=14)}))
        self.assertEqual(report["confirmed_edges"], 1, report)
        edges, _binding, reason = self.stored_edges()
        self.assertIsNone(reason)
        self.assertEqual(edges[0]["target_id"], "app/tool.py::function@2:4")

    def test_a_target_outside_the_inventory_is_external_and_produces_no_edge(self):
        _identity, before = self.unresolved_run_reference()
        outside = self.root.parent / "elsewhere" / "venv" / "lib.py"
        engine = StubEngine(answers={("use.py", before["span"][0]): Definition(outside, "run")})
        report = self.run_engine(engine)
        self.assertEqual(report["verdicts"].get("external-definition"), 1)
        self.assertEqual(report["confirmed_edges"], 0)
        self.assertTrue(self.edges.exists())
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(reason)
        self.assertEqual(edges, [])
        self.assertEqual((binding["confirmed"], binding["candidates"]), (0, 0))

    def test_a_project_name_that_is_no_symbol_stays_a_candidate(self):
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "not_a_symbol")})
        report = self.run_engine(engine)
        self.assertEqual(report["verdicts"].get("project-not-a-symbol"), 1)
        self.assertEqual((report["candidates"], report["confirmed_edges"]), (1, 0))
        edges, _binding, reason = self.stored_edges()
        self.assertIsNone(reason, reason)
        self.assertEqual([(edge["verdict"], edge["confidence"], edge["target_id"])
                          for edge in edges],
                         [("project-not-a-symbol", "candidate", None)])

    def test_an_unready_engine_is_a_declared_degradation_that_writes_nothing(self):
        engine = StubEngine(ready=False, reason="jedi is not installed")
        report = self.run_engine(engine)
        self.assertFalse(report["available"])
        self.assertEqual(report["reason"], "jedi is not installed")
        self.assertEqual(engine.asked, [])
        self.assertFalse(self.edges.exists())

    def test_a_dry_run_grades_without_writing_a_store(self):
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "run")})
        report = self.run_engine(engine, dry_run=True)
        self.assertEqual(report["confirmed_edges"], 1)
        self.assertTrue(report["dry_run"])
        self.assertEqual(report["edges_store"], None)
        self.assertFalse(self.edges.exists())

    def test_coverage_is_declared_against_the_population_it_asked_about(self):
        report = self.run_engine(StubEngine(), limit=1)
        self.assertEqual(report["asked"], 1)
        self.assertGreaterEqual(report["population"], 1)
        self.assertEqual(report["coverage"],
                         f"1 of {report['population']} unresolved call references")
        self.assertIn("builtin-lexical", report["note"])

    def test_selected_dynamic_references_are_not_counted_as_engine_invocations(self):
        (self.root / "app/use.py").write_text(
            "def use(helper):\n    helper.run()\n    helper()()\n", encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        engine = StubEngine()
        report = self.run_engine(engine)
        self.assertGreater(report["selected"], report["asked"], report)
        self.assertEqual(report["asked"], len(engine.asked))
        self.assertEqual(report["coverage"],
                         f"{len(engine.asked)} of {report['population']} unresolved call references")
        self.assertEqual(report["verdicts"].get("dynamic-callee"), 1)

    def test_failed_inferences_are_counted_as_actual_requests(self):
        class FailingEngine(StubEngine):
            def definitions(self, path, line, column):
                super().definitions(path, line, column)
                raise RuntimeError("engine failed")

        engine = FailingEngine()
        report = self.run_engine(engine)
        self.assertEqual(report["asked"], len(engine.asked))
        self.assertEqual(report["asked"], 1)
        self.assertEqual(report["verdicts"], {"infer-error:RuntimeError": 1})

    def test_invalid_positions_are_selected_but_never_counted_as_asked(self):
        source = "def use(helper):\n    helper.K()\n"
        (self.root / "app/use.py").write_text(source, encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        # AST normalizes this identifier to K. A position that cannot be
        # verified against its recorded spelling must remain unprobed.
        engine = StubEngine()
        report = self.run_engine(engine)
        self.assertEqual((report["selected"], report["asked"], report["position_unverified"]),
                         (1, 0, 1), report)
        self.assertEqual(engine.asked, [])

    def test_the_population_is_limited_to_the_engines_python_language(self):
        (self.root / "app/use.ts").write_text(
            "function use(helper) { return helper.run(); }\n", encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        engine = StubEngine()
        report = self.run_engine(engine)
        self.assertEqual(report["population"], 1, report)
        self.assertEqual(report["population_language"], "python")
        self.assertEqual({file for file, line, column in engine.asked}, {"use.py"})

    def test_p95_uses_the_upper_sample_for_two_inferences(self):
        (self.root / "app/use.py").write_text(
            "def use(helper):\n    helper.run()\n    helper.free()\n", encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        with mock.patch.object(resolve_edges.time, "perf_counter",
                               side_effect=[0, 1, 1.01, 2, 2.1, 3, 3.2, 4]):
            report = self.run_engine(StubEngine())
        self.assertEqual(report["asked"], 2)
        self.assertEqual(report["latency_mean_ms"], 150)
        self.assertEqual(report["latency_p95_ms"], 200)
        for field in ("probe_init_elapsed_ms", "inference_elapsed_ms", "total_elapsed_ms"):
            self.assertTrue(math.isfinite(report[field]), (field, report))
            self.assertGreaterEqual(report[field], 0)
        self.assertEqual(report["probe_init_elapsed_ms"], 10)
        self.assertEqual(report["inference_elapsed_ms"], 300)
        self.assertEqual(report["total_elapsed_ms"], 4000)
        estimate = report["inference_only_extrapolation"]
        self.assertEqual((estimate["asked"], estimate["selected"], estimate["population"], estimate["stride"]),
                         (report["asked"], report["selected"], report["population"], report["stride"]))
        self.assertEqual(estimate["estimated_ms"], 300)
        self.assertIn("deterministic", estimate["sampling_bias"])
        self.assertIn("excluded", estimate["cost_scope"])

    def test_edges_of_another_snapshot_revision_are_refused_not_joined(self):
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "run")})
        self.run_engine(engine)
        (self.root / "app" / "use.py").write_text(
            "class User:\n    def go(self, helper):\n        return helper.run()\n"
            "# edited after the engine pass\n", encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNotNone(binding)
        self.assertIn("different snapshot revision", reason)

    def test_a_json_manifest_is_refused_because_it_holds_no_reference_table(self):
        manifest = self.root.parent / "manifest.json"
        snapshot.write_snapshot(self.root, manifest, format="json")
        report = resolve_edges.resolve_edges(manifest, engine=StubEngine(), limit=None,
                                             stride=1, out=self.edges)
        self.assertFalse(report["available"])
        self.assertIn("sqlite", report["reason"])

    def test_a_malformed_derived_store_is_refused_with_a_reason(self):
        self.edges.write_bytes(b"not a SQLite database")
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNone(binding)
        self.assertIn("invalid engine edge store", reason)

    def test_resolver_version_mismatch_is_rejected(self):
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "run")})
        self.run_engine(engine)
        with mock.patch.object(resolve_edges.semantic_store, "RESOLVER_VERSION", 999):
            edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNotNone(binding)
        self.assertIn("resolver version", reason)

    def test_completed_empty_pass_is_distinct_from_missing_store(self):
        with open_snapshot(self.manifest) as store:
            missing_edges, missing_binding, missing_reason = resolve_edges.read_edge_store(self.edges, store)
        self.assertIsNone(missing_edges)
        self.assertIsNone(missing_binding)
        self.assertIn("no engine edge store", missing_reason)

        report = self.run_engine(StubEngine())
        self.assertTrue(report["available"])
        self.assertEqual((report["confirmed_edges"], report["candidates"]), (0, 0))
        self.assertTrue(self.edges.is_file())
        self.assertEqual(report["edges_store"], self.edges.as_posix())
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(reason)
        self.assertEqual(edges, [])
        self.assertEqual(binding["confirmed"], 0)
        self.assertEqual(binding["no_edges_reason"], "no-project-targets")

    def test_engine_target_must_belong_to_snapshot(self):
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "run")})
        self.run_engine(engine)
        import sqlite3
        conn = sqlite3.connect(self.edges)
        try:
            conn.execute("UPDATE edges SET target_id='app/ghost.py::function@1:0'")
            conn.commit()
        finally:
            conn.close()
        edges, binding, reason = self.stored_edges()
        self.assertIsNone(edges)
        self.assertIsNotNone(binding)
        self.assertIn("not in snapshot", reason)

    def test_divergent_targets_remain_conflicts(self):
        import edge_view
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "run")})
        self.run_engine(engine)
        import sqlite3
        with open_snapshot(self.manifest) as store:
            row = store.connection.execute(
                "SELECT id FROM sem_declarations WHERE file='app/tool.py' AND name='free'"
            ).fetchone()
            free_id = row[0]
        conn = sqlite3.connect(self.manifest)
        try:
            # Simulate a reference already resolved lexically to `free` while engine says `run`
            conn.close()
        finally:
            pass
        with open_snapshot(self.manifest) as store:
            edges, binding, reason = resolve_edges.read_edge_store(self.edges, store)
            self.assertIsNone(reason)
            view = edge_view.load_edge_view(
                store,
                engine_store=self.edges,
                lexical_overrides={_identity: free_id},
            )
        self.assertEqual(len(view["conflicts"]), 1)
        conflict = view["conflicts"][0]
        self.assertEqual(conflict["reference_id"], _identity)
        self.assertEqual(conflict["lexical_target_id"], free_id)
        self.assertTrue(conflict["engine_target_id"].startswith("app/tool.py::function@2:4"))
        ref_by_id = {item["id"]: item for item in view["references"]}
        self.assertEqual(ref_by_id[_identity]["target_id"], free_id)


class CalleePositionTests(unittest.TestCase):
    def test_the_callee_name_is_probed_not_the_receiver(self):
        line = "        return helper.run()"
        start = line.index("helper")
        span = [2, start, 2, start + len("helper.run")]
        self.assertEqual(resolve_edges.callee_column(line, span, "run"),
                         start + len("helper."))

    def test_a_name_outside_its_own_span_is_not_probed_at_a_guess(self):
        line = "        return helper.run()"
        start = line.index("helper")
        span = [2, start, 2, start + len("helper")]
        self.assertIsNone(resolve_edges.callee_column(line, span, "run"))


class EnvironmentTests(unittest.TestCase):
    def make_environment(self, root, relative, names):
        environment = root / relative
        packages = environment / "Lib/site-packages"
        packages.mkdir(parents=True)
        (environment / "pyvenv.cfg").write_text("home = .\n", encoding="utf-8")
        interpreter = environment / "Scripts/python.exe"
        interpreter.parent.mkdir()
        interpreter.write_bytes(b"fixture; never executed")
        for name in names:
            (packages / name).mkdir()
        return environment, packages

    def engine_with_mock_jedi(self, root, environments, *, broken=()):
        jedi = types.ModuleType("jedi")
        jedi.__version__ = "test"
        api = types.ModuleType("jedi.api")
        environment_api = types.ModuleType("jedi.api.environment")
        default = types.SimpleNamespace(executable=sys.executable, version_info=(3, 13, 0))

        def project(*, path, added_sys_path):
            return types.SimpleNamespace(path=path, added_sys_path=added_sys_path)

        def create_environment(path, *, safe):
            path = Path(path)
            if path in broken or not (path / "pyvenv.cfg").is_file():
                raise RuntimeError("requested interpreter cannot launch")
            return types.SimpleNamespace(path=str(path),
                                         executable=str(path / "Scripts/python.exe"),
                                         version_info=(3, 13, 0))

        jedi.Project = mock.Mock(side_effect=project)
        jedi.Script = mock.Mock(return_value=types.SimpleNamespace(infer=lambda **kwargs: [object()]))
        environment_api.create_environment = create_environment
        environment_api.get_default_environment = lambda: default
        self.enterContext(mock.patch.dict(sys.modules, {"jedi": jedi, "jedi.api": api,
                                                       "jedi.api.environment": environment_api}))
        engine = resolve_edges.JediEngine(root, environments)
        ready, reason = engine.probe()
        self.assertTrue(ready, reason)
        return engine

    def test_a_venv_root_a_site_packages_and_neither(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            windows = root / "win-venv"
            (windows / "Lib" / "site-packages").mkdir(parents=True)
            (windows / "pyvenv.cfg").write_text("home = .\n", encoding="utf-8")
            posix = root / "posix-venv"
            (posix / "lib" / "python3.12" / "site-packages").mkdir(parents=True)
            (posix / "pyvenv.cfg").write_text("home = .\n", encoding="utf-8")
            bare = root / "site-packages"
            bare.mkdir()
            plain = root / "project"
            plain.mkdir()
            self.assertEqual(resolve_edges.site_packages_of(windows),
                             windows / "Lib" / "site-packages")
            self.assertEqual(resolve_edges.site_packages_of(posix),
                             posix / "lib" / "python3.12" / "site-packages")
            self.assertEqual(resolve_edges.site_packages_of(bare), bare)
            self.assertIsNone(resolve_edges.site_packages_of(plain))

    def test_package_count_excludes_installers_metadata_and_nonimportable_files(self):
        with tempfile.TemporaryDirectory() as temp:
            packages = Path(temp).resolve() / "site-packages"
            packages.mkdir()
            for name in ("pip", "setuptools", "wheel", "_distutils_hack", "pkg_resources",
                         "__pycache__", "requests", "google", "pkg-1.dist-info"):
                (packages / name).mkdir()
            for name in ("service.py", "native.cp313-win_amd64.pyd", "README.txt", "editable.pth"):
                (packages / name).write_bytes(b"")
            self.assertEqual(resolve_edges.package_names(packages),
                             ["google", "native", "requests", "service"])

    def test_a_populated_outer_environment_beats_a_nearer_pip_only_stub(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            populated, _ = self.make_environment(root, "env", ["requests"])
            stub, _ = self.make_environment(root, "app/.venv", ["pip", "setuptools", "wheel"])
            engine = self.engine_with_mock_jedi(root, [stub, populated])
            _project, environment, mode = engine.environment_for(root / "app/use.py")
            self.assertEqual((Path(environment.path), mode), (populated, "create_environment"))
            report = engine.report()["file_environments"]["app/use.py"]
            self.assertEqual(report["path"], populated.as_posix())
            self.assertEqual(report["package_count"], 1)
            self.assertEqual(Path(report["interpreter"]), populated / "Scripts/python.exe")
            self.assertEqual(report["selection"], "populated-serving-scope")

    def test_a_populated_offered_environment_beats_an_empty_serving_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            stub, _ = self.make_environment(root, ".venv", ["pip"])
            populated, _ = self.make_environment(root, "worker/env", ["requests"])
            engine = self.engine_with_mock_jedi(root, [stub, populated])
            _project, environment, mode = engine.environment_for(root / "app/use.py")
            self.assertEqual((Path(environment.path), mode), (populated, "create_environment"))
            self.assertEqual(engine.report()["file_environments"]["app/use.py"]["selection"],
                             "populated-nearest-offered-environment")

    def test_populated_environments_use_the_nearest_serving_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            outer, _ = self.make_environment(root, "env", ["requests", "more"])
            inner, _ = self.make_environment(root, "app/.venv", ["requests"])
            engine = self.engine_with_mock_jedi(root, [outer, inner])
            _project, environment, mode = engine.environment_for(root / "app/use.py")
            self.assertEqual((Path(environment.path), mode), (inner, "create_environment"))

    def test_fallback_environments_do_not_pool_other_projects_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            first, first_packages = self.make_environment(root, "first/env", ["first_pkg"])
            second, second_packages = self.make_environment(root, "second/env", ["second_pkg"])
            engine = self.engine_with_mock_jedi(root, [first, second], broken=[first, second])
            project, environment, mode = engine.environment_for(root / "first/use.py")
            self.assertEqual(mode, "added_sys_path")
            self.assertEqual(project.added_sys_path, [str(root), str(first_packages)])
            self.assertNotIn(str(second_packages), project.added_sys_path)
            report = engine.report()["file_environments"]["first/use.py"]
            self.assertEqual(report["path"], first.as_posix())
            self.assertEqual(report["requested_interpreter"], (first / "Scripts/python.exe").as_posix())
            self.assertEqual(report["interpreter"], sys.executable)
            self.assertEqual(report["package_count"], 1)
            self.assertNotIn("package_names", report)
            self.assertIn("cannot launch", engine.report()["environments"][0]["create_environment_error"])

    def test_a_healthy_environment_wins_a_tie_with_a_broken_populated_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            broken, _ = self.make_environment(root, ".venv", ["more", "packages"])
            healthy, _ = self.make_environment(root, "venv", ["requests"])
            engine = self.engine_with_mock_jedi(root, [broken, healthy], broken=[broken])
            _project, environment, mode = engine.environment_for(root / "app/use.py")
            self.assertEqual((Path(environment.path), mode), (healthy, "create_environment"))
            self.assertIn("create_environment_error", engine.report()["environments"][0])

    def test_a_bare_site_packages_directory_serves_the_project_in_fallback_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            packages = root / "dependencies/site-packages"
            (packages / "requests").mkdir(parents=True)
            engine = self.engine_with_mock_jedi(root, [packages])
            project, _environment, mode = engine.environment_for(root / "app/use.py")
            self.assertEqual(mode, "added_sys_path")
            self.assertEqual(project.added_sys_path, [str(root), str(packages)])
            self.assertEqual(engine.report()["file_environments"]["app/use.py"]["package_count"], 1)

    def test_project_only_and_unusable_environments_are_declared_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            missing = root / "no-such-environment"
            engine = self.engine_with_mock_jedi(root, [missing])
            _project, environment, mode = engine.environment_for(root / "app/use.py")
            self.assertEqual(mode, "project-only")
            report = engine.report()
            self.assertEqual(report["unusable_environments"], [str(missing)])
            self.assertEqual(report["file_environments"]["app/use.py"]["interpreter"], sys.executable)
            self.assertEqual(report["inference_modes"], {"project-only": 1})


class CommandLineTests(unittest.TestCase):
    def test_the_command_reports_a_missing_engine_as_a_failure_with_its_recovery(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve() / "proj"
            root.mkdir()
            (root / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
            manifest = Path(temp).resolve() / "manifest.sqlite"
            snapshot.write_snapshot(root, manifest)
            engine = StubEngine(ready=False, reason="jedi is not installed")
            stdout = io.StringIO()
            with mock.patch.object(resolve_edges, "JediEngine", return_value=engine):
                with contextlib.redirect_stdout(stdout):
                    code = resolve_edges.main([str(manifest), "--engine", "jedi"])
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["available"])
        self.assertIn("uv run --with jedi", payload["install"])


if __name__ == "__main__":
    unittest.main()
