"""Integration proof uses real commit graphs and contents, including squash."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/work-controller/skills/work-record/scripts/run_state.py"
SPEC = importlib.util.spec_from_file_location("worktree_integration_run_state", SCRIPT)
RUN_STATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_STATE)


@unittest.skipUnless(shutil.which("git"), "Git is required for integration graph proofs")
class IntegrationProofTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="daodan-integration-",
                                                     dir=os.environ.get("DAODAN_TEST_TMPDIR"))
        self.addCleanup(self.directory.cleanup)
        self.project = Path(self.directory.name).resolve()
        self.scope = {"paths": ["payload.txt"]}
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Integration test")
        self.git("config", "user.email", "integration@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "core.hooksPath", str(self.project / ".empty-hooks"))
        self.file = self.project / "payload.txt"
        self.file.write_text("base\n", encoding="utf-8")
        self.git("add", "payload.txt")
        self.git("commit", "-m", "Base")
        self.target = self.git("rev-parse", "HEAD")
        self.git("checkout", "-b", "task")
        self.file.write_text("first change\n", encoding="utf-8")
        self.git("commit", "-am", "First change")
        self.file.write_text("reviewed result\n", encoding="utf-8")
        self.git("commit", "-am", "Second change")
        self.reviewed = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.receipt = {
            "head": self.reviewed,
            "snapshot": self.binding()["snapshot"]["digest"],
        }

    def git(self, *args, input_text=None):
        result = subprocess.run(
            ["git", "-C", str(self.project), *args], input=input_text,
            text=True, capture_output=True, check=True, timeout=15,
        )
        return result.stdout.strip()

    def binding(self):
        return RUN_STATE.project_binding(
            self.project, self.scope, self.project / ".daodan",
        )

    def candidate(self, *, tree=None, parents=None):
        args = ["commit-tree", tree or self.tree]
        for parent in [self.target] if parents is None else parents:
            args.extend(["-p", parent])
        commit = self.git(*args, input_text="Integrated result\n")
        self.git("checkout", "--detach", commit)
        return {
            "strategy": "squash", "target_sha": self.target,
            "merged_sha": commit, "candidate_review": dict(self.receipt),
        }

    def check_proof(self, integration):
        RUN_STATE.validate_integrated_commit(
            self.project, integration, self.binding(), self.scope, self.project / ".daodan",
        )

    def normalize_reviewed_text(self):
        self.git("config", "core.autocrlf", "true")
        self.file.write_bytes(b"reviewed result\r\n")
        self.git("add", "--renormalize", "payload.txt")
        self.git("commit", "--allow-empty", "-m", "Normalize reviewed text")
        self.reviewed = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.receipt = {"head": self.reviewed, "snapshot": self.binding()["snapshot"]["digest"]}

    def test_real_squash_preserves_reviewed_contents_without_ancestry(self):
        integration = self.candidate()
        self.assertIsNone(RUN_STATE.git_value(
            self.project, "merge-base", "--is-ancestor", self.reviewed, integration["merged_sha"],
        ))
        self.check_proof(integration)

    def test_ordinary_ancestry_remains_supported(self):
        self.check_proof({"merged_sha": self.reviewed, "candidate_review": self.receipt})

    def test_unidentified_rewrite_cannot_use_squash_exception(self):
        integration = self.candidate()
        del integration["strategy"]
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "does not descend"):
            self.check_proof(integration)
        integration["strategy"] = "rebase"
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "does not descend"):
            self.check_proof(integration)

    def test_squash_requires_exact_target_parent(self):
        moved = self.git("commit-tree", self.tree, "-p", self.target, input_text="Moved target\n")
        integration = self.candidate(parents=[moved])
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "exactly the pinned target"):
            self.check_proof(integration)

    def test_squash_does_not_accept_a_merge_commit(self):
        integration = self.candidate(parents=[self.target, self.reviewed])
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "exactly the pinned target"):
            self.check_proof(integration)

    def test_unreviewed_content_fails_even_with_valid_parent(self):
        integration = self.candidate(tree=self.git("rev-parse", self.target + "^{tree}"))
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "tree differs"):
            self.check_proof(integration)

    def test_dirty_review_snapshot_cannot_certify_committed_tree(self):
        self.file.write_text("uncommitted review input\n", encoding="utf-8")
        self.receipt["snapshot"] = self.binding()["snapshot"]["digest"]
        self.git("restore", "payload.txt")
        integration = self.candidate()
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)

    def test_dirty_integrated_checkout_cannot_be_closed(self):
        integration = self.candidate()
        self.file.write_text("uncommitted after integration\n", encoding="utf-8")
        integration["candidate_review"]["snapshot"] = self.binding()["snapshot"]["digest"]
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)

    def test_missing_target_or_unknown_commit_fails(self):
        integration = self.candidate()
        del integration["target_sha"]
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "full target"):
            self.check_proof(integration)
        integration["target_sha"] = "f" * 40
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "unavailable commit"):
            self.check_proof(integration)

    def test_reviewed_candidate_must_include_target(self):
        integration = self.candidate()
        orphan = self.git("commit-tree", self.tree, input_text="Unrelated candidate\n")
        integration["candidate_review"]["head"] = orphan
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "does not include"):
            self.check_proof(integration)

    def test_completion_still_requires_current_integrated_head(self):
        integration = self.candidate()
        self.git("checkout", "task")
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "current HEAD"):
            self.check_proof(integration)

    def test_clean_crlf_checkout_matches_reviewed_squash_without_changing_snapshot(self):
        self.normalize_reviewed_text()
        original_digest = self.receipt["snapshot"]
        integration = self.candidate()
        self.assertFalse(self.binding()["head_matches_snapshot"])
        self.assertEqual(self.binding()["snapshot"]["digest"], original_digest)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.check_proof(integration)
        self.assertEqual(integration["candidate_review"]["snapshot"], original_digest)

    def test_crlf_normalization_does_not_hide_substantive_changes(self):
        self.normalize_reviewed_text()
        integration = self.candidate()
        self.file.write_bytes(b"different result\r\n")
        integration["candidate_review"]["snapshot"] = self.binding()["snapshot"]["digest"]
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)

    def test_text_unset_prevents_normalization_even_with_autocrlf(self):
        self.git("config", "core.autocrlf", "true")
        (self.project / ".gitattributes").write_bytes(b"payload.txt -text\n")
        self.file.write_bytes(b"reviewed result\n")
        self.git("add", ".gitattributes", "payload.txt")
        self.git("commit", "-m", "Preserve byte exact data")
        self.reviewed = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.receipt = {"head": self.reviewed, "snapshot": self.binding()["snapshot"]["digest"]}
        integration = self.candidate()
        self.file.write_bytes(b"reviewed result\r\n")
        integration["candidate_review"]["snapshot"] = self.binding()["snapshot"]["digest"]
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)
        (self.project / ".gitattributes").write_bytes(b"payload.txt text\n")
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)

    def test_scoped_untracked_input_still_blocks_crlf_proof(self):
        self.normalize_reviewed_text()
        integration = self.candidate()
        self.scope = {"paths": ["."]}
        (self.project / "untracked.txt").write_bytes(b"not integrated\r\n")
        integration["candidate_review"]["snapshot"] = self.binding()["snapshot"]["digest"]
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)

    def test_custom_filter_is_never_executed_to_certify_squash(self):
        self.normalize_reviewed_text()
        (self.project / ".gitattributes").write_bytes(b"payload.txt filter=untrusted\n")
        self.git("add", ".gitattributes")
        self.git("commit", "-m", "Declare custom filter")
        self.reviewed = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.receipt = {"head": self.reviewed, "snapshot": self.binding()["snapshot"]["digest"]}
        integration = self.candidate()
        self.git("config", "filter.untrusted.clean", "echo executed > filter-ran; exit 99")
        self.git("config", "filter.untrusted.process", "echo executed > filter-ran; exit 99")
        self.git("config", "filter.untrusted.required", "true")
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)
        self.assertFalse((self.project / "filter-ran").exists())

    def test_mixed_legacy_crlf_and_normalized_lf_blobs_are_clean(self):
        (self.project / "legacy.txt").write_bytes(b"legacy\r\n")
        self.git("add", "legacy.txt")
        self.git("commit", "-m", "Preserve legacy CRLF blob")
        self.scope = {"paths": ["."]}
        self.normalize_reviewed_text()
        integration = self.candidate()
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertIn("i/crlf", self.git("ls-files", "--eol", "legacy.txt"))
        self.check_proof(integration)

    def test_forced_text_normalizes_nul_without_using_auto_heuristics(self):
        (self.project / ".gitattributes").write_bytes(b"payload.txt text\n")
        self.file.write_bytes(b"forced\0text\r\n")
        self.git("add", ".gitattributes", "payload.txt")
        self.git("commit", "-m", "Force text for this payload")
        self.reviewed = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.receipt = {"head": self.reviewed, "snapshot": self.binding()["snapshot"]["digest"]}
        integration = self.candidate()
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertIn("w/-text", self.git("ls-files", "--eol", "payload.txt"))
        self.check_proof(integration)

    def test_git_input_attributes_force_conversion_even_for_binary_statistics(self):
        content = b"lone\rreturn\x01\0payload\r\n"
        for attribute in ("text=input", "crlf=input"):
            for autocrlf in ("false", "true"):
                with self.subTest(attribute=attribute, autocrlf=autocrlf):
                    self.git("config", "core.autocrlf", autocrlf)
                    (self.project / ".gitattributes").write_bytes(f"payload.txt {attribute}\n".encode())
                    self.file.write_bytes(content)
                    self.git("add", ".gitattributes", "payload.txt")
                    self.git("commit", "--allow-empty", "-m", "Explicit input conversion")
                    self.reviewed = self.git("rev-parse", "HEAD")
                    self.tree = self.git("rev-parse", "HEAD^{tree}")
                    self.receipt = {"head": self.reviewed, "snapshot": self.binding()["snapshot"]["digest"]}
                    stored = subprocess.run(["git", "-C", str(self.project), "show", "HEAD:payload.txt"],
                                            capture_output=True, check=True).stdout
                    self.assertEqual(stored, content.replace(b"\r\n", b"\n"))
                    integration = self.candidate()
                    self.assertEqual(self.git("status", "--porcelain"), "")
                    self.check_proof(integration)

    def test_changed_live_attributes_outside_scope_cannot_enable_equivalence(self):
        self.normalize_reviewed_text()
        integration = self.candidate()
        (self.project / ".gitattributes").write_bytes(b"payload.txt -text\n")
        self.assertEqual(self.git("check-attr", "text", "--", "payload.txt"), "payload.txt: text: unset")
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)

    def test_changed_index_cannot_certify_working_bytes_against_head(self):
        self.normalize_reviewed_text()
        integration = self.candidate()
        self.file.write_bytes(b"staged other content\r\n")
        self.git("add", "payload.txt")
        self.file.write_bytes(b"reviewed result\r\n")
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)

    def test_binary_content_is_not_normalized_by_autocrlf(self):
        self.git("config", "core.autocrlf", "true")
        self.file.write_bytes(b"binary\0payload\n")
        self.git("add", "payload.txt")
        self.git("commit", "-m", "Binary payload")
        self.reviewed = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")
        self.receipt = {"head": self.reviewed, "snapshot": self.binding()["snapshot"]["digest"]}
        integration = self.candidate()
        self.file.write_bytes(b"binary\0payload\r\n")
        integration["candidate_review"]["snapshot"] = self.binding()["snapshot"]["digest"]
        with self.assertRaisesRegex(RUN_STATE.ProtocolError, "clean integrated content"):
            self.check_proof(integration)


if __name__ == "__main__":
    unittest.main()
