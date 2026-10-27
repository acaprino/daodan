"""Public CLI contracts for Science Mode and its local evidence archive.

Fixtures are synthetic storage records, never evidence about actual papers.
"""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "plugins/research/skills/science-based-approach/scripts/science_runtime.py"


class ScienceResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="science contract ")
        self.addCleanup(self.remove_owned_temp)
        self.base = Path(self.temp.name)
        self.project = self.base / "project with spaces"
        self.project.mkdir()
        self.serial = 0

    def remove_owned_temp(self):
        self.assertTrue(self.base.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.temp.cleanup()

    def snapshot(self, root=None):
        root = root or self.project
        return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in root.rglob("*") if p.is_file()}

    def payload_file(self, value):
        self.serial += 1
        path = self.base / f"payload-{self.serial}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def command(self, command, *args, payload=None, project=None):
        argv = [sys.executable, str(CLI), command]
        if command != "hook":
            argv += ["--project", str(project or self.project)]
        argv += list(map(str, args))
        if payload is not None:
            argv += ["--payload", str(self.payload_file(payload))]
        return argv

    def run_cli(self, command, *args, payload=None, project=None, stdin=None, code=0):
        result = subprocess.run(self.command(command, *args, payload=payload, project=project),
                                input=stdin, capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        stream = result.stdout if code == 0 else result.stderr
        return json.loads(stream) if stream.strip() else None

    def preference(self, enabled, expected=0, project=None):
        return self.run_cli("mode", "on" if enabled else "off", "--expected-revision", expected,
                            "--source", "synthetic user request", project=project)

    def publication(self, number=1, research_id="synthetic-study", path="docs/research/synthetic-study"):
        return {"id": research_id, "path": path, "operation_id": f"publication-{research_id}-{number}",
                "expected_revision": number - 1, "title": "Synthetic storage fixture",
                "question": "Can the archive preserve this test document?", "owner": "research",
                "reason": f"Synthetic revision {number}", "topics": ["synthetic", "storage"],
                "known_consumers": ["synthetic-consumer"],
                "document": f"# Synthetic fixture {number}\n\nNot a real paper or scientific claim.\n",
                "check": {"id": f"publication-check-{research_id}-{number}",
                          "status": "completed-with-change", "summary": "Synthetic fixture published",
                          "coverage": ["storage contract only"], "limitations": ["No scientific evidence"]}}

    def check_payload(self, identity, status="completed-no-change", expected=1):
        return {"id": "synthetic-study", "expected_revision": expected,
                "check": {"id": identity, "status": status, "summary": "Synthetic check fixture",
                          "coverage": ["storage contract only"], "limitations": ["No network research"]}}

    def test_default_mode_and_repeated_on_do_not_create_state(self):
        before = self.snapshot()
        result = self.run_cli("mode")
        self.assertTrue(result["enabled"])
        self.assertEqual(result["revision"], 0)
        self.assertFalse(self.preference(True)["changed"])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.project / ".daodan").exists())

    def test_mode_is_persistent_idempotent_and_rejects_stale_revision(self):
        self.assertTrue(self.preference(False)["changed"])
        before = self.snapshot()
        self.assertFalse(self.preference(False, 1)["changed"])
        self.assertEqual(self.snapshot(), before)
        self.run_cli("mode", "on", "--expected-revision", 0, "--source", "stale request", code=2)
        self.assertEqual(self.snapshot(), before)
        history = self.project / ".daodan/science-mode-history"
        pending = history / "r0002.json"
        corrupt = json.loads((self.project / ".daodan/science-mode.json").read_text())
        corrupt.update(enabled=True, revision=2, updated_at="invalid timestamp")
        pending.write_text(json.dumps(corrupt), encoding="utf-8")
        with_corruption = self.snapshot()
        self.run_cli("mode", "on", "--expected-revision", 1, "--source", "synthetic user request", code=2)
        self.assertEqual(self.snapshot(), with_corruption)
        self.assertFalse(self.run_cli("mode")["enabled"])
        pending.unlink()
        self.assertEqual(self.preference(True, 1)["revision"], 2)
        self.assertEqual(len(list(history.glob("*.json"))), 2)
        self.assertFalse(json.loads((history / "r0001.json").read_text())["enabled"])

    def test_corrupt_mode_is_reported_preserved_and_explicit_research_still_works(self):
        self.preference(False)
        config = self.project / ".daodan/science-mode.json"
        damaged = b'{"enabled": INVALID}\xff'
        config.write_bytes(damaged)
        before = self.snapshot()
        self.assertEqual(self.run_cli("mode", code=2)["status"], "configuration-error")
        hook = self.run_cli("hook", stdin=json.dumps({"cwd": str(self.project), "hook_event_name": "SessionStart"}))
        self.assertIn("configuration-error", hook["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.snapshot(), before)
        blocked = self.publication()
        blocked["automatic"] = True
        self.assertEqual(self.run_cli("publish", payload=blocked)["status"], "configuration-error")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.run_cli("publish", payload=self.publication())["status"], "published")
        self.assertEqual(config.read_bytes(), damaged)

    def test_hook_on_routes_both_events_without_writes_and_off_is_silent(self):
        for event in ("SessionStart", "UserPromptSubmit"):
            result = self.run_cli("hook", stdin=json.dumps({"cwd": str(self.project), "hook_event_name": event}))
            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], event)
            self.assertIn("science-based-approach", output["additionalContext"])
        self.assertEqual(self.snapshot(), {})
        self.preference(False)
        before = self.snapshot()
        for event in ("SessionStart", "UserPromptSubmit"):
            self.assertIsNone(self.run_cli("hook", stdin=json.dumps({"cwd": str(self.project), "hook_event_name": event})))
        for malformed in ("{", "[]", json.dumps({"cwd": str(self.project), "hook_event_name": "Stop"})):
            self.run_cli("hook", stdin=malformed, code=2)
        self.assertEqual(self.snapshot(), before)

    def test_git_worktrees_share_main_preference(self):
        def git(*args):
            result = subprocess.run(["git", "-C", str(self.project), *args], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
        git("init", "--quiet")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "Synthetic fixture")
        linked = self.base / "linked worktree"
        git("worktree", "add", "--detach", str(linked))
        self.preference(False, project=linked)
        self.assertFalse(self.run_cli("mode")["enabled"])
        self.assertEqual(self.run_cli("mode", project=linked)["project"], str(self.project))
        self.assertFalse((linked / ".daodan").exists())
        main_docs = self.project / "docs"
        main_docs.mkdir()
        (main_docs / "README.md").write_bytes(b"# Existing main checkout documentation\n")
        main_before = self.snapshot(main_docs)
        linked_before = self.snapshot(linked)
        automatic = {**self.publication(), "automatic": True}
        self.assertEqual(self.run_cli("publish", payload=automatic, project=linked)["status"], "disabled")
        self.assertEqual(self.snapshot(linked), linked_before)
        self.assertEqual(self.snapshot(main_docs), main_before)
        self.assertEqual(self.run_cli("publish", payload=self.publication(), project=linked)["status"], "published")
        self.assertTrue((linked / "docs/research/synthetic-study/revisions/r0001.md").is_file())
        self.assertEqual(self.snapshot(main_docs), main_before)
        self.assertFalse((main_docs / "research").exists())
        self.assertEqual(self.run_cli("list")["research"], [])
        self.assertEqual(self.run_cli("list", project=linked)["research"][0]["id"], "synthetic-study")
        self.assertFalse(self.run_cli("mode", project=linked)["enabled"])
        self.assertFalse((linked / ".daodan").exists())

    def test_separate_git_directory_keeps_caller_project_mode_and_archive(self):
        git_store = self.base / "separate git store"
        def git(*args):
            result = subprocess.run(["git", "-C", str(self.project), *args], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
        git("init", "--quiet", "--separate-git-dir", str(git_store))
        nested = self.project / "tracked project"
        nested.mkdir()
        (nested / "fixture.txt").write_text("Synthetic project boundary fixture.\n")
        git("add", "tracked project/fixture.txt")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Synthetic fixture")
        self.preference(False, project=nested)
        self.assertEqual(self.run_cli("mode", project=nested)["project"], str(nested))
        self.assertTrue(self.run_cli("mode")["enabled"])
        self.assertFalse((self.project / ".daodan").exists())
        before = self.snapshot(nested)
        automatic = {**self.publication(), "automatic": True}
        self.assertEqual(self.run_cli("publish", payload=automatic, project=nested)["status"], "disabled")
        self.assertEqual(self.snapshot(nested), before)
        self.assertEqual(self.run_cli("publish", payload=self.publication(), project=nested)["status"], "published")
        self.assertTrue((nested / "docs/research/synthetic-study/revisions/r0001.md").is_file())
        self.assertFalse((self.project / "docs").exists())
        self.assertFalse(self.run_cli("mode", project=nested)["enabled"])

    def test_checkpoint_deduplicates_but_rechecks_changed_context_phase_and_mode(self):
        payload = {"task_id": "synthetic-task", "phase": "brainstorm", "context": {"intent": "synthetic", "version": "1"}}
        self.assertEqual(self.run_cli("checkpoint", payload=payload)["status"], "needed")
        self.assertEqual(self.snapshot(), {})
        original = self.run_cli("checkpoint", "--record", payload=payload)
        self.assertEqual(original["status"], "claimed")
        self.assertEqual(self.run_cli("checkpoint", "--record", payload=payload)["status"], "duplicate")
        finished = {**payload, "outcome": "not-applicable", "reason": "Synthetic fixture has no scientific question", "references": []}
        self.assertEqual(self.run_cli("checkpoint", "--record", payload=finished)["status"], "recorded")
        before = self.snapshot()
        self.assertEqual(self.run_cli("checkpoint", "--record", payload=finished)["status"], "duplicate")
        self.assertEqual(self.snapshot(), before)
        for changed in ({**payload, "context": {"intent": "synthetic", "version": "2"}}, {**payload, "phase": "specification"}):
            result = self.run_cli("checkpoint", payload=changed)
            self.assertEqual(result["status"], "needed")
            self.assertNotEqual(result["key"], original["key"])
        self.preference(False)
        self.preference(True, 1)
        self.assertEqual(self.run_cli("checkpoint", payload=payload)["status"], "needed")
        maintenance = {**payload, "research_maintenance": True}
        before = self.snapshot()
        self.assertEqual(self.run_cli("checkpoint", "--record", payload=maintenance)["status"], "not-applicable")
        self.assertEqual(self.snapshot(), before)

    def test_off_blocks_automatic_checkpoint_and_publication_but_allows_explicit(self):
        self.preference(False)
        before = self.snapshot()
        self.assertEqual(self.run_cli("checkpoint", "--record", payload={})["status"], "disabled")
        automatic = {**self.publication(), "automatic": True}
        self.assertEqual(self.run_cli("publish", payload=automatic)["status"], "disabled")
        self.assertEqual(self.run_cli("check", payload={"automatic": True})["status"], "disabled")
        self.assertEqual(self.snapshot(), before)
        self.run_cli("publish", payload=self.publication())
        self.assertFalse(self.run_cli("mode")["enabled"])

    def test_revisions_and_receipts_are_immutable_and_retries_are_idempotent(self):
        first = self.publication()
        self.run_cli("publish", payload=first)
        archive = self.project / first["path"]
        current = archive / "README.md"
        self.assertIn(first["document"], current.read_text())
        historical = {p: p.read_bytes() for p in [archive / "revisions/r0001.md", archive / "revisions/r0001.json", archive / "checks/publication-check-synthetic-study-1.json"]}
        self.assertEqual(self.run_cli("publish", payload=first)["status"], "unchanged")
        second = self.publication(2)
        second["document"] = (
            "# Updated synthetic fixture\n\n~~Synthetic obsolete claim.~~\n\n"
            "Revised synthetic explanation; no actual scientific evidence.\n\n"
            "## Changelog\n\n| Revision | Change |\n|---|---|\n"
            "| 2 | Replaced obsolete synthetic claim and retained its visible history. |\n"
        )
        self.run_cli("publish", payload=second)
        self.assertIn(second["document"], current.read_text())
        self.assertIn("~~Synthetic obsolete claim.~~", current.read_text())
        self.assertFalse((archive / "README-r0002.md").exists())
        for path, content in historical.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(len(list((archive / "revisions").glob("*.md"))), 2)
        before = self.snapshot()
        self.run_cli("publish", payload={**self.publication(2), "document": "Conflicting synthetic content"}, code=2)
        self.assertEqual(self.snapshot(), before)

    def test_existing_research_keeps_same_current_file_and_guards_manual_edits(self):
        current = self.project / "docs/research/existing-note.md"
        current.parent.mkdir(parents=True)
        original = b"# Existing synthetic research\r\n\r\nOriginal synthetic claim.\r\n"
        current.write_bytes(original)
        first = self.publication()
        first.update(current_path="docs/research/existing-note.md", expected_document_digest=hashlib.sha256(original).hexdigest())
        first["document"] = "# Existing synthetic research updated\n\n~~Original synthetic claim.~~\n\nReplacement synthetic explanation.\n\n## Changelog\n\nOriginal claim superseded in fixture revision 1.\n"
        self.run_cli("publish", payload=first)
        archive = self.project / first["path"]
        baseline = archive / "revisions/r0000.md"
        self.assertEqual(baseline.read_bytes(), original)
        self.assertTrue(current.read_bytes().startswith(first["document"].encode()))
        self.assertFalse((archive / "README.md").exists())
        index = (self.project / "docs/research/README.md").read_text()
        self.assertEqual(index.count("](existing-note.md)"), 1)
        self.assertNotIn("synthetic-study/README.md", index)
        published = self.snapshot()
        self.run_cli("publish", payload=first)
        self.assertEqual(self.snapshot(), published)
        state_marker = b"<!-- daodan:science-state:begin -->"
        scientific_before = current.read_bytes().split(state_marker, 1)[0]
        current_before_check = current.read_bytes()
        check = self.run_cli("check", payload=self.check_payload("legacy-no-change"))["check"]
        self.assertEqual(current.read_bytes().split(state_marker, 1)[0], scientific_before)
        self.assertNotEqual(current.read_bytes(), current_before_check)
        self.assertIn(check["checked_at"], current.read_text())
        self.assertIn("completed-no-change", current.read_text())
        duplicate = self.publication(research_id="overlapping-study", path="docs/research/overlapping-study")
        duplicate.update(current_path=first["current_path"], expected_document_digest=hashlib.sha256(current.read_bytes()).hexdigest())
        before_duplicate = self.snapshot()
        self.run_cli("publish", payload=duplicate, code=2)
        self.assertEqual(self.snapshot(), before_duplicate)

        second = self.publication(2)
        second.update(current_path=first["current_path"], expected_document_digest=hashlib.sha256(current.read_bytes()).hexdigest())
        manual = current.read_bytes() + b"\nUser's manual synthetic clarification.\n"
        current.write_bytes(manual)
        before = self.snapshot()
        self.run_cli("publish", payload=second, code=2)
        self.assertEqual(self.snapshot(), before)
        self.run_cli("reindex", code=2)
        self.assertEqual(current.read_bytes(), manual)
        self.run_cli("check", payload=self.check_payload("manual-conflict-check"), code=2)
        self.assertEqual(current.read_bytes(), manual)
        second["expected_document_digest"] = hashlib.sha256(manual).hexdigest()
        self.run_cli("publish", payload=second)
        self.assertTrue(current.read_bytes().startswith(second["document"].encode()))
        self.assertEqual(baseline.read_bytes(), original)
        self.assertEqual((archive / "revisions/r0001.md").read_bytes(), first["document"].encode())
        self.assertIn(manual, [path.read_bytes() for path in (archive / "revisions").glob("*.md")])
        self.assertFalse((archive / "README.md").exists())

    @unittest.skipUnless(os.name == "nt", "Windows read-only current document blocks replacement")
    def test_interrupted_legacy_publication_does_not_overwrite_intervening_manual_edits(self):
        current = self.project / "docs/research/existing-note.md"
        current.parent.mkdir(parents=True)
        original = b"# Original synthetic research before interrupted adoption\n"
        current.write_bytes(original)
        first = self.publication()
        first.update(current_path="docs/research/existing-note.md", expected_document_digest=hashlib.sha256(original).hexdigest())
        current.chmod(stat.S_IREAD)
        try:
            self.run_cli("publish", payload=first, code=2)
            self.assertEqual(current.read_bytes(), original)
        finally:
            current.chmod(stat.S_IREAD | stat.S_IWRITE)
        manual = original + b"\nManual edit after interruption.\n"
        current.write_bytes(manual)
        before = self.snapshot()
        self.run_cli("publish", payload=first, code=2)
        self.assertEqual(self.snapshot(), before)
        self.run_cli("reindex", code=2)
        self.assertEqual(current.read_bytes(), manual)
        self.assertEqual((self.project / first["path"] / "revisions/r0000.md").read_bytes(), original)
        current.write_bytes(original)  # Restore only the owned synthetic fixture's expected state.
        self.run_cli("publish", payload=first)
        self.assertTrue(current.read_bytes().startswith(first["document"].encode()))
        self.assertFalse((self.project / first["path"] / "README.md").exists())

    def test_no_change_and_failed_checks_do_not_claim_substantive_update_or_freshness(self):
        self.run_cli("publish", payload=self.publication())
        initial = self.run_cli("list")["research"][0]
        success = self.run_cli("check", payload=self.check_payload("unchanged-check"))["check"]
        after_success = self.run_cli("reindex")["research"][0]
        failed_payload = self.check_payload("failed-check", "failed")
        document = (
            "## Origin\n\nSynthetic update request.\n\n"
            "## Context\n\nThe synthetic source was unavailable.\n\n"
            "## Queries\n\n```text\nsite:example.invalid synthetic archive\n```\n\n"
            "## Check history\n\n| Attempt | Outcome |\n|---|---|\n| Fixture | Failed |\n\n"
        )
        failed_payload["check"]["document"] = document
        failed = self.run_cli("check", payload=failed_payload)["check"]
        receipts = self.project / "docs/research/synthetic-study/checks"
        stored = json.loads((receipts / "failed-check.json").read_text())
        rendered = (receipts / "failed-check.md").read_text()
        self.assertEqual(stored["document"], document)
        self.assertEqual(failed["document"], document)
        self.assertTrue(rendered.endswith(document))
        self.assertLess(rendered.index("- check_id: failed-check"), rendered.index("## Origin"))
        self.assertNotIn("- document:", rendered)
        after_failure = self.run_cli("reindex")["research"][0]
        self.assertEqual(after_success["last_complete_check_at"], success["checked_at"])
        self.assertEqual(after_failure["last_complete_check_at"], success["checked_at"])
        self.assertEqual(after_failure["last_checked_at"], failed["checked_at"])
        self.assertEqual(after_failure["last_check_status"], "failed")
        self.assertEqual(after_failure["updated_at"], initial["updated_at"])
        self.assertEqual(after_failure["revision"], 1)
        before = self.snapshot()
        self.run_cli("check", payload=failed_payload)
        self.assertEqual(self.snapshot(), before)
        changed = self.check_payload("failed-check", "completed-no-change")
        self.run_cli("check", payload=changed, code=2)
        self.assertEqual(self.snapshot(), before)
        changed_document = self.check_payload("failed-check", "failed")
        changed_document["check"]["document"] = document + "Different synthetic evidence.\n"
        self.run_cli("check", payload=changed_document, code=2)
        self.assertEqual(self.snapshot(), before)

    def test_material_partial_update_publishes_without_claiming_complete_freshness(self):
        initial = self.publication()
        initial["check"]["status"] = "partial"
        initial["check"]["limitations"] = ["Synthetic source unavailable; review incomplete"]
        initial["status"] = "review-needed"
        self.assertEqual(self.run_cli("publish", payload=initial)["status"], "published")
        first = self.run_cli("reindex")["research"][0]
        self.assertEqual(first["revision"], 1)
        self.assertEqual(first["last_check_status"], "partial")
        self.assertIsNone(first["last_complete_check_at"])

        self.run_cli("publish", payload=self.publication(2))
        complete = self.run_cli("reindex")["research"][0]
        self.assertIsNotNone(complete["last_complete_check_at"])
        archive = self.project / initial["path"]
        historical = {path: path.read_bytes() for path in (archive / "revisions").iterdir()}
        partial = self.publication(3)
        partial["document"] = (
            "# Synthetic material correction\n\n"
            "This fixture withdraws a synthetic claim after a synthetic retraction notice.\n"
            "Other synthetic sources remain unavailable; the review is incomplete.\n"
            "No real paper, retraction or scientific claim is represented.\n"
        )
        partial["status"] = "review-needed"
        partial["check"]["status"] = "partial"
        partial["check"]["coverage"] = ["Synthetic retraction notice checked"]
        partial["check"]["limitations"] = ["Remaining synthetic sources inaccessible"]
        self.assertEqual(self.run_cli("publish", payload=partial)["status"], "published")
        current = self.run_cli("reindex")["research"][0]
        receipt = json.loads((archive / "checks/publication-check-synthetic-study-3.json").read_text())
        self.assertEqual(current["revision"], 3)
        self.assertEqual(current["status"], "review-needed")
        self.assertEqual(current["last_check_status"], "partial")
        self.assertEqual(current["last_checked_at"], receipt["checked_at"])
        self.assertEqual(current["last_complete_check_at"], complete["last_complete_check_at"])
        self.assertNotEqual(current["updated_at"], complete["updated_at"])
        self.assertEqual((archive / "revisions/r0003.md").read_text(), partial["document"])
        for path, original in historical.items():
            self.assertEqual(path.read_bytes(), original)

        before = self.snapshot()
        for status in ("failed", "cancelled", "completed-no-change"):
            with self.subTest(rejected_publication_status=status):
                invalid = self.publication(4)
                invalid["check"]["status"] = status
                self.run_cli("publish", payload=invalid, code=2)
                self.assertEqual(self.snapshot(), before)

    def test_concurrent_publish_has_one_winner_and_preserves_old_revision(self):
        self.run_cli("publish", payload=self.publication())
        archive = self.project / "docs/research/synthetic-study"
        old = (archive / "revisions/r0001.md").read_bytes()
        left, right = self.publication(2), self.publication(2)
        right["operation_id"] = "second-writer"
        right["document"] = "# Synthetic second writer\n"
        right["check"]["id"] = "second-writer-check"
        processes = [subprocess.Popen(self.command("publish", payload=value), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8") for value in (left, right)]
        outputs = [process.communicate(timeout=20) for process in processes]
        self.assertEqual(sorted(process.returncode for process in processes), [0, 2], outputs)
        winner = next(value for value, process in zip((left, right), processes) if process.returncode == 0)
        self.assertEqual((archive / "revisions/r0002.md").read_text(), winner["document"])
        self.assertEqual((archive / "revisions/r0001.md").read_bytes(), old)
        self.assertEqual(self.run_cli("list")["research"][0]["revision"], 2)

    def test_partial_publication_keeps_current_readable_and_exact_retry_recovers(self):
        self.run_cli("publish", payload=self.publication())
        archive = self.project / "docs/research/synthetic-study"
        obstruction = archive / "revisions/r0002.md"
        obstruction.mkdir()
        update = self.publication(2)
        update["automatic"] = True
        self.run_cli("publish", payload=update, code=2)
        self.assertEqual(self.run_cli("list")["research"][0]["revision"], 1)
        staged = (archive / "revisions/r0002.json").read_bytes()
        obstruction.rmdir()
        self.preference(False)
        update["automatic"] = False  # Explicit recovery is allowed after automatic work stops.
        conflict = {**update, "operation_id": "foreign-operation", "document": "Conflicting synthetic revision"}
        self.run_cli("publish", payload=conflict, code=2)
        self.assertEqual((archive / "revisions/r0002.json").read_bytes(), staged)
        self.assertEqual(self.run_cli("publish", payload=update)["status"], "published")
        self.assertEqual((archive / "revisions/r0002.json").read_bytes(), staged)
        self.assertEqual(self.run_cli("list")["research"][0]["revision"], 2)

    @unittest.skipUnless(os.name == "nt", "Windows read-only destination blocks atomic replacement")
    def test_unpublished_receipt_does_not_advance_verified_freshness(self):
        self.run_cli("publish", payload=self.publication())
        original = self.run_cli("reindex")["research"][0]
        archive = self.project / "docs/research/synthetic-study"
        pointer = archive / "science.json"
        previous_pointer = pointer.read_bytes()
        pointer.chmod(stat.S_IREAD)
        try:
            self.run_cli("publish", payload=self.publication(2), code=2)
            self.assertEqual(pointer.read_bytes(), previous_pointer)
            self.assertTrue((archive / "checks/publication-check-synthetic-study-2.json").is_file())
            interrupted = self.run_cli("reindex")["research"][0]
            self.assertEqual(interrupted["revision"], 1)
            self.assertEqual(interrupted["last_complete_check_at"], original["last_complete_check_at"])
            self.assertEqual(interrupted["updated_at"], original["updated_at"])
        finally:
            pointer.chmod(stat.S_IREAD | stat.S_IWRITE)
        self.assertEqual(self.run_cli("publish", payload=self.publication(2))["status"], "published")

    def test_reindex_and_post_pointer_retry_preserve_existing_readme_bytes(self):
        index = self.project / "docs/research/README.md"
        index.parent.mkdir(parents=True)
        prefix = b"# Existing human notes\r\n\r\nKeep these exact bytes.\r\n"
        index.write_bytes(prefix)
        record = self.publication()
        archive = self.project / record["path"]
        archive.mkdir()
        view = archive / "README.md"
        view.mkdir()  # Filesystem failure after immutable artifacts and pointer publication.
        self.run_cli("publish", payload=record, code=2)
        self.assertEqual(self.run_cli("list")["research"][0]["revision"], 1)
        view.rmdir()
        self.assertEqual(self.run_cli("publish", payload=record)["status"], "unchanged")
        self.assertTrue(index.read_bytes().startswith(prefix))
        suffix = b"\nHuman suffix remains too.\n"
        index.write_bytes(index.read_bytes() + suffix)
        before = index.read_bytes()
        self.run_cli("reindex")
        self.assertEqual(index.read_bytes(), before)
        self.assertTrue(index.read_bytes().endswith(suffix))

    def test_single_research_operations_leave_unrelated_views_for_explicit_reindex(self):
        self.run_cli("publish", payload=self.publication())
        unrelated = self.publication(research_id="unrelated-study", path="docs/research/unrelated-study")
        self.run_cli("publish", payload=unrelated)
        directory = self.project / unrelated["path"]
        readme = directory / "README.md"
        current_before = readme.read_bytes()
        readme.unlink()
        receipt_view = directory / "checks/publication-check-unrelated-study-1.md"
        receipt_before = receipt_view.read_bytes()
        receipt_view.unlink()
        unrelated_before = self.snapshot(directory)
        update = self.publication(2)
        receipt = self.check_payload("only-primary-check", expected=2)
        for command, payload in (("publish", update), ("publish", update), ("check", receipt), ("check", receipt)):
            with self.subTest(operation=command):
                self.run_cli(command, payload=payload)
                self.assertEqual(self.snapshot(directory), unrelated_before)
                self.assertFalse(receipt_view.exists())
                index = (self.project / "docs/research/README.md").read_text()
                self.assertIn("synthetic-study/README.md", index)
                self.assertIn("unrelated-study/README.md", index)
        self.run_cli("reindex")
        self.assertEqual(receipt_view.read_bytes(), receipt_before)
        self.assertEqual(readme.read_bytes(), current_before)
        self.assertIn("<!-- daodan:science:begin -->", readme.read_text())

    def test_traversal_and_duplicate_identity_or_path_are_rejected(self):
        for path in ("../escape", "docs/research/../../escape", str(self.base / "outside"), "docs/superpowers/research/fixture"):
            with self.subTest(path=path):
                self.run_cli("publish", payload=self.publication(path=path), code=2)
        self.assertEqual(self.snapshot(), {})
        self.run_cli("publish", payload=self.publication())
        before = self.snapshot()
        self.run_cli("publish", payload=self.publication(path="docs/research/duplicate"), code=2)
        self.run_cli("publish", payload=self.publication(research_id="different-id"), code=2)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.base / "outside").exists())

    def test_symlink_archive_and_mode_paths_do_not_write_outside(self):
        external = self.base / "external"
        external.mkdir()
        research = self.project / "docs/research"
        research.parent.mkdir()
        research.symlink_to(external, target_is_directory=True)
        self.run_cli("publish", payload=self.publication(), code=2)
        self.assertEqual(list(external.iterdir()), [])
        research.unlink()
        state = self.project / ".daodan"
        state.symlink_to(external, target_is_directory=True)
        self.run_cli("mode", code=2)
        self.run_cli("mode", "off", "--expected-revision", 0, "--source", "synthetic", code=2)
        self.assertEqual(list(external.iterdir()), [])
        state.unlink()

    def test_existing_current_document_paths_cannot_escape_the_checkout(self):
        external = self.base / "outside.md"
        original = b"# Synthetic external document must remain untouched\n"
        external.write_bytes(original)
        for path in ("../outside.md", str(external)):
            with self.subTest(current_path=path):
                payload = self.publication()
                payload.update(current_path=path, expected_document_digest=hashlib.sha256(original).hexdigest())
                self.run_cli("publish", payload=payload, code=2)
                self.assertEqual(external.read_bytes(), original)
                self.assertEqual(self.snapshot(), {})
        linked = self.project / "docs/research/existing-note.md"
        linked.parent.mkdir(parents=True)
        linked.symlink_to(external)
        payload = self.publication()
        payload.update(current_path="docs/research/existing-note.md", expected_document_digest=hashlib.sha256(original).hexdigest())
        self.run_cli("publish", payload=payload, code=2)
        self.assertEqual(external.read_bytes(), original)
        self.assertTrue(linked.is_symlink())
        linked.unlink()

    @unittest.skipUnless(os.name == "nt", "Windows junction boundary")
    def test_windows_junction_archive_is_rejected(self):
        external = self.base / "junction external"
        external.mkdir()
        research = self.project / "docs/research"
        research.parent.mkdir()
        env = {**os.environ, "SCIENCE_TEST_LINK": str(research), "SCIENCE_TEST_TARGET": str(external)}
        result = subprocess.run(["powershell", "-NoProfile", "-Command", "$ErrorActionPreference = 'Stop'; New-Item -ItemType Junction -Path $env:SCIENCE_TEST_LINK -Target $env:SCIENCE_TEST_TARGET | Out-Null"], env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        try:
            self.run_cli("publish", payload=self.publication(), code=2)
            self.assertEqual(list(external.iterdir()), [])
        finally:
            os.rmdir(research)


if __name__ == "__main__":
    unittest.main()
