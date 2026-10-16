"""Mechanical delivery and publication rules for each Codebase Map mode."""

import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import snapshot


class RunControlsTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="map-controls-"))
        self.addCleanup(shutil.rmtree, self.project, True)
        (self.project / "src").mkdir()
        self.root = self.project / ".codebase-map"
        self.run = self.root / "runs/current"
        self.run.mkdir(parents=True)
        self.state = {
            "run_id": "current", "target": "src", "mode": "classic",
            "status": "in_progress", "parent_run": None, "incremental": None,
            "flags": {"depth": "full", "critical": False, "comments": False,
                      "docs_only": False, "phase": None},
        }
        self.save_state()
        self.write("snapshot/manifest.json", json.dumps(snapshot.build_manifest(self.project / "src")))

    def write(self, name, content="# Evidence\n", run=None):
        path = (run or self.run) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def save_state(self):
        self.write("state.json", json.dumps(self.state))

    def invoke(self, *args, run=None):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "snapshot.py"), args[0],
             str(run or self.run), *map(str, args[1:])],
            capture_output=True, text=True,
        )
        try:
            result = json.loads(proc.stdout)
        except ValueError:
            result = {"stdout": proc.stdout, "stderr": proc.stderr}
        return proc.returncode, result

    def prepare(self, *args):
        code, result = self.invoke("prepare", *args)
        self.assertEqual(code, 0, result)
        return result

    def deliver(self, *phases):
        self.write("knowledge/navigation.md")
        self.write("knowledge/documentation-leads.md")
        for phase in phases:
            self.write(snapshot.PHASE_FILES[phase - 1])

    def check(self):
        return self.invoke("check", "--json")

    def test_full_delivery_publishes_only_when_every_artifact_is_nonempty(self):
        plan = self.prepare()
        self.assertEqual(plan["run_phases"], list(range(8)))
        self.deliver(1, 2, 3, 4, 5, 6)
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertIn("07-final-report.md", result["missing"])
        self.assertEqual(result["first_incomplete_phase"], 7)
        self.write("07-final-report.md", " \n")
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertIn("07-final-report.md", result["empty"])
        self.write("07-final-report.md")
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["may_publish"])

    def test_lite_skips_without_reporting_missing_and_rejects_unexpected_outputs(self):
        self.state["flags"]["depth"] = "lite"
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 5, 7)
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["may_publish"])
        self.write("03-flows.md")
        self.write("09-fabricated.md")
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(result["unexpected"], ["03-flows.md", "09-fabricated.md"])

    def test_phase_and_docs_only_are_partial_even_after_resume(self):
        for flags, phase in (({"phase": 3}, 3), ({"docs_only": True}, 6)):
            with self.subTest(flags=flags):
                shutil.rmtree(self.run)
                self.run.mkdir()
                self.state["flags"].update({"phase": None, "docs_only": False, **flags})
                self.save_state()
                self.write("snapshot/manifest.json", json.dumps(snapshot.build_manifest(self.project / "src")))
                plan = self.prepare()
                self.assertEqual(plan["run_phases"], [0, phase])
                self.deliver(phase)
                code, result = self.check()
                self.assertEqual(code, 0, result)
                self.assertFalse(result["may_publish"])
                self.prepare("--resume-from", phase, "--run-name", "current")
                self.assertFalse(self.check()[1]["may_publish"])

    def test_invalid_single_phase_and_stop_combinations_write_nothing(self):
        before = (self.run / "state.json").read_bytes()
        for args in (("--phase", 7), ("--phase", 0), ("--phase", 2, "--stop-after", 4),
                     ("--stop-after", 7), ("--stop-after", 0)):
            with self.subTest(args=args):
                self.assertNotEqual(self.invoke("prepare", *args)[0], 0)
                self.assertEqual((self.run / "state.json").read_bytes(), before)
        self.state["flags"]["docs_only"] = True
        self.save_state()
        self.assertEqual(self.invoke("prepare", "--stop-after", 4)[0], 2)

    def test_stopped_run_reports_later_work_then_resume_completes_same_run(self):
        plan = self.prepare("--stop-after", 4)
        self.assertEqual(plan["run_phases"], [0, 1, 2, 3, 4])
        self.deliver(1, 2, 3, 4)
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertFalse(result["complete"])
        self.assertFalse(result["may_publish"])
        self.assertEqual(result["first_incomplete_phase"], 5)
        self.assertEqual(result["not_yet_produced"], ["05-risks.md", "06-documentation.md", "07-final-report.md"])
        prior = (self.run / "01-structure.md").read_bytes()
        plan = self.prepare("--resume-from", "--run-name", "current")
        self.assertEqual(plan["resume_from"], 5)
        self.assertIsNone(plan["stop_after"])
        self.assertEqual(plan["run_phases"], [5, 6, 7])
        self.assertEqual(plan["artifacts"]["01-structure.md"]["status"], "inherited")
        self.assertEqual((self.run / "01-structure.md").read_bytes(), prior)
        self.deliver(5, 6, 7)
        self.assertTrue(self.check()[1]["may_publish"])

    def test_automatic_resume_starts_at_empty_or_stale_artifact(self):
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.write("02-interfaces.md", "")
        self.assertEqual(self.prepare("--resume-from", "--run-name", "current")["resume_from"], 2)
        self.write("02-interfaces.md")
        self.write("03-flows.md", "<!-- xray:stale cites=src/a.py::a -->\n# claim\n")
        self.assertEqual(self.check()[1]["first_incomplete_phase"], 3)

    def test_explicit_resume_refuses_bad_earlier_artifact_and_immutable_flag_changes(self):
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        before = (self.run / "state.json").read_bytes()
        for args in (("--resume-from", 4, "--run-name", "different"),
                     ("--resume-from", 4),
                     ("--resume-from", 4, "--run-name", "current", "--mode", "team"),
                     ("--resume-from", 4, "--run-name", "current", "--flags", '{"depth":"lite"}'),
                     ("--resume-from", 0, "--run-name", "current"),
                     ("--resume-from", 8, "--run-name", "current")):
            with self.subTest(args=args):
                self.assertEqual(self.invoke("prepare", *args)[0], 2)
                self.assertEqual((self.run / "state.json").read_bytes(), before)
        self.write("01-structure.md", "")
        self.assertEqual(self.invoke("prepare", "--resume-from", 4, "--run-name", "current")[0], 1)

    def test_resume_provenance_rejects_changed_earlier_bytes_or_snapshot(self):
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.prepare("--resume-from", 7, "--run-name", "current")
        self.write("01-structure.md", "Changed earlier evidence\n")
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertIn("01-structure.md", result["invalid_inherited"])
        self.assertIsNone(result["first_incomplete_phase"])

    def test_comment_health_is_required_only_when_non_lite_phase6_runs(self):
        self.state["flags"]["comments"] = True
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.assertIn("comment_health.md", self.check()[1]["missing"])
        self.write("comment_health.md")
        self.assertIn("06-documentation.md", self.check()[1]["empty"])
        self.write("06-documentation.md", "# Documentation\n\n## Comment Quality\nNo changes proposed.\n")
        self.assertTrue(self.check()[1]["may_publish"])

    def test_publisher_removes_previous_team_and_full_only_files_preserving_other_runs(self):
        self.state["flags"]["depth"] = "lite"
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 5, 7)
        for name in snapshot.PHASE_FILES:
            self.write(name, "Previous mirror\n", run=self.root)
        foreign = self.write("runs/other/keep.md", "foreign\n", run=self.root)
        self.write("runs.json", json.dumps({"schema": 2, "active": [{"run_id": "current"}, {"run_id": "other"}], "latest_completed": "old"}), run=self.root)
        code, result = self.invoke("publish")
        self.assertEqual(code, 0, result)
        self.assertFalse(any((self.root / name).exists() for name in ("03-flows.md", "04-semantics.md", "06-documentation.md", "08-interconnect-map.md")))
        self.assertEqual(foreign.read_text(), "foreign\n")
        self.assertEqual(json.loads((self.root / "runs.json").read_text())["active"], [{"run_id": "other"}])
        self.assertEqual(json.loads((self.root / "state.json").read_text())["run_id"], "current")

    def test_partial_and_failed_deliveries_cannot_replace_mirror(self):
        self.prepare("--phase", 3)
        self.deliver(3)
        mirror = self.write("01-structure.md", "Keep\n", run=self.root)
        self.assertEqual(self.invoke("publish")[0], 1)
        self.assertEqual(mirror.read_text(), "Keep\n")

    def update_parent(self, mode="classic", partial=False):
        parent = self.root / "runs/parent"
        parent.mkdir()
        parent_state = {**self.state, "run_id": "parent", "mode": mode,
                        "status": "in_progress" if partial else "complete"}
        self.write("state.json", json.dumps(parent_state), run=parent)
        self.write("snapshot/manifest.json", (self.run / "snapshot/manifest.json").read_text(), run=parent)
        for phase in range(1, 5 if partial else 9):
            self.write(snapshot.PHASE_FILES[phase - 1], run=parent)
        self.state.update(parent_run="parent", incremental={})
        self.save_state()
        self.write("changes.json", json.dumps({
            "parent_run": "parent", "renumber": {},
            "files": {"modified": [], "added": [], "removed": []},
            "claims": [], "symbols": {"added": []},
        }))
        self.write("changes.md", "\n".join(f"## {heading}\nNone.\n" for heading in
                   ("Claims confirmed", "Claims revised", "Claims retired", "Claims added", "Extra reads")))
        return parent

    def test_update_accepts_mechanical_carry_and_rejects_forged_or_changed_provenance(self):
        parent = self.update_parent()
        code, result = self.invoke("carry", self.run, run=parent)
        self.assertEqual(code, 0, result)
        plan = self.prepare()
        self.assertEqual(plan["artifacts"]["01-structure.md"]["status"], "inherited")
        self.deliver(7)
        self.assertTrue(self.check()[1]["may_publish"])
        state = json.loads((self.run / "state.json").read_text())
        state["delivery"]["artifacts"]["01-structure.md"]["provenance"] = {"kind": "carry", "run_id": "parent"}
        self.write("state.json", json.dumps(state))
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertIn("01-structure.md", result["invalid_inherited"])

    def test_stopped_update_defers_stale_later_claims_until_resume(self):
        parent = self.update_parent()
        self.write("05-risks.md", "<!-- xray:stale reason=changed -->\n# old risk\n", run=parent)
        self.invoke("carry", self.run, run=parent)
        self.prepare("--stop-after", 4)
        self.deliver()
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertFalse(result["may_publish"])
        self.assertEqual(result["stale"], [{"artifact": "05-risks.md", "line": 1, "deferred": True}])
        self.assertEqual(result["first_incomplete_phase"], 5)
        plan = self.prepare("--resume-from", "--run-name", "current")
        self.assertEqual(plan["resume_from"], 5)
        self.assertEqual(self.check()[0], 1)
        self.write("05-risks.md")
        self.write("07-final-report.md")
        self.assertTrue(self.check()[1]["may_publish"])

    def test_missing_later_partial_team_parent_artifacts_are_produced_in_classic_child(self):
        parent = self.update_parent(mode="team", partial=True)
        self.state["parent_phases"] = [1, 2, 3, 4]
        self.save_state()
        self.write("08-interconnect-map.md", run=parent)
        self.invoke("carry", self.run, run=parent)
        plan = self.prepare("--stop-after", 4)
        self.assertEqual(plan["artifacts"]["01-structure.md"]["status"], "inherited")
        self.assertEqual(plan["artifacts"]["05-risks.md"]["status"], "produced")
        self.assertFalse((self.run / "08-interconnect-map.md").exists())
        self.deliver()
        self.assertEqual(self.check()[0], 0)
        self.assertTrue((parent / "08-interconnect-map.md").exists())

    def test_added_symbol_and_missing_update_completion_sections_block_publication(self):
        self.update_parent()
        changes = json.loads((self.run / "changes.json").read_text())
        changes["symbols"]["added"] = [{"file": "src/new.py", "symbol": "new", "kind": "function"}]
        self.write("changes.json", json.dumps(changes))
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.write("changes.md", "# Pending update\n")
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(result["undocumented_added"], ["src/new.py::new"])
        self.assertEqual(result["first_incomplete_phase"], 1)
        self.assertIn("changes.md", result["empty"])

    def test_source_byte_change_blocks_resume_and_publication_without_mutating_state(self):
        (self.project / "src/new.py").write_bytes(b"X = 1\n")
        self.write("snapshot/manifest.json", json.dumps(snapshot.build_manifest(self.project / "src")))
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        (self.project / "src/new.py").write_bytes(b"X = 1\r\n")
        before = (self.run / "state.json").read_bytes()
        code, result = self.invoke("prepare", "--resume-from", 7, "--run-name", "current")
        self.assertEqual(code, 2)
        self.assertIn("worktree bytes changed", result["error"])
        self.assertEqual(self.invoke("publish")[0], 2)
        self.assertEqual((self.run / "state.json").read_bytes(), before)

    def test_snapshot_change_invalidates_same_run_inheritance(self):
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.prepare("--resume-from", 7, "--run-name", "current")
        manifest = json.loads((self.run / "snapshot/manifest.json").read_text())
        manifest["created_at"] = "changed"
        self.write("snapshot/manifest.json", json.dumps(manifest))
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertIn("01-structure.md", result["invalid_inherited"])

    def test_team_requires_interconnect_except_when_explicitly_skipped(self):
        self.state["mode"] = "team"
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(result["first_incomplete_phase"], 8)
        self.write("08-interconnect-map.md")
        self.assertTrue(self.check()[1]["may_publish"])

    def test_team_skip_flags_deliver_only_the_requested_consolidated_reports(self):
        cases = (
            (False, False, (1, 2, 3, 4, 5, 6, 7, 8), True),
            (False, True, (1, 2, 3, 4, 5, 6, 7), True),
            (True, False, (), False),
            (True, True, (), False),
        )
        for skip_synthesis, skip_interconnect, phases, may_publish in cases:
            with self.subTest(skip_synthesis=skip_synthesis, skip_interconnect=skip_interconnect):
                shutil.rmtree(self.run)
                self.run.mkdir()
                self.state["mode"] = "team"
                self.state["flags"].update(skip_synthesis=skip_synthesis,
                                           skip_interconnect=skip_interconnect)
                self.save_state()
                self.write("snapshot/manifest.json", json.dumps(snapshot.build_manifest(self.project / "src")))
                self.prepare()
                self.deliver(*phases)
                code, result = self.check()
                self.assertEqual(code, 0, result)
                self.assertEqual(result["may_publish"], may_publish)
                if skip_synthesis:
                    self.assertFalse((self.run / "07-final-report.md").exists())
                    self.assertFalse((self.run / "08-interconnect-map.md").exists())

    def test_team_comment_delivery_uses_owned_partition_and_consolidated_sections(self):
        self.state.update(mode="team", partitions=[{"name": "api", "status": "done"},
                                                    {"name": "web", "status": "done"}])
        self.state["flags"]["comments"] = True
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7, 8)
        for name in ("06-documentation.md", "partitions/api/06-documentation.md",
                     "partitions/web/06-documentation.md"):
            self.write(name, "# Documentation\n\n## Comment Quality\nNo issues found.\n")
        self.assertFalse((self.run / "comment_health.md").exists())
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["may_publish"])

    def test_team_comment_delivery_rejects_missing_empty_or_unreported_partition_work(self):
        self.state.update(mode="team", partitions=[{"name": "api", "status": "done"},
                                                    {"name": "web", "status": "done"}])
        self.state["flags"]["comments"] = True
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7, 8)
        self.write("06-documentation.md", "# Documentation\n\n## Comment Quality\nSee partition reports.\n")
        self.write("partitions/api/06-documentation.md", "## Comment Quality\nNo issues found.\n")
        code, result = self.check()
        self.assertEqual(code, 1, result)
        self.assertIn("partitions/web/06-documentation.md", result["missing"])
        self.assertFalse(result["may_publish"])
        for content in ("", "# Documentation\n", "## Comment Quality\n\n## Source reading\nEvidence.\n"):
            with self.subTest(content=content):
                self.write("partitions/web/06-documentation.md", content)
                code, result = self.check()
                self.assertEqual(code, 1, result)
                self.assertIn("partitions/web/06-documentation.md", result["empty"])
                self.assertEqual(result["first_incomplete_phase"], 6)
        self.write("partitions/web/06-documentation.md", "## Comment Quality\nNo issues found.\n")
        self.write("06-documentation.md", "# Documentation\n")
        self.assertIn("06-documentation.md", self.check()[1]["empty"])

    def test_team_skipped_synthesis_still_requires_partition_comment_work(self):
        self.state.update(mode="team", partitions=[{"name": "api", "status": "done"}])
        self.state["flags"].update(comments=True, skip_synthesis=True)
        self.save_state()
        self.prepare()
        self.deliver()
        self.assertIn("partitions/api/06-documentation.md", self.check()[1]["missing"])
        self.write("partitions/api/06-documentation.md", "## Comment Quality\nNo issues found.\n")
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertFalse(result["may_publish"])

    def test_team_lite_with_comments_has_no_phase_six_delivery(self):
        self.state.update(mode="team", partitions=[{"name": "api", "status": "done"}])
        self.state["flags"].update(comments=True, depth="lite")
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 5, 7, 8)
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["may_publish"])

    def test_team_comment_delivery_rejects_unconfined_partition_names(self):
        self.state.update(mode="team", partitions=[{"name": "../foreign"}])
        self.state["flags"]["comments"] = True
        self.save_state()
        before = (self.run / "state.json").read_bytes()
        code, result = self.invoke("prepare")
        self.assertEqual(code, 2, result)
        self.assertEqual((self.run / "state.json").read_bytes(), before)

    def test_missing_phase0_lead_is_first_recovery_phase(self):
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        (self.run / "knowledge/documentation-leads.md").unlink()
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(result["first_incomplete_phase"], 0)
        self.assertEqual(self.prepare("--resume-from", "--run-name", "current")["run_phases"], list(range(8)))

    def test_publisher_rolls_back_prior_mirror_and_registry_on_replace_failure(self):
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.write("01-structure.md", "Previous structure\n", run=self.root)
        self.write("08-interconnect-map.md", "Previous map\n", run=self.root)
        self.write("state.json", '{"run_id":"old"}\n', run=self.root)
        self.write("runs.json", '{"schema":2,"active":[],"latest_completed":"old"}\n', run=self.root)
        # The coordination lock persists independently of mirror publication.
        lock = snapshot._acquire_registry_lock(self.root)
        lock.unlink()
        before = {path.name: path.read_bytes() for path in self.root.iterdir() if path.is_file()}
        replace = snapshot.os.replace

        def fail_second(source, destination):
            if Path(destination) == self.root / "02-interfaces.md":
                raise OSError("injected filesystem failure")
            return replace(source, destination)

        with mock.patch.object(snapshot.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "injected"):
                snapshot.publish_run(self.run)
        after = {path.name: path.read_bytes() for path in self.root.iterdir() if path.is_file()}
        self.assertEqual(after, before)
        self.assertEqual(json.loads((self.run / "state.json").read_text())["status"], "in_progress")

    def test_registry_registration_is_idempotent_and_removes_only_its_own_entry(self):
        self.state["started_at"] = "2026-10-14T10:00:00Z"
        self.save_state()
        foreign = {"run_id": "other", "target": "elsewhere", "mode": "team", "custom": "keep"}
        self.write("runs.json", json.dumps({"schema": 2, "active": [foreign],
                                          "latest_completed": "previous"}), run=self.root)
        for _ in range(2):
            code, result = self.invoke("register")
            self.assertEqual(code, 0, result)
        registry = json.loads((self.root / "runs.json").read_text())
        self.assertEqual(registry["active"], [foreign, {
            "run_id": "current", "target": "src", "mode": "classic",
            "started_at": "2026-10-14T10:00:00Z", "parent_run": None,
        }])
        self.assertEqual(registry["latest_completed"], "previous")
        for _ in range(2):
            code, result = self.invoke("unregister")
            self.assertEqual(code, 0, result)
        registry = json.loads((self.root / "runs.json").read_text())
        self.assertEqual(registry["active"], [foreign])
        self.assertEqual(registry["latest_completed"], "previous")

    def test_registration_waits_for_publication_and_preserves_both_registry_changes(self):
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.write("runs.json", json.dumps({"schema": 2, "active": [{"run_id": "current"}],
                                          "latest_completed": None}), run=self.root)
        other = self.root / "runs/new-run"
        other.mkdir()
        self.write("state.json", json.dumps({**self.state, "run_id": "new-run",
                                             "started_at": "2026-10-14T10:01:00Z"}), run=other)
        release = self.project / "release-publication"
        publisher_code = """import json, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import snapshot
original = snapshot.check_delivery
calls = 0
def staged_check(run):
    global calls
    result = original(run)
    calls += 1
    if calls == 2:
        print('staged', flush=True)
        deadline = time.monotonic() + 10
        while not Path(sys.argv[3]).exists():
            if time.monotonic() >= deadline:
                raise RuntimeError('test did not release publication')
            time.sleep(0.01)
    return result
snapshot.check_delivery = staged_check
print(json.dumps(snapshot.publish_run(Path(sys.argv[2]))), flush=True)
"""
        registrar_code = """import sys
sys.path.insert(0, sys.argv[1])
import snapshot
print('registering', flush=True)
raise SystemExit(snapshot.main(['register', sys.argv[2]]))
"""
        publisher = subprocess.Popen([sys.executable, "-u", "-c", publisher_code,
                                      str(SCRIPTS), str(self.run), str(release)],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        registrar = None
        try:
            self.assertEqual(publisher.stdout.readline().strip(), "staged")
            registrar = subprocess.Popen([sys.executable, "-u", "-c", registrar_code,
                                          str(SCRIPTS), str(other)],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(registrar.stdout.readline().strip(), "registering")
            with self.assertRaises(subprocess.TimeoutExpired):
                registrar.communicate(timeout=0.2)
            release.write_text("continue", encoding="utf-8")
            published, publish_error = publisher.communicate(timeout=15)
            registered, register_error = registrar.communicate(timeout=15)
            self.assertEqual(publisher.returncode, 0, publish_error)
            self.assertTrue(json.loads(published)["published"])
            self.assertEqual(registrar.returncode, 0, register_error or registered)
            registry = json.loads((self.root / "runs.json").read_text())
            self.assertEqual([entry["run_id"] for entry in registry["active"]], ["new-run"])
            self.assertEqual(registry["latest_completed"], "current")
        finally:
            release.write_text("continue", encoding="utf-8")
            for process in (publisher, registrar):
                if process is not None:
                    try:
                        process.communicate(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()

    def test_unconfined_identity_or_linked_output_is_rejected(self):
        self.state["run_id"] = "different"
        self.save_state()
        self.assertEqual(self.invoke("prepare")[0], 2)
        self.state["run_id"] = "current"
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        with mock.patch.object(Path, "is_symlink", autospec=True,
                               side_effect=lambda path: path == self.run / "01-structure.md"):
            with self.assertRaisesRegex(snapshot.RunControlError, "linked path"):
                snapshot.check_delivery(self.run)

    def test_initial_update_refuses_missing_or_partial_carry_proof_without_state_write(self):
        parent = self.update_parent()
        self.invoke("carry", self.run, run=parent)
        carry_path = self.run / "carry.json"
        original = carry_path.read_bytes()
        before = (self.run / "state.json").read_bytes()
        for corruption in (None, "missing-entry", "wrong-hash"):
            with self.subTest(corruption=corruption):
                if corruption is None:
                    carry_path.unlink()
                else:
                    record = json.loads(original)
                    if corruption == "missing-entry":
                        record["artifacts"].pop("01-structure.md")
                    else:
                        record["artifacts"]["01-structure.md"]["sha256"] = "0" * 64
                    self.write("carry.json", json.dumps(record))
                code, result = self.invoke("prepare")
                self.assertEqual(code, 2, result)
                self.assertEqual((self.run / "state.json").read_bytes(), before)
                carry_path.write_bytes(original)

    def test_invalid_inherited_proof_never_becomes_produced_on_resume(self):
        parent = self.update_parent()
        self.invoke("carry", self.run, run=parent)
        self.prepare()
        self.deliver(7)
        original = (self.run / "state.json").read_bytes()
        for corruption in ("wrong-hash", "missing-provenance", "missing-file", "empty-file"):
            with self.subTest(corruption=corruption):
                state = json.loads(original)
                inherited = state["delivery"]["artifacts"]["01-structure.md"]
                if corruption == "wrong-hash":
                    inherited["provenance"]["sha256"] = "0" * 64
                elif corruption == "missing-provenance":
                    inherited.pop("provenance")
                elif corruption == "missing-file":
                    (self.run / "01-structure.md").unlink()
                else:
                    self.write("01-structure.md", "")
                self.write("state.json", json.dumps(state))
                before = (self.run / "state.json").read_bytes()
                checked = self.check()[1]
                self.assertIsNone(checked["first_incomplete_phase"])
                for args in (("--resume-from", "--run-name", "current"),
                             ("--resume-from", 1, "--run-name", "current")):
                    code, result = self.invoke("prepare", *args)
                    self.assertNotEqual(code, 0, result)
                    self.assertEqual((self.run / "state.json").read_bytes(), before)
                self.write("01-structure.md")

    def test_initial_prepare_requires_valid_confined_snapshot_before_state_write(self):
        path = self.run / "snapshot/manifest.json"
        subprocess.run(["git", "init", "--quiet", str(self.project)], check=True,
                       capture_output=True, text=True)
        (self.project / "src/existing.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.write("snapshot/manifest.json", json.dumps(snapshot.build_manifest(self.project / "src")))
        original = path.read_bytes()
        valid = json.loads(original)
        self.assertEqual(Path(valid["root"]).resolve(), self.project.resolve())
        self.assertEqual(valid["target"], "src")
        entry = next(iter(valid["files"].values()))
        before = (self.run / "state.json").read_bytes()
        variants = (
            None,
            {"schema": 1, "root": self.project.as_posix(), "target": "different", "files": {}},
            {**valid, "files": {"../outside.py": entry}},
            {**valid, "files": {"AGENTS.md": entry}},
        )
        for manifest in variants:
            with self.subTest(manifest=manifest):
                if manifest is None:
                    path.unlink()
                else:
                    self.write("snapshot/manifest.json", json.dumps(manifest))
                code, result = self.invoke("prepare")
                self.assertEqual(code, 2, result)
                self.assertEqual((self.run / "state.json").read_bytes(), before)
                path.write_bytes(original)
        self.state["target"] = str(self.project.parent / "outside-target")
        self.save_state()
        self.write("snapshot/manifest.json", json.dumps({"schema": 1,
                   "root": self.project.parent.as_posix(), "target": "outside-target", "files": {}}))
        before = (self.run / "state.json").read_bytes()
        self.assertEqual(self.invoke("prepare")[0], 2)
        self.assertEqual((self.run / "state.json").read_bytes(), before)

    def test_team_failed_or_pending_coverage_keeps_global_warning_report_unpublished(self):
        self.state.update(mode="team", partitions=[{"name": "api", "status": "done"}],
                          agents_spawned=[{"name": "P0.A", "partition": "api", "status": "delivered"}])
        self.save_state()
        self.prepare()
        self.deliver(1, 2, 3, 4, 5, 6, 7, 8)
        original = json.loads((self.run / "state.json").read_text())
        for ledger, status in (("partitions", "failed"), ("partitions", "pending"),
                               ("partitions", "structure_done"), ("partitions", None),
                               ("agents_spawned", "failed"), ("agents_spawned", "dispatched"),
                               ("agents_spawned", None)):
            with self.subTest(ledger=ledger, status=status):
                state = json.loads(json.dumps(original))
                state[ledger][0]["status"] = status
                self.write("state.json", json.dumps(state))
                code, result = self.check()
                self.assertEqual(code, 1, result)
                self.assertTrue(result["coverage_gaps"])
                self.assertFalse(result["complete"])
                self.assertFalse(result["may_publish"])
                self.assertEqual(self.invoke("publish")[0], 1)
                self.assertTrue((self.run / "07-final-report.md").exists())
                self.assertFalse((self.root / "07-final-report.md").exists())
        self.write("state.json", json.dumps(original))
        self.assertTrue(self.check()[1]["may_publish"])

    def test_stopped_update_only_defers_produced_work_and_preserves_later_inheritance(self):
        parent = self.update_parent()
        self.invoke("carry", self.run, run=parent)
        self.prepare("--stop-after", 4)
        self.deliver()
        checked = self.check()[1]
        self.assertEqual(checked["first_incomplete_phase"], 7)
        self.assertEqual(checked["not_yet_produced"], ["07-final-report.md", "changes.md"])
        original = (self.run / "state.json").read_bytes()
        self.write("05-risks.md", "Changed inherited claim\n")
        checked = self.check()[1]
        self.assertIn("05-risks.md", checked["invalid_inherited"])
        self.assertEqual(checked["first_incomplete_phase"], 7)
        self.assertNotEqual(self.invoke("prepare", "--resume-from", "--run-name", "current")[0], 0)
        self.assertEqual((self.run / "state.json").read_bytes(), original)
        self.write("05-risks.md")
        resumed = self.prepare("--resume-from", "--run-name", "current")
        self.assertEqual(resumed["run_phases"], [7])
        self.assertEqual(resumed["artifacts"]["05-risks.md"]["status"], "inherited")
        self.deliver(7)
        self.assertTrue(self.check()[1]["may_publish"])

    def test_rederived_update_output_is_not_revalidated_against_the_old_carry_hash(self):
        parent = self.update_parent()
        self.write("01-structure.md", "<!-- xray:stale reason=changed -->\nOld claim.\n", run=parent)
        self.invoke("carry", self.run, run=parent)
        self.prepare()
        self.deliver(1, 7)
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["may_publish"])

    def test_python310_reparse_point_is_rejected_without_is_junction(self):
        candidate = self.run / "01-structure.md"
        self.write("01-structure.md")
        original_lstat = Path.lstat

        def reparse(path):
            if path == candidate:
                return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
            return original_lstat(path)

        with mock.patch.object(Path, "is_symlink", return_value=False), \
             mock.patch.object(Path, "lstat", autospec=True, side_effect=reparse):
            with self.assertRaisesRegex(snapshot.RunControlError, "linked path"):
                snapshot._reject_links(candidate)


if __name__ == "__main__":
    unittest.main()
