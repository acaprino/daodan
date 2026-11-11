"""The optional engine pass: probing, grading against this snapshot, declared coverage."""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_edges
import snapshot
from snapshot_store import _unpack, open_snapshot


class Definition:
    """An engine's answer: a path and the exact position of a name, in UTF-8 bytes.

    Name and kind mirror what Jedi also reports; grading reads only the position.
    """

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
        answer = self.answers.get((Path(path).name, line, column), self.answers.get((Path(path).name, line)))
        return [] if answer is None else answer if isinstance(answer, list) else [answer]


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
                           # An answer that names no declaration, as Jedi's instances do.
                           Definition(self.root / "app/tool.py", "run", column=None)):
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

    def test_unicode_before_the_callee_is_counted_in_bytes_at_the_engine_boundary(self):
        source = 'class User:\n    def go(self, helper):\n        marker = "é"; return helper.run()\n'
        (self.root / "app/use.py").write_text(source, encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        _identity, before = self.unresolved_run_reference()
        engine = StubEngine({("use.py", before["span"][0]):
                             Definition(self.root / "app/tool.py", "run")})
        report = self.run_engine(engine)
        self.assertEqual(report["confirmed_edges"], 1, report)
        line = source.splitlines()[2]
        self.assertEqual(engine.asked[0][2], len(line[:line.index("run")].encode("utf-8")))

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
        # `1` in `return 1`: a project position that names no declaration.
        engine = StubEngine(answers={("use.py", before["span"][0]):
                                     Definition(self.root / "app/tool.py", "not_a_symbol", line=3, column=15)})
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
        # `K` is declared, so the callee is named after a project declaration
        # and stays in the population the engine is asked about.
        source = "def K():\n    return 1\n\n\ndef use(helper):\n    helper.K()\n"
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
        # A clock that only the engine advances: 10 ms to start, then 100 and 200 ms per answer.
        clock = [0.0]
        steps = iter([0.01, 0.1, 0.2])

        class TimedEngine(StubEngine):
            def probe(self):
                clock[0] += next(steps)
                return super().probe()

            def definitions(self, path, line, column):
                clock[0] += next(steps)
                return super().definitions(path, line, column)

        with mock.patch.object(resolve_edges.time, "perf_counter", side_effect=lambda: clock[0]):
            report = self.run_engine(TimedEngine())
        self.assertEqual(report["asked"], 2)
        self.assertEqual(report["latency_mean_ms"], 150)
        self.assertEqual(report["latency_p95_ms"], 200)
        for field in ("probe_init_elapsed_ms", "inference_elapsed_ms", "total_elapsed_ms"):
            self.assertTrue(math.isfinite(report[field]), (field, report))
            self.assertGreaterEqual(report[field], 0)
        self.assertEqual(report["probe_init_elapsed_ms"], 10)
        self.assertEqual(report["inference_elapsed_ms"], 300)
        self.assertEqual(report["total_elapsed_ms"], 310)
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


class ResolvabilityTests(unittest.TestCase):
    """Resolved over resolvable, the engine kept on project names, and the store lifecycle."""

    SOURCES = {
        # One call of each kind: a builtin, a callee named after nothing the
        # project declares, and an unknown receiver whose method the project has.
        "app/use.py": ("class User:\n    def go(self, helper):\n"
                       "        helper.append(len(helper))\n        return helper.run()\n"),
        "app/tool.py": "class Tool:\n    def run(self):\n        return 1\n",
        "notes.md": "# Notes\n",
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.write_snapshot(self.root, self.manifest)

    def run_line(self):
        return self.SOURCES["app/use.py"].split("\n").index("        return helper.run()") + 1

    def confirming_engine(self):
        return StubEngine(answers={("use.py", self.run_line()): Definition(self.root / "app/tool.py", "run")})

    def run_pass(self, engine=None):
        return resolve_edges.resolve_edges(self.manifest, engine=engine or self.confirming_engine(),
                                           limit=None, stride=1)

    def test_only_proven_external_calls_leave_the_denominator(self):
        with open_snapshot(self.manifest) as store:
            summary = resolve_edges.resolution_summary(store.connection, None)
        self.assertEqual((summary["calls"], summary["resolved"], summary["external"], summary["resolvable"]),
                         (3, 0, 1, 2))
        self.assertEqual(summary["external_by_class"],
                         {"builtin": 1, "engine-external-definition": 0})
        self.assertEqual((summary["askable"], summary["unasked"], summary["resolved_ratio"]), (2, 2, 0.0))

    def test_project_names_are_prioritized_but_other_names_are_asked(self):
        engine = self.confirming_engine()
        report = self.run_pass(engine)
        self.assertTrue(report["available"], report)
        self.assertEqual([line for _name, line, _column in engine.asked], [self.run_line(), self.run_line() - 1])
        self.assertEqual(report["excluded_classes"], {"builtin": 1})
        resolution = report["resolution"]
        self.assertEqual((resolution["resolved"], resolution["resolvable"], resolution["resolved_ratio"]),
                         (1, 2, 0.5))

    def test_an_alias_absent_from_project_names_can_resolve_internally(self):
        (self.root / "app/use.py").write_text(
            "from .tool import Tool\ndef use():\n    alias = Tool.run\n    return alias(None)\n",
            encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        with open_snapshot(self.manifest) as store:
            self.assertNotIn("alias", resolve_edges.project_callee_names(store.connection))
        engine = StubEngine({("use.py", 4): Definition(self.root / "app/tool.py", "run")})
        resolution = self.run_pass(engine)["resolution"]
        self.assertEqual((resolution["resolved"], resolution["resolvable"], resolution["external"]), (1, 1, 0))

    def test_each_language_says_whether_an_engine_covers_it(self):
        (self.root / "app/use.ts").write_text(
            "function use(helper) { return helper.run(); }\n", encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        by_language = self.run_pass()["resolution"]["by_language"]
        self.assertEqual((by_language["python"]["engine"], by_language["python"]["resolved"]), ("stub@1.0", 1))
        self.assertEqual(by_language["typescript"],
                         {"calls": 1, "resolved": 0, "resolvable": 1, "resolved_ratio": 0.0, "engine": None})

    def test_the_engine_sees_the_directories_the_project_puts_on_sys_path(self):
        (self.root / "tools").mkdir()
        (self.root / "tools/helper.py").write_text("def assist():\n    return 1\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "tests/test_tool.py").write_text(
            "import json\nimport sys\nsys.path.insert(0, 'tools')\nimport helper\nhelper.assist()\n",
            encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        with open_snapshot(self.manifest) as store:
            self.assertEqual(resolve_edges.runtime_import_roots(store.connection), ["tools"])
        engine = self.confirming_engine()
        engine.import_roots = []
        self.run_pass(engine)
        self.assertEqual(engine.import_roots, [self.root / "tools"])

    def test_a_changed_document_does_not_refuse_a_python_pass(self):
        (self.root / "notes.md").write_text("# Notes, edited during the pass\n", encoding="utf-8")
        report = self.run_pass()
        self.assertTrue(report["available"], report)
        self.assertEqual(report["source_verification"], {"before_inference": 2, "after_inference": 2})

    def test_the_store_state_follows_the_pass_and_the_snapshot(self):
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "missing")
        self.run_pass()
        state = resolve_edges.edge_state(self.manifest)
        self.assertEqual(state["state"], "fresh")
        self.assertEqual(state["resolution"]["resolved"], 1)
        (self.root / "app/tool.py").write_text("class Tool:\n    def run(self):\n        return 2\n",
                                                encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "stale")

    def test_a_missing_engine_is_unavailable_and_starts_no_process(self):
        with mock.patch.object(resolve_edges.shutil, "which", return_value=None), \
                mock.patch.object(resolve_edges.importlib.util, "find_spec", return_value=None), \
                mock.patch.object(resolve_edges, "_spawn_detached") as spawn:
            result = resolve_edges.ensure_edges(self.manifest)
        spawn.assert_not_called()
        self.assertEqual((result["state"], result["action"]), ("unavailable", "none"))
        self.assertIn("uv", result["install"])
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "unavailable")

    def test_the_pass_runs_under_uv_with_the_snapshots_parser_set(self):
        report = self.manifest.with_name(resolve_edges.REPORT_NAME)

        def version(name):
            if name == "tree-sitter":
                return "0.25.2"
            raise resolve_edges.metadata.PackageNotFoundError(name)

        with mock.patch.object(resolve_edges.shutil, "which", return_value="uv"), \
                mock.patch.object(resolve_edges.metadata, "version", side_effect=version):
            command = resolve_edges.stage_command(resolve_edges.ENGINES[0], self.manifest, report, [])
        python = f"{sys.version_info[0]}.{sys.version_info[1]}"
        self.assertEqual(command[:7], ["uv", "run", "--quiet", "--no-config", "--no-project", "--python", python])
        self.assertEqual(command[7:11], ["--with", "jedi>=0.19", "--with", "tree-sitter==0.25.2"])
        self.assertEqual(command[11:15], ["python", "-B", "-X", "faulthandler"])
        self.assertIn(str(report), command)
        with mock.patch.object(resolve_edges.shutil, "which", return_value=None), \
                mock.patch.object(resolve_edges.importlib.util, "find_spec", return_value=object()):
            self.assertEqual(resolve_edges.stage_command(resolve_edges.ENGINES[0], self.manifest, report, [])[:4],
                             [sys.executable, "-B", "-X", "faulthandler"])
        # The detached pass itself needs nothing beyond this interpreter.
        self.assertEqual(resolve_edges.engine_command(self.manifest, report, [])[-3:],
                         ["--pass", "--report-out", str(report)])

    def test_a_background_pass_is_running_while_its_process_lives(self):
        child = mock.Mock(pid=os.getpid())
        with mock.patch.object(resolve_edges, "engine_command", return_value=["engine"]), \
                mock.patch.object(resolve_edges, "_spawn_detached", return_value=child) as spawn:
            started = resolve_edges.ensure_edges(self.manifest)
            again = resolve_edges.ensure_edges(self.manifest)
        self.assertEqual((started["state"], started["action"]), ("running", "started"))
        self.assertEqual((again["state"], again["action"]), ("running", "none"))
        spawn.assert_called_once()
        self.assertEqual(spawn.call_args.args[0], ["engine"])
        ended = subprocess.Popen([sys.executable, "-c", "pass"])
        ended.wait()
        self.manifest.with_name(resolve_edges.RUNNING_NAME).write_text(
            json.dumps({"pid": ended.pid}), encoding="utf-8")
        state = resolve_edges.edge_state(self.manifest)
        self.assertEqual(state["state"], "failed")
        self.assertIn(resolve_edges.LOG_NAME, state["reason"])

    def test_the_edge_view_carries_resolution_and_names_a_running_pass(self):
        import edge_view
        self.manifest.with_name(resolve_edges.RUNNING_NAME).write_text(
            json.dumps({"pid": os.getpid(), "started_at": "2026-11-08T00:00:00Z"}), encoding="utf-8")
        view = edge_view.load_edge_view(self.manifest)
        self.assertEqual(view["coverage"]["status"], "missing_store")
        self.assertEqual(view["coverage"]["engine_pass"]["state"], "running")
        self.assertTrue(any(gap.startswith("engine pass running") for gap in view["gaps"]), view["gaps"])
        resolution = view["coverage"]["resolution"]
        self.assertEqual((resolution["resolvable"], resolution["resolved"]), (2, 0))

    def test_rewriting_a_manifest_first_ends_the_pass_over_its_old_revision(self):
        import contextlib
        import io
        running = self.manifest.with_name(resolve_edges.RUNNING_NAME)
        running.write_text(json.dumps({"pid": 4242}), encoding="utf-8")
        partial = self.manifest.with_name(".engine-edges.sqlite.abc.partial")
        partial.write_bytes(b"half a store")
        with mock.patch.object(resolve_edges, "_process_alive", return_value=True), \
                mock.patch.object(resolve_edges, "_terminate_tree") as terminate, \
                mock.patch.object(resolve_edges, "ensure_edges",
                                  return_value={"state": "running", "edges_store": "x"}), \
                contextlib.redirect_stdout(io.StringIO()):
            code = snapshot.main(["write", str(self.root), "--out", str(self.manifest), "--no-index",
                                  "--no-modules"])
        self.assertEqual(code, 0)
        terminate.assert_called_once_with(4242)
        self.assertFalse(running.exists())
        self.assertFalse(partial.exists())

    def test_snapshot_write_starts_the_pass_unless_told_not_to(self):
        import contextlib
        import io
        out = self.root.parent / "written.sqlite"
        for options, calls in (([], 1), (["--no-engine"], 0)):
            with self.subTest(options=options), \
                    mock.patch.object(resolve_edges, "ensure_edges",
                                      return_value={"state": "running", "edges_store": "x"}) as ensure, \
                    contextlib.redirect_stdout(io.StringIO()):
                code = snapshot.main(["write", str(self.root), "--out", str(out), "--no-index",
                                      "--no-modules", *options])
            self.assertEqual(code, 0)
            self.assertEqual(ensure.call_count, calls)
            if calls:
                self.assertEqual(ensure.call_args.args, (out,))


class HomonymHolderTests(unittest.TestCase):
    """Same-name calls and library-returned values in Python and TypeScript.

    Holder-only responses cannot prove provenance. Follow-up responses that name
    the actual callable can; the factory's location is never used as that proof.
    Scripted engine responses test the common grading, not LSP inference quality.
    """

    SOURCES = {
        "web/i18n.ts": "export function t(key: string): string {\n  return key;\n}\n",
        "web/title.ts": "import { t } from './i18n';\nexport function title() {\n  return t('a');\n}\n",
        "web/label.ts": ("import { useTranslation } from 'react-i18next';\nexport function label() {\n"
                         "  const { t } = useTranslation();\n  return t('b');\n}\n"),
        "web/memo.ts": ("import { useCallback } from 'react';\nfunction localT(key: string): string {\n"
                        "  return key;\n}\nexport function heading() {\n  const t = useCallback(localT, []);\n"
                        "  return t('titolo');\n}\n"),
        "app/label.py": ("import gettext\n\n\ndef label():\n"
                         "    t = gettext.translation('app', fallback=True).gettext\n    return t('b')\n"),
        "app/memo.py": ("import functools\n\n\ndef local_t(key, upper):\n    return key.upper() if upper else key\n\n\n"
                        "def heading():\n    t = functools.partial(local_t, upper=True)\n    return t('titolo')\n"),
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        self.edges = self.root.parent / "engine-edges.sqlite"
        snapshot.write_snapshot(self.root, self.manifest)

    def calls(self):
        """The `t()` call of each file, unresolved by the lexical resolver, with its line."""
        with open_snapshot(self.manifest) as store:
            names = resolve_edges.project_callee_names(store.connection)
            rows = [(row[0], row[1], _unpack(row[2])) for row in store.connection.execute(
                "SELECT id, file, payload FROM sem_references WHERE kind='call' AND last_name='t'")]
        return names, {file: (identity, payload) for identity, file, payload in rows}

    def engine(self, language):
        """Scripted answers: library calls land in packages, held `t()` calls on their variable."""
        outside = self.root.parent / "packages"
        lines = {rel: text.split("\n") for rel, text in self.SOURCES.items()}

        def at(rel, needle):
            line = next(index for index, text in enumerate(lines[rel], 1) if needle in text)
            return line, lines[rel][line - 1].index(needle)

        answers = {}
        for rel, library, holder in (("web/label.ts", "useTranslation()", "{ t }"),
                                     ("web/memo.ts", "useCallback(", "t ="),
                                     ("app/label.py", "gettext.translation", "t ="),
                                     ("app/memo.py", "functools.partial", "t =")):
            line, _column = at(rel, library)
            answers[(Path(rel).name, line)] = Definition(outside / "lib", library, line=1, column=0)
            line, column = at(rel, holder)
            column += holder.index("t")
            holder_definition = Definition(self.root / rel, "t", line=line, column=column)
            answers[(Path(rel).name, line + 1)] = holder_definition
            answers[(Path(rel).name, line, column)] = holder_definition
        line, column = at("web/i18n.ts", "t(key")
        answers[("title.ts", 3)] = Definition(self.root / "web/i18n.ts", "t", line=line, column=column)
        engine = StubEngine(answers)
        engine.languages = (language,)
        return engine

    def verdicts(self):
        for language in ("typescript", "python"):
            resolve_edges.resolve_edges(self.manifest, engine=self.engine(language), limit=None, stride=1,
                                        out=self.edges)
        with open_snapshot(self.manifest) as store:
            edges, _binding, reason = resolve_edges.read_edge_store(self.edges, store)
        self.assertIsNone(reason)
        _names, calls = self.calls()
        by_reference = {edge["reference_id"]: edge["verdict"] for edge in edges}
        return {file: by_reference.get(identity) for file, (identity, _payload) in calls.items()}

    def test_the_name_filter_asks_the_engine_about_every_held_call(self):
        names, calls = self.calls()
        self.assertEqual(sorted(calls), ["app/label.py", "app/memo.py", "web/label.ts", "web/memo.ts", "web/title.ts"])
        held = {file: resolve_edges.classify_reference(payload, names)
                for file, (_identity, payload) in calls.items() if file != "web/title.ts"}
        self.assertEqual(set(held.values()), {"askable"}, held)

    def test_a_project_function_returned_by_a_library_stays_in_the_denominator(self):
        verdicts = self.verdicts()
        self.assertEqual((verdicts["web/memo.ts"], verdicts["app/memo.py"]),
                         ("project-not-a-symbol", "project-not-a-symbol"))

    def test_a_holder_without_callable_evidence_stays_unresolved(self):
        verdicts = self.verdicts()
        self.assertEqual((verdicts["web/label.ts"], verdicts["app/label.py"]),
                         ("project-not-a-symbol", "project-not-a-symbol"))

    def test_an_engine_answer_with_holder_and_callable_is_resolved(self):
        engine = self.engine("typescript")
        holder = engine.answers[("label.ts", 4)]
        engine.answers[("label.ts", 4)] = [holder, engine.answers[("title.ts", 3)]]
        resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None, stride=1, out=self.edges)
        with open_snapshot(self.manifest) as store:
            edges, _, _ = resolve_edges.read_edge_store(self.edges, store)
        _, calls = self.calls()
        found = next(edge for edge in edges if edge["reference_id"] == calls["web/label.ts"][0])
        self.assertEqual(found["verdict"], "edge-call")

    def test_following_a_holder_uses_the_callable_not_the_factory(self):
        for language, rel in (("typescript", "web/label.ts"), ("python", "app/label.py")):
            before = resolve_edges.resolve_edges(self.manifest, engine=self.engine(language),
                                                 limit=None, stride=1, out=self.edges)["resolution"]
            engine = self.engine(language)
            for key, answer in list(engine.answers.items()):
                if len(key) == 3 and answer.module_path == self.root / rel:
                    engine.answers[key] = Definition(self.root.parent / "packages/translate", "translate")
            after = resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None,
                                                stride=1, out=self.edges)["resolution"]
            self.assertEqual(after["external"], before["external"] + 1)
            self.assertEqual(after["resolvable"], before["resolvable"] - 1)
            self.assertEqual(after["resolved"], before["resolved"])
        with open_snapshot(self.manifest) as store:
            edges, _, reason = resolve_edges.read_edge_store(self.edges, store)
        self.assertIsNone(reason)
        _, calls = self.calls()
        verdicts = {edge["reference_id"]: edge["verdict"] for edge in edges}
        for rel in ("web/memo.ts", "app/memo.py"):
            self.assertEqual(verdicts[calls[rel][0]], "project-not-a-symbol")



class ProvenanceGradingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent
        self.path = self.root / "virtual.py"
        self.external = Definition(self.root.parent / "outside.py", "external")
        self.target = Definition(self.path, "run", line=100, column=0)
        self.holder = Definition(self.path, "held", line=1, column=0)
        self.table = ({**{(n, 0): (f"holder-{n}", "binding") for n in range(1, 100)},
                       (100, 0): ("target", "function")}, set())

    def grade(self, definitions, follow):
        return resolve_edges.grade_all(definitions, {"virtual.py"}, {}, self.root,
                                       lambda _: self.table, follow=follow)

    def test_holder_beside_callable_keeps_the_confirmed_edge(self):
        verdict, target = self.grade([self.holder, self.target], lambda _: [self.holder])
        self.assertEqual((verdict, target["id"] if target else None), ("edge-call", "target"))

    def test_repeated_branches_query_each_holder_once(self):
        asked = []
        def follow(location):
            asked.append(location.line)
            if location.line == 10:
                return [self.target]
            child = Definition(self.path, "held", line=location.line + 1, column=0)
            return [child, child]
        self.assertEqual(self.grade([self.holder], follow)[0], "edge-call")
        self.assertEqual(asked, list(range(1, 11)))

    def test_mixed_internal_external_and_missing_evidence_are_not_external(self):
        for targets in ([self.target, self.external], [self.external, self.holder]):
            self.assertEqual(self.grade([self.holder], lambda _: targets)[0], "ambiguous-target")

    def test_cycle_stays_unknown(self):
        self.assertEqual(self.grade([self.holder], lambda _: [self.holder])[0], "project-not-a-symbol")

    def test_wide_graph_has_a_total_query_budget(self):
        asked = []
        def follow(location):
            asked.append(location.line)
            if location.line == 1:
                return [Definition(self.path, "held", line=n, column=0) for n in range(2, 100)]
            return [self.external]
        self.assertNotEqual(self.grade([self.holder], follow)[0], "external-definition")
        self.assertLessEqual(len(asked), 64)


class MultiLanguageTests(unittest.TestCase):
    """One store with one entry per language, written by one engine at a time."""

    SOURCES = {
        "app/use.py": "class User:\n    def go(self, helper):\n        return helper.run()\n",
        "app/tool.py": "class Tool:\n    def run(self):\n        return 1\n",
        "web/tool.ts": ("export class Tool {\n  run(): number { return 1; }\n}\n"
                        "export function make(a: string): Tool;\nexport function make(a: number): Tool;\n"
                        "export function make(a: any): Tool { return new Tool(); }\n"),
        "web/use.ts": ("import { Tool } from './tool';\nexport function go(tool: Tool) {\n  return tool.run();\n}\n"
                       "const twice = (t: Tool) => t.run();\nfoo().bar();\n"),
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        for rel, text in self.SOURCES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.write_snapshot(self.root, self.manifest)

    def declarations(self, rel):
        with open_snapshot(self.manifest) as store:
            return {(row[0], row[1]): _unpack(row[2]) for row in store.connection.execute(
                "SELECT name, kind, payload FROM sem_declarations WHERE file=? AND kind IN "
                "('function','method','class')", (rel,))}

    def python_engine(self):
        return StubEngine({("use.py", 3): Definition(self.root / "app/tool.py", "run")})

    def typescript_engine(self):
        engine = StubEngine({("use.ts", 3): Definition(self.root / "web/tool.ts", "run", line=2, column=2)})
        engine.languages = ("typescript",)
        engine.identity = lambda: "tsstub@1.0"
        return engine

    def test_tree_sitter_declarations_record_where_an_engine_names_them(self):
        tool = self.declarations("web/tool.ts")
        self.assertEqual(tool[("Tool", "class")]["name_span"][:2], [1, 13])
        self.assertEqual(tool[("run", "method")]["name_span"][:2], [2, 2])
        make = tool[("make", "function")]
        self.assertEqual(make["name_span"][:2], [6, 16])
        self.assertEqual([span[:2] for span in make["signature_spans"]], [[4, 16], [5, 16]])
        # An arrow function is named where its variable is.
        self.assertEqual(self.declarations("web/use.ts")[("twice", "function")]["name_span"][:2], [5, 6])

    def test_a_call_on_a_computed_value_keeps_its_member_name(self):
        with open_snapshot(self.manifest) as store:
            calls = [_unpack(row[0]) for row in store.connection.execute(
                "SELECT payload FROM sem_references WHERE file='web/use.ts' AND kind='call'")]
        bar = next(call for call in calls if call["parts"][-1:] == ["bar"])
        self.assertEqual((bar["parts"], bar["reason"]), (["(expr)", "bar"], "dynamic-callee"))

    def test_an_overload_signature_names_its_implementation(self):
        with open_snapshot(self.manifest) as store:
            table, ambiguous = resolve_edges.symbol_table(
                store.connection, "web/tool.ts", self.SOURCES["web/tool.ts"])
        implementation = table[(6, 16)]
        self.assertEqual(implementation[1], "function")
        self.assertEqual((table[(4, 16)], table[(5, 16)]), (implementation, implementation))
        self.assertEqual(ambiguous, set())

    def test_each_engine_keeps_the_entries_of_the_other_languages(self):
        for engine in (self.python_engine(), self.typescript_engine(), self.python_engine()):
            report = resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None, stride=1)
            self.assertTrue(report["available"], report)
        with open_snapshot(self.manifest) as store:
            edges, binding, reason = resolve_edges.read_edge_store(
                resolve_edges.default_edge_store(self.manifest), store)
        self.assertIsNone(reason, reason)
        self.assertEqual({edge["language"]: edge["resolver"] for edge in edges},
                         {"python": "stub@1.0", "typescript": "tsstub@1.0"})
        self.assertEqual({language: entry["engine"] for language, entry in binding["languages"].items()},
                         {"python": "stub@1.0", "typescript": "tsstub@1.0"})
        by_language = resolve_edges.edge_state(self.manifest)["resolution"]["by_language"]
        self.assertEqual((by_language["typescript"]["engine"], by_language["python"]["engine"]),
                         ("tsstub@1.0", "stub@1.0"))

    def stage_runner(self, outcomes, calls):
        """A fake `subprocess.run` writing each stage's report as the stage would."""
        def run(command, **_options):
            name, report = command[0], Path(command[1])
            calls.append(name)
            if outcomes[name] is not None:
                report.write_text(json.dumps(outcomes[name]), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0 if outcomes[name] else 1)
        return run

    def run_whole_pass(self, outcomes, free=8 * 2**30):
        calls = []
        report = self.manifest.with_name(resolve_edges.REPORT_NAME)
        with mock.patch.object(resolve_edges, "stage_command",
                               side_effect=lambda spec, manifest, path, environments, offline=False:
                               [spec.name, str(path)]), \
                mock.patch.object(resolve_edges, "cached_offline", return_value=False), \
                mock.patch.object(resolve_edges.subprocess, "run", side_effect=self.stage_runner(outcomes, calls)), \
                mock.patch.object(resolve_edges, "free_memory", return_value=free):
            result = resolve_edges.run_pass(self.manifest, report, [])
        return result, calls

    def test_the_pass_runs_one_engine_at_a_time_and_records_each_language(self):
        result, calls = self.run_whole_pass({
            "jedi": {"available": True, "engine": "jedi@0.20.1", "languages": {"python": {"state": "fresh"}}},
            "typescript": {"available": False, "reason": "node and npm are needed",
                           "install": "install Node.js 18 or later with npm (https://nodejs.org)"}})
        self.assertEqual(calls, ["jedi", "typescript"])
        self.assertEqual(result["languages"]["python"], {"state": "fresh", "engine": "jedi@0.20.1"})
        self.assertEqual(result["languages"]["typescript"]["state"], "unavailable")
        self.assertIn("Node.js", result["languages"]["typescript"]["install"])
        state = resolve_edges.edge_state(self.manifest)
        self.assertEqual(state["languages"]["typescript"]["state"], "unavailable")
        # No store was written by the fake stages, so Python reads as not yet passed.
        self.assertEqual(state["state"], "missing")

    def test_an_engine_that_runs_out_of_memory_starts_no_other(self):
        result, calls = self.run_whole_pass({
            "jedi": {"available": False, "reason": "MemoryError during inference", "memory_exhausted": True},
            "typescript": {"available": True}})
        self.assertEqual(calls, ["jedi"])
        self.assertEqual(result["languages"]["python"]["state"], "failed")
        self.assertEqual(result["languages"]["typescript"],
                         {"state": "failed", "engine": "typescript",
                          "reason": "not started: the jedi engine ran out of memory"})

    def test_an_engine_waits_for_free_memory(self):
        result, calls = self.run_whole_pass({"jedi": None, "typescript": None}, free=2**30)
        self.assertEqual(calls, [])
        self.assertTrue(all(outcome["state"] == "failed" and "GB of memory free" in outcome["reason"]
                            for outcome in result["languages"].values()), result)
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "failed")

    def test_a_stage_without_a_report_failed_and_says_where_to_look(self):
        result, _calls = self.run_whole_pass({"jedi": None, "typescript": {"available": True}})
        self.assertEqual(result["languages"]["python"]["state"], "failed")
        self.assertIn(resolve_edges.LOG_NAME, result["languages"]["python"]["reason"])


class DistributionTests(unittest.TestCase):
    """Work goes where it is worth most: reuse what cannot have changed, edited files first, publish as it goes."""

    SOURCES = {
        "lib.py": "def helper():\n    return 1\n\n\nclass Box:\n    def open(self):\n        return 2\n",
        "mid.py": "import lib\n\n\ndef middle(box):\n    return box.open()\n",
        "top.py": "from mid import middle\n\n\ndef run(box):\n    return box.open()\n",
        "other.py": "def alone(box):\n    return box.open()\n",
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        self.root.mkdir()
        for rel, text in self.SOURCES.items():
            (self.root / rel).write_text(text, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.write_snapshot(self.root, self.manifest)

    def engine(self, context="ctx-1", fail_after=None):
        owner = self

        class CachingEngine(StubEngine):
            """Every `open` call lands on `Box.open`; the context makes its answers reusable."""
            probes = 0

            def context(self):
                return context

            def probe(self):
                CachingEngine.probes += 1
                return super().probe()

            def definitions(self, path, line, column):
                if fail_after is not None and len(self.asked) >= fail_after:
                    raise resolve_edges.EngineFailure("the server exited")
                self.asked.append((Path(path).name, line, column))
                return [Definition(owner.root / "lib.py", "open", line=6, column=8)]

        return CachingEngine()

    def run_engine(self, engine):
        return resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None, stride=1)

    def edit(self, rel, text):
        (self.root / rel).write_text(text, encoding="utf-8")
        snapshot.write_snapshot(self.root, self.manifest)

    def test_an_unchanged_snapshot_reuses_every_answer_without_starting_the_engine(self):
        first = self.run_engine(self.engine())
        self.assertEqual((first["asked"], first["reused"], first["confirmed_edges"]), (3, 0, 3))
        again = self.engine()
        second = self.run_engine(again)
        self.assertEqual((second["asked"], second["reused"], second["confirmed_edges"]), (0, 3, 3))
        self.assertEqual((again.asked, type(again).probes), ([], 0))
        self.assertEqual(second["languages"]["python"]["state"], "fresh")
        self.assertEqual(Path(second["answer_cache"]).name, resolve_edges.ANSWERS_NAME)
        self.assertEqual(second["resolution"]["unasked"], 0)

    def test_an_edit_reasks_its_file_and_every_file_that_imports_it(self):
        self.run_engine(self.engine())
        # Every answer lands in lib.py, so editing lib.py would re-ask all of them.
        self.edit("mid.py", self.SOURCES["mid.py"] + "\n\ndef extra():\n    return 3\n")
        engine = self.engine()
        report = self.run_engine(engine)
        self.assertEqual(sorted(name for name, _line, _column in engine.asked), ["mid.py", "top.py"])
        self.assertEqual((report["reused"], report["confirmed_edges"]), (1, 3))

    def test_edited_files_are_asked_before_files_whose_imports_changed(self):
        self.run_engine(self.engine())
        (self.root / "lib.py").write_text(self.SOURCES["lib.py"] + "\n# edited\n", encoding="utf-8")
        self.edit("other.py", "# edited\n" + self.SOURCES["other.py"])
        engine = self.engine()
        self.run_engine(engine)
        self.assertEqual([name for name, _line, _column in engine.asked][0], "other.py")
        self.assertEqual(len(engine.asked), 3)

    def test_the_reusable_part_of_the_graph_is_published_before_the_engine_starts(self):
        self.run_engine(self.engine())
        self.edit("mid.py", self.SOURCES["mid.py"] + "\n\ndef extra():\n    return 3\n")
        engine, seen = self.engine(), []
        start = engine.probe

        def probe():
            with open_snapshot(self.manifest) as store:
                edges, binding, reason = resolve_edges.read_edge_store(
                    resolve_edges.default_edge_store(self.manifest), store)
            seen.append((reason, len(edges or ()), (binding or {}).get("languages", {}).get("python", {}).get("state")))
            return start()

        engine.probe = probe
        self.run_engine(engine)
        self.assertEqual(seen, [(None, 1, "partial")])

    def test_another_engine_context_reuses_nothing(self):
        self.run_engine(self.engine())
        engine = self.engine(context="ctx-2")
        report = self.run_engine(engine)
        self.assertEqual((report["asked"], report["reused"]), (3, 0))

    def test_a_failed_pass_keeps_what_it_proved_and_the_next_one_resumes(self):
        with mock.patch.object(resolve_edges, "PUBLISH_SECONDS", 0):
            failed = self.run_engine(self.engine(fail_after=2))
        self.assertFalse(failed["available"])
        with open_snapshot(self.manifest) as store:
            edges, binding, reason = resolve_edges.read_edge_store(
                resolve_edges.default_edge_store(self.manifest), store)
        self.assertIsNone(reason, reason)
        self.assertEqual((len(edges), binding["languages"]["python"]["state"]), (2, "partial"))
        self.assertEqual(resolve_edges.edge_state(self.manifest)["languages"]["python"]["state"], "sampled")
        engine = self.engine()
        resumed = self.run_engine(engine)
        self.assertEqual((resumed["asked"], resumed["reused"], resumed["confirmed_edges"]), (1, 2, 3))
        self.assertEqual(resolve_edges.edge_state(self.manifest)["state"], "fresh")

    def test_a_dry_run_asks_everything_and_writes_no_answer(self):
        self.run_engine(self.engine())
        engine = self.engine()
        report = resolve_edges.resolve_edges(self.manifest, engine=engine, limit=None, stride=1, dry_run=True)
        self.assertEqual((report["asked"], report["reused"], report["answer_cache"]), (3, 0, None))

    def test_digests_follow_imports_and_cycles(self):
        hashes = {"a": "1", "b": "2", "c": "3", "d": "4"}
        dependencies = {"a": {"b"}, "b": {"a", "c"}, "d": set()}
        before = resolve_edges.dependency_digests(hashes, dependencies)
        self.assertEqual(before["a"], before["b"])
        after = resolve_edges.dependency_digests({**hashes, "c": "changed"}, dependencies)
        self.assertNotEqual(after["a"], before["a"])
        self.assertNotEqual(after["c"], before["c"])
        self.assertEqual(after["d"], before["d"])


class ContractTests(unittest.TestCase):
    """Calls that go through a type's contract arrive at it; a value holder is never a target."""

    TYPES = "\n".join([
        "export interface Client {",
        "  get(url: string): string;",
        "  post: (url: string) => string;",
        "  json: { <T>(): T; raw(): string };",
        "  timeout: number;",
        "}",
        "export type Factory = {",
        "  (base: string): Client;",
        "};",
        "export class Box {",
        "  constructor(size: number) {}",
        "}",
        "export const box = new Box(1);",
        "",
    ])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "proj"
        self.root.mkdir()
        (self.root / "types.ts").write_text(self.TYPES, encoding="utf-8")
        self.manifest = self.root.parent / "manifest.sqlite"
        snapshot.write_snapshot(self.root, self.manifest)
        self.lines = self.TYPES.split("\n")

    def at(self, line, text, offset=0):
        return line, self.lines[line - 1].index(text) + offset

    def table(self):
        with open_snapshot(self.manifest) as store:
            return resolve_edges.symbol_table(store.connection, "types.ts", self.TYPES)

    def grade(self, *positions):
        definitions = [Definition(self.root / "types.ts", "?", line=line, column=column) for line, column in positions]
        with open_snapshot(self.manifest) as store:
            inventory = resolve_edges.inventory_files(store.connection)
            return resolve_edges.grade_all(definitions, inventory, {}, self.root, lambda rel: resolve_edges.symbol_table(
                store.connection, rel, self.TYPES))

    def test_callable_members_of_interfaces_and_types_are_contracts(self):
        table, ambiguous = self.table()
        self.assertEqual(ambiguous, set())
        for position in (self.at(2, "get"), self.at(3, "post"), self.at(4, "raw"), self.at(8, "(")):
            with self.subTest(position=position):
                self.assertEqual(table[position][1], "function")
        # A property's own call signature names the property.
        self.assertEqual(table[self.at(4, "<")], table[self.at(4, "json")])
        self.assertEqual(table[self.at(5, "timeout")][1], "binding")

    def test_a_constructor_names_its_class(self):
        table, _ambiguous = self.table()
        self.assertEqual(table[self.at(11, "constructor")], table[self.at(10, "Box")])
        verdict, target = self.grade(self.at(10, "Box"), self.at(11, "constructor"))
        self.assertEqual((verdict, target["kind"]), ("edge-instantiation", "class"))

    def test_the_value_holder_beside_a_callable_is_not_a_target(self):
        self.assertEqual(self.grade(self.at(13, "box"), self.at(2, "get"))[0], "edge-call")
        self.assertEqual(self.grade(self.at(5, "timeout")), ("project-not-a-symbol", None))

    def test_contracts_are_never_lexical_bindings(self):
        with open_snapshot(self.manifest) as store:
            rows = [_unpack(row[0]) for row in store.connection.execute(
                "SELECT payload FROM sem_declarations WHERE kind IN ('method','property')")]
        contracts = [row for row in rows if row.get("contract") or row["kind"] == "property"]
        self.assertTrue(contracts)
        self.assertTrue(all(row.get("lexical") is False for row in contracts), contracts)
        self.assertIn("Client.get", {row["qualified_name"] for row in contracts})


class JavaEngineTests(unittest.TestCase):
    def test_the_java_server_builds_nothing_downloads_nothing_and_writes_outside_the_project(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = resolve_edges.JavaEngine(Path(temp), install_dir=Path(temp) / "engines")
            engine.jre_home = Path(temp) / "jre"
            java = engine.settings()["java"]
            self.assertEqual((java["autobuild"]["enabled"], java["import"]["maven"]["enabled"],
                              java["import"]["gradle"]["enabled"]), (False, False, False))
            options = engine.initialization_options()
            self.assertEqual(options["bundles"], [])
            # Library definitions come back as class-file locations, which grade as external.
            self.assertTrue(options["extendedClientCapabilities"]["classFileContentsSupport"])
            self.assertEqual(engine.definitions.__func__, resolve_edges.LspEngine.definitions)

    def test_the_java_server_finds_the_gradle_release_list_locally(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            plugins = home / "extension" / "server" / "plugins"
            plugins.mkdir(parents=True)
            (plugins / "org.eclipse.equinox.launcher_1.jar").write_bytes(b"")
            for name in ("config_win", "config_linux", "config_mac"):
                (home / "extension" / "server" / name).mkdir()
            engine = resolve_edges.JavaEngine(Path(temp), install_dir=Path(temp) / "engines")
            engine.jre_home = Path(temp) / "jre"
            with mock.patch.object(resolve_edges.JavaEngine, "pinned",
                                   return_value={"version": "1", "jre_path": "jre/bin/java"}):
                _command, environment = engine.command(home)
            versions = Path(environment["XDG_CACHE_HOME"]) / "tooling" / "gradle" / "versions.json"
            self.assertEqual(versions.read_text(encoding="utf-8"), "[]")
            engine.cleanup()
            self.assertFalse(versions.exists())


class OfflineStageTests(unittest.TestCase):
    def test_a_cached_stage_runs_uv_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, report = Path(temp) / "manifest.sqlite", Path(temp) / "report.json"
            spec = resolve_edges.ENGINES[1]
            with mock.patch.object(resolve_edges.shutil, "which", return_value="uv"):
                online = resolve_edges.stage_command(spec, manifest, report, [])
                offline = resolve_edges.stage_command(spec, manifest, report, [], offline=True)
            self.assertNotIn("--offline", online)
            self.assertEqual(offline[:6], ["uv", "run", "--quiet", "--no-config", "--no-project", "--offline"])


class JvmLibraryTests(unittest.TestCase):
    """The project's libraries are read from its build files, never by running them, and resolved once."""

    POM = """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <parent><groupId>org.demo</groupId><artifactId>parent</artifactId><version>3</version></parent>
  <groupId>org.demo</groupId><artifactId>app</artifactId><version>1.0</version>
  <properties><guava.version>33.0-jre</guava.version></properties>
  <dependencyManagement><dependencies>
    <dependency><groupId>org.demo</groupId><artifactId>bom</artifactId><version>2</version>
      <type>pom</type><scope>import</scope></dependency>
    <dependency><groupId>junit</groupId><artifactId>junit</artifactId><version>4.13.2</version></dependency>
  </dependencies></dependencyManagement>
  <dependencies>
    <dependency><groupId>com.google.guava</groupId><artifactId>guava</artifactId><version>${guava.version}</version></dependency>
    <dependency><groupId>junit</groupId><artifactId>junit</artifactId><scope>test</scope></dependency>
    <dependency><groupId>org.slf4j</groupId><artifactId>slf4j-api</artifactId></dependency>
  </dependencies>
  <build><plugins><plugin><artifactId>maven-compiler-plugin</artifactId><dependencies>
    <dependency><groupId>org.tool</groupId><artifactId>only-for-the-build</artifactId><version>1</version></dependency>
  </dependencies></plugin></plugins></build>
</project>
"""

    def test_coordinates_come_from_poms_gradle_files_and_catalogs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pom.xml").write_text(self.POM, encoding="utf-8")
            (root / "lib").mkdir()
            (root / "lib/build.gradle.kts").write_text(
                'plugins { kotlin("jvm") version "2.0.0" }\n'
                'dependencies {\n  implementation("com.squareup.okio:okio:3.9.0")\n'
                '  implementation(kotlin("reflect"))\n  implementation(project(":app"))\n}\n', encoding="utf-8")
            (root / "gradle").mkdir()
            (root / "gradle/libs.versions.toml").write_text(
                '[versions]\nktor = "2.3.0"\n[libraries]\n'
                'ktor = { module = "io.ktor:ktor-client-core", version.ref = "ktor" }\n', encoding="utf-8")
            coordinates, boms = resolve_edges.jvm_coordinates(root)
        self.assertEqual(coordinates, [
            "com.google.guava:guava:33.0-jre", "com.squareup.okio:okio:3.9.0", "io.ktor:ktor-client-core:2.3.0",
            "junit:junit:4.13.2", "org.jetbrains.kotlin:kotlin-reflect:2.0.0", "org.slf4j:slf4j-api"])
        self.assertEqual(boms, ["org.demo:bom:2", "org.demo:parent:3"])

    def test_the_classpath_is_resolved_once_with_versions_left_to_boms_or_the_latest_stable(self):
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(resolve_edges, "shared_cache_dir", return_value=Path(temp) / "cache"):
            root = Path(temp) / "proj"
            root.mkdir()
            jar = Path(temp) / "guava.jar"
            jar.write_bytes(b"jar")
            calls = []

            def run(command, **_options):
                calls.append(command)
                return subprocess.CompletedProcess(command, 0, stdout=f"{jar}\n", stderr="")

            with mock.patch.object(resolve_edges, "jvm_coordinates",
                                   return_value=(["com.google.guava:guava", "junit:junit:4.13.2"], [])), \
                    mock.patch.object(resolve_edges, "java_runtime", return_value=Path("java")), \
                    mock.patch.object(resolve_edges, "coursier_jar", return_value=Path("coursier.jar")), \
                    mock.patch.object(resolve_edges.subprocess, "run", side_effect=run):
                first = resolve_edges.jvm_classpath(root)
                again = resolve_edges.jvm_classpath(root)
        self.assertEqual((first, again), ([jar], [jar]))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-2:], ["com.google.guava:guava:latest.stable", "junit:junit:4.13.2"])
        self.assertNotIn("m2Local", calls[0])

    def test_the_java_server_opens_an_eclipse_project_kept_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            (root / "src/main/java/org/demo").mkdir(parents=True)
            (root / "src/main/java/org/demo/App.java").write_text("package org.demo;\nclass App {}\n", encoding="utf-8")
            (root / "pom.xml").write_text(self.POM, encoding="utf-8")
            engine = resolve_edges.JavaEngine(root, install_dir=Path(temp) / "engines")
            engine.sources = [root / "src/main/java/org/demo/App.java"]
            engine.workspace = Path(temp) / "workspace"
            engine.workspace.mkdir()
            with mock.patch.object(resolve_edges, "jvm_classpath", return_value=[Path(temp) / "guava.jar"]):
                engine.describe_project()
            project = engine.workspace_root()
            description = (project / ".project").read_text(encoding="utf-8")
            classpath = (project / ".classpath").read_text(encoding="utf-8")
            self.assertIn((root / "src/main/java").as_posix(), description)
            self.assertIn("kind='src' path='source0'", classpath)
            self.assertIn((Path(temp) / "guava.jar").as_posix(), classpath)
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["pom.xml", "src"])

    def test_a_language_server_is_given_the_files_exact_line_endings(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "App.java"
            source.write_bytes(b"class App {\r\n  void run() {}\r\n}\r\n")
            _served, text = resolve_edges.LspEngine(Path(temp)).served_text(source)
        self.assertEqual(text.count("\r\n"), 3)


class TypeScriptMirrorTests(unittest.TestCase):
    def test_the_mirror_links_the_project_and_its_removal_leaves_every_target_intact(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            (root / "src/deep").mkdir(parents=True)
            (root / "src/deep/a.ts").write_text("export const a = 1;\n", encoding="utf-8")
            (root / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
            modules = Path(temp) / "shared/node_modules/pkg"
            modules.mkdir(parents=True)
            (modules / "index.d.ts").write_text("export declare const p: number;\n", encoding="utf-8")
            engine = resolve_edges.TypeScriptEngine(root, install_dir=Path(temp) / "engines")
            engine.mirror = engine.build_mirror(modules.parent)
            mirror = engine.workspace_root()
            self.assertEqual((mirror / "src/deep/a.ts").read_text(encoding="utf-8"), "export const a = 1;\n")
            self.assertTrue((mirror / "node_modules/pkg/index.d.ts").is_file())
            served, _text = engine.served_text(root / "src/deep/a.ts")
            self.assertEqual(served.resolve(), (root / "src/deep/a.ts").resolve())
            engine.cleanup()
            self.assertFalse(mirror.exists())
            self.assertTrue((root / "src/deep/a.ts").is_file())
            self.assertTrue((modules / "index.d.ts").is_file())
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["package.json", "src"])

    def test_only_the_manifests_reach_npm_and_scripts_never_run(self):
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(resolve_edges, "shared_cache_dir", return_value=Path(temp) / "cache"):
            root = Path(temp) / "proj"
            (root / "src").mkdir(parents=True)
            (root / "src/a.ts").write_text("export const a = 1;\n", encoding="utf-8")
            (root / "package.json").write_text('{"name": "demo", "devDependencies": {"ava": "^6"}}',
                                               encoding="utf-8")
            seen = []

            def run(command, cwd, **_options):
                seen.append((command, sorted(path.name for path in Path(cwd).iterdir())))
                (Path(cwd) / "node_modules").mkdir()
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with mock.patch.object(resolve_edges.shutil, "which", return_value="npm"), \
                    mock.patch.object(resolve_edges.subprocess, "run", side_effect=run):
                first = resolve_edges.npm_modules(root)
                again = resolve_edges.npm_modules(root)
        self.assertEqual(first, again)
        self.assertEqual(len(seen), 1)
        command, files = seen[0]
        self.assertEqual(files, ["package.json"])
        self.assertIn("--ignore-scripts", command)


class KotlinEngineTests(unittest.TestCase):
    def test_a_maven_jar_on_disk_is_reused_and_a_download_is_verified(self):
        import io
        payload = b"jar bytes"
        with tempfile.TemporaryDirectory() as temp,                 mock.patch.object(resolve_edges, "shared_cache_dir", return_value=Path(temp) / "cache"),                 mock.patch.object(resolve_edges.Path, "home", return_value=Path(temp) / "home"):
            local = Path(temp) / "home/.m2/repository/org/demo/lib/1.0/lib-1.0.jar"
            local.parent.mkdir(parents=True)
            local.write_bytes(payload)
            with mock.patch("urllib.request.urlopen") as urlopen:
                self.assertEqual(resolve_edges.maven_artifact("org.demo:lib:1.0"), local)
            urlopen.assert_not_called()

            def answer(url, timeout):
                digest = hashlib.sha1(payload).hexdigest().encode()
                return io.BytesIO(digest if url.endswith(".sha1") else payload)

            with mock.patch("urllib.request.urlopen", side_effect=answer):
                fetched = resolve_edges.maven_artifact("org.demo:other:2.0")
            self.assertEqual(fetched, resolve_edges.maven_central_dir() / "org/demo/other/2.0/other-2.0.jar")
            self.assertEqual(fetched.read_bytes(), payload)
            with mock.patch("urllib.request.urlopen", side_effect=lambda url, timeout: io.BytesIO(
                    b"0" * 40 if url.endswith(".sha1") else payload)),                     mock.patch.object(resolve_edges.time, "sleep"):
                with self.assertRaises(ValueError):
                    resolve_edges.maven_artifact("org.demo:broken:3.0")
            self.assertFalse((resolve_edges.maven_central_dir() / "org/demo/broken/3.0/broken-3.0.jar").exists())

    def test_the_kotlin_engine_loads_the_snapshots_kotlin_and_java_files_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            (root / "src").mkdir(parents=True)
            # `make().run()` needs a type the lexical resolver does not infer, so the engine is started.
            (root / "src/Tool.kt").write_text(
                "class Tool {\n    fun run(): Int = 1\n}\n\nfun make(): Tool = Tool()\n\nfun go(): Int = make().run()\n",
                encoding="utf-8")
            (root / "src/Help.java").write_text("class Help { int go() { return 1; } }\n", encoding="utf-8")
            (root / "notes.md").write_text("# notes\n", encoding="utf-8")
            manifest = Path(temp) / "manifest.sqlite"
            snapshot.write_snapshot(root, manifest)
            engine = resolve_edges.KotlinEngine(root)
            seen = []
            engine.probe = lambda: (seen.append(sorted(path.name for path in engine.sources)), (False, "stopped"))[1]
            report = resolve_edges.resolve_edges(manifest, engine=engine, limit=None, stride=1)
        self.assertFalse(report["available"])
        self.assertEqual(seen, [["Help.java", "Tool.kt"]])


class RustGoContractTests(unittest.TestCase):
    """A method with no body, an interface's or a trait's, is a contract; an enum variant builds through its name."""

    def table(self, name, source):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            root.mkdir()
            (root / name).write_text(source, encoding="utf-8")
            manifest = Path(temp) / "manifest.sqlite"
            snapshot.write_snapshot(root, manifest)
            with open_snapshot(manifest) as store:
                return resolve_edges.symbol_table(store.connection, name, source)

    def test_go_interface_methods_are_contracts(self):
        source = "package demo\n\ntype Router interface {\n\tRoute(pattern string)\n\tRoutes() []string\n}\n"
        table, ambiguous = self.table("demo.go", source)
        self.assertEqual(ambiguous, set())
        self.assertEqual(table[(4, source.split("\n")[3].index("Route"))][1], "function")
        self.assertEqual(table[(5, source.split("\n")[4].index("Routes"))][1], "function")

    def test_rust_trait_signatures_and_enum_variants_are_contracts(self):
        source = ("pub trait Tool {\n    fn run(&self) -> u32;\n    fn name(&self) -> u32 { 1 }\n}\n\n"
                  "pub enum Code {\n    Message(String),\n    Eof,\n}\n")
        lines = source.split("\n")
        table, ambiguous = self.table("lib.rs", source)
        self.assertEqual(ambiguous, set())
        for line, text in ((2, "run"), (3, "name"), (7, "Message")):
            with self.subTest(text=text):
                self.assertEqual(table[(line, lines[line - 1].index(text))][1], "function")


class NativeToolchainTests(unittest.TestCase):
    def test_a_toolchain_on_the_path_is_used_when_it_holds_the_standard_library_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            sysroot = Path(temp) / "sysroot"
            (sysroot / "lib/rustlib/src/rust/library").mkdir(parents=True)
            (sysroot / "bin").mkdir()
            fake = lambda name: str(sysroot / "bin" / name)
            with mock.patch.object(resolve_edges.shutil, "which", side_effect=fake), \
                    mock.patch.object(resolve_edges.subprocess, "run", return_value=subprocess.CompletedProcess(
                        [], 0, stdout=str(sysroot) + "\n", stderr="")), \
                    mock.patch.object(resolve_edges, "shared_cache_dir", return_value=Path(temp) / "cache"):
                self.assertEqual(resolve_edges.rust_toolchain(), sysroot)
            self.assertFalse((Path(temp) / "cache").exists())

    def test_without_sources_cargo_rustc_and_rust_src_come_from_the_release_and_are_verified(self):
        import io
        import tarfile
        import lzma

        def archive(component):
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w:xz") as bundle:
                payload = component.encode()
                member = tarfile.TarInfo(f"{component}-1/{component}/bin/{component}")
                member.size = len(payload)
                bundle.addfile(member, io.BytesIO(payload))
            return buffer.getvalue()

        archives = {component: archive(component) for component in ("rustc", "cargo", "rust-src")}
        manifest = "\n".join(
            f'[pkg.{name}.target.x86_64-pc-windows-msvc]\nxz_url = "https://static.rust-lang.org/{name}.tar.xz"\n'
            f'xz_hash = "{hashlib.sha256(data).hexdigest()}"\n' for name, data in archives.items())

        def answer(url, timeout=None):
            url = url if isinstance(url, str) else url.full_url
            if url.endswith(".toml"):
                return io.BytesIO(manifest.encode())
            return io.BytesIO(archives[Path(url).name.removesuffix(".tar.xz")])

        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(resolve_edges.shutil, "which", return_value=None), \
                mock.patch.object(resolve_edges, "_platform", return_value="win-x64"), \
                mock.patch.object(resolve_edges, "shared_cache_dir", return_value=Path(temp) / "cache"), \
                mock.patch("urllib.request.urlopen", side_effect=answer):
            home = resolve_edges.rust_toolchain()
            self.assertEqual(home.name, resolve_edges.RUST_VERSION)
            for component in ("rustc", "cargo", "rust-src"):
                self.assertTrue((home / "bin" / component).is_file())
            self.assertTrue((home / ".installed").is_file())
            # The second call installs nothing.
            with mock.patch("urllib.request.urlopen", side_effect=AssertionError("downloaded again")):
                self.assertEqual(resolve_edges.rust_toolchain(), home)

    def test_a_download_that_fails_its_checksum_leaves_no_toolchain(self):
        import io
        manifest = ('[pkg.rustc.target.x86_64-pc-windows-msvc]\nxz_url = "https://static.rust-lang.org/rustc.tar.xz"\n'
                    'xz_hash = "' + "0" * 64 + '"\n')
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(resolve_edges.shutil, "which", return_value=None), \
                mock.patch.object(resolve_edges, "_platform", return_value="win-x64"), \
                mock.patch.object(resolve_edges.time, "sleep"), \
                mock.patch.object(resolve_edges, "shared_cache_dir", return_value=Path(temp) / "cache"), \
                mock.patch("urllib.request.urlopen", side_effect=lambda url, timeout=None: io.BytesIO(
                    manifest.encode() if str(url).endswith(".toml") else b"not the archive")):
            self.assertIsNone(resolve_edges.rust_toolchain())
            self.assertEqual([path.name for path in (Path(temp) / "cache/engines/rust").iterdir()], [])

    def test_the_go_toolchain_is_unpacked_once_and_checked(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp) / "go.zip"
            with zipfile.ZipFile(bundle, "w") as archive:
                archive.writestr("go/bin/" + resolve_edges.executable_name("go"), "binary")
            payload = bundle.read_bytes()
            assets = {"win-x64": ("go.zip", hashlib.sha256(payload).hexdigest())}
            calls = []

            def fetch(url, target, **options):
                calls.append(url)
                target.write_bytes(payload)
                return target

            with mock.patch.object(resolve_edges, "GO_ASSETS", assets), \
                    mock.patch.object(resolve_edges, "_platform", return_value="win-x64"), \
                    mock.patch.object(resolve_edges, "download", side_effect=fetch), \
                    mock.patch.object(resolve_edges, "shared_cache_dir", return_value=Path(temp) / "cache"):
                root = resolve_edges.go_toolchain()
                self.assertTrue((root / "bin" / resolve_edges.executable_name("go")).is_file())
                self.assertEqual(resolve_edges.go_toolchain(), root)
            self.assertEqual(len(calls), 1)

    def test_a_mirror_keeps_what_the_server_writes_out_of_the_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "proj"
            (root / "src").mkdir(parents=True)
            (root / "src/lib.rs").write_bytes(b"pub fn a() {}\n")
            (root / "Cargo.toml").write_text('[package]\nname = "demo"\n', encoding="utf-8")
            (root / ".git").mkdir()
            engine = resolve_edges.RustEngine(root, install_dir=Path(temp) / "engines")
            engine.mirror = engine.build_mirror()
            mirror = engine.workspace_root()
            self.assertFalse((mirror / ".git").exists())
            (mirror / "Cargo.lock").write_text("lock", encoding="utf-8")
            served, text = engine.served_text(root / "src/lib.rs")
            self.assertEqual((served.resolve(), text), ((root / "src/lib.rs").resolve(), "pub fn a() {}\n"))
            engine.cleanup()
            self.assertFalse(mirror.exists())
            self.assertEqual(sorted(path.name for path in root.iterdir()), [".git", "Cargo.toml", "src"])
            self.assertTrue((root / "src/lib.rs").is_file())


class ScipTypedRangeTests(unittest.TestCase):
    """The current SCIP schema writes an occurrence's range as a message, with zero fields left out."""

    @staticmethod
    def varint(value):
        out = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            out.append(byte | (0x80 if value else 0))
            if not value:
                return bytes(out)

    def field(self, number, payload):
        if isinstance(payload, int):
            return self.varint(number << 3) + self.varint(payload)
        return self.varint(number << 3 | 2) + self.varint(len(payload)) + payload

    def occurrence(self, symbol, roles, *range_fields):
        single = b"".join(self.field(number, value) for number, value in range_fields if value)
        return self.field(2, self.field(8, single) + self.field(2, symbol.encode()) + self.field(3, roles))

    def test_single_line_ranges_are_read_without_their_zero_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "a.go").write_text("package a\n\nfunc Run() {}\n\nfunc Go() { Run() }\n", encoding="utf-8")
            symbol = "scip-go gomod demo . `demo`/Run()."
            document = (self.field(1, b"a.go")
                        + self.occurrence(symbol, 1, (1, 2), (2, 5), (3, 8))
                        + self.occurrence(symbol, 0, (1, 4), (2, 13), (3, 16))
                        + self.occurrence("local 0", 1, (2, 1), (3, 2)))
            index = root / "index.scip"
            index.write_bytes(self.field(2, document))
            engine = resolve_edges.ScipEngine(root, [index])
            self.assertEqual(engine.probe(), (True, ""))
            found = engine.definitions(root / "a.go", 5, 13)
        self.assertEqual([(location.line, location.column) for location in found], [(3, 5)])


class PositionUnitTests(unittest.TestCase):
    def test_positions_convert_explicitly_between_units(self):
        line = 'x = "é😀"; run()'
        byte = len(line[:line.index("run")].encode("utf-8"))
        self.assertEqual(resolve_edges.byte_to_char(line, byte), line.index("run"))
        self.assertEqual(resolve_edges.byte_to_utf16(line, byte), line.index("run") + 1)
        self.assertEqual(resolve_edges.utf16_to_byte(line, line.index("run") + 1), byte)
        self.assertEqual(resolve_edges.char_to_byte(line, line.index("run")), byte)
        # A byte inside a character and a unit inside a surrogate pair name no position.
        self.assertIsNone(resolve_edges.byte_to_char(line, line.index("é") + 1))
        self.assertIsNone(resolve_edges.utf16_to_byte(line, line.index("😀") + 1))


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
            (root / "a.py").write_text("def f(x):\n    return x.f()\n", encoding="utf-8")
            manifest = Path(temp).resolve() / "manifest.sqlite"
            snapshot.write_snapshot(root, manifest)
            stdout = io.StringIO()
            with mock.patch.dict(sys.modules, {"jedi": None}), contextlib.redirect_stdout(stdout):
                code = resolve_edges.main([str(manifest), "--engine", "jedi"])
        self.assertEqual(code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["available"])
        self.assertIn("uv run --with jedi", payload["reason"])
        self.assertEqual(payload["install"], resolve_edges.ENGINE_INSTALL)


if __name__ == "__main__":
    unittest.main()
