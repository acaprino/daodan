from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.artifacts import ArtifactStore
from work_controller.errors import (
    DefinitionError,
    ExecutionError,
    OutcomeUnknownError,
)
from work_controller.git_support import GitSupport


class ArtifactStoreTests(unittest.TestCase):
    def test_put_bytes_stores_content_at_its_digest_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifacts"
            store = ArtifactStore(root)

            first = store.put_bytes(b"deadly brain")
            second = store.put_bytes(b"deadly brain")

            digest = hashlib.sha256(b"deadly brain").hexdigest()
            self.assertEqual(first, second)
            self.assertEqual(first["digest"], digest)
            self.assertEqual(first["size"], 12)
            self.assertEqual(first["path"], store.path_for(digest))
            self.assertEqual(first["path"].read_bytes(), b"deadly brain")
            self.assertEqual(len(list((root / "objects").rglob("*.blob"))), 1)

    def test_put_file_stores_the_same_bytes_as_put_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.bin"
            source.write_bytes(b"streamed artifact")
            store = ArtifactStore(root / "store")

            from_file = store.put_file(source)
            from_bytes = store.put_bytes(b"streamed artifact")

            self.assertEqual(from_file, from_bytes)
            self.assertEqual(from_file["size"], len(b"streamed artifact"))

    def test_read_returns_bytes_and_enforces_max_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary) / "store")
            stored = store.put_bytes(b"bounded")

            self.assertEqual(store.read(stored["digest"]), b"bounded")
            self.assertEqual(store.read(stored["digest"], max_bytes=7), b"bounded")
            with self.assertRaises(ExecutionError):
                store.read(stored["digest"], max_bytes=6)

    def test_path_for_rejects_digests_that_are_invalid_or_escape_the_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary) / "store")
            invalid = ("", "a" * 63, "g" * 64, "../" + "a" * 61, "/tmp/object")

            for digest in invalid:
                with self.subTest(digest=digest), self.assertRaises(DefinitionError):
                    store.path_for(digest)

    def test_put_bytes_never_overwrites_different_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary) / "store")
            stored = store.put_bytes(b"expected")
            stored["path"].write_bytes(b"corrupt!")

            with self.assertRaises(ExecutionError):
                store.put_bytes(b"expected")

            self.assertEqual(stored["path"].read_bytes(), b"corrupt!")

    def test_put_file_rejects_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ArtifactStore(Path(temporary) / "store")

            with self.assertRaises(ExecutionError):
                store.put_file(Path(temporary))

    def test_put_enforces_the_total_artifact_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = ArtifactStore(root / "store")
            source = root / "large.bin"
            source.write_bytes(b"12345")
            with patch("work_controller.artifacts._MAX_ARTIFACT_BYTES", 4):
                with self.assertRaises(ExecutionError):
                    store.put_bytes(b"12345")
                with self.assertRaises(ExecutionError):
                    store.put_file(source)


def git_result(
    stdout: str = "", *, returncode: int = 0, stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["git"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class GitSupportTests(unittest.TestCase):
    def test_ensure_clean_accepts_a_clean_non_bare_work_tree_without_a_shell(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = Mock(
                side_effect=[
                    git_result("true\n"),
                    git_result("false\n"),
                    git_result(temporary + "\n"),
                    git_result(""),
                ]
            )
            GitSupport(Path(temporary), runner=runner).ensure_clean()

        self.assertEqual(
            [call.args[0] for call in runner.call_args_list],
            [
                ["git", "rev-parse", "--is-inside-work-tree"],
                ["git", "rev-parse", "--is-bare-repository"],
                ["git", "rev-parse", "--show-toplevel"],
                ["git", "status", "--porcelain", "--untracked-files=all"],
            ],
        )
        for call in runner.call_args_list:
            self.assertIs(call.kwargs["shell"], False)
            self.assertIs(call.kwargs["text"], True)
            self.assertEqual(call.kwargs["encoding"], "utf-8")
            self.assertEqual(call.kwargs["timeout"], 60)

    def test_ensure_clean_rejects_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = Mock(
                side_effect=[
                    git_result("true\n"),
                    git_result("false\n"),
                    git_result(temporary + "\n"),
                    git_result("?? notes.txt\n"),
                ]
            )
            support = GitSupport(Path(temporary), runner=runner)
            with self.assertRaises(ExecutionError):
                support.ensure_clean()

    def test_ensure_clean_rejects_a_bare_repository(self) -> None:
        runner = Mock(side_effect=[git_result("true\n"), git_result("true\n")])
        with tempfile.TemporaryDirectory() as temporary:
            support = GitSupport(Path(temporary), runner=runner)
            with self.assertRaises(ExecutionError):
                support.ensure_clean()

        self.assertEqual(runner.call_count, 2)

    def test_ensure_clean_rejects_a_subdirectory_for_scoped_commits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "nested"
            workspace.mkdir()
            runner = Mock(
                side_effect=[
                    git_result("true\n"),
                    git_result("false\n"),
                    git_result(str(root) + "\n"),
                ]
            )
            with self.assertRaisesRegex(ExecutionError, "work-tree root"):
                GitSupport(workspace, runner=runner).ensure_clean()
            self.assertEqual(runner.call_count, 3)

    def test_git_errors_are_compact_execution_errors(self) -> None:
        runner = Mock(
            return_value=git_result(
                returncode=2, stderr="fatal: invalid\n" + "x" * 500
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            support = GitSupport(Path(temporary), runner=runner)
            with self.assertRaises(ExecutionError) as caught:
                support.ensure_clean()

        message = str(caught.exception)
        self.assertIn("git rev-parse failed (2):", message)
        self.assertNotIn("\n", message)
        self.assertLessEqual(len(message), 300)

    def test_commit_paths_stages_only_normalized_paths_and_returns_head_sha(self) -> None:
        sha = "0123456789abcdef0123456789abcdef01234567"
        runner = Mock(
            side_effect=[
                git_result(),
                git_result("docs/note.md\nsrc/ok.py\n"),
                git_result(),
                git_result(sha + "\n"),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            support = GitSupport(Path(temporary), runner=runner)

            result = support.commit_paths(
                ["src/ok.py", str(Path("docs") / "note.md")],
                "Implement scoped files",
            )

        self.assertEqual(result, sha)
        self.assertEqual(
            [call.args[0] for call in runner.call_args_list],
            [
                ["git", "add", "--", "src/ok.py", "docs/note.md"],
                ["git", "diff", "--cached", "--name-only"],
                [
                    "git",
                    "commit",
                    "-m",
                    "Implement scoped files",
                    "--",
                    "src/ok.py",
                    "docs/note.md",
                ],
                ["git", "rev-parse", "HEAD"],
            ],
        )

    def test_commit_paths_rejects_an_invalid_head_sha(self) -> None:
        runner = Mock(
            side_effect=[
                git_result(),
                git_result("allowed.txt\n"),
                git_result(),
                git_result("not-a-sha\n"),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            support = GitSupport(Path(temporary), runner=runner)
            with self.assertRaises(OutcomeUnknownError):
                support.commit_paths(["allowed.txt"], "Scoped commit")

    def test_commit_paths_marks_rev_parse_failure_as_unknown_outcome(self) -> None:
        runner = Mock(
            side_effect=[
                git_result(),
                git_result("allowed.txt\n"),
                git_result(),
                git_result(returncode=1, stderr="cannot read HEAD"),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            support = GitSupport(Path(temporary), runner=runner)
            with self.assertRaises(OutcomeUnknownError):
                support.commit_paths(["allowed.txt"], "Scoped commit")

    def test_commit_paths_rejects_extraneous_staging_before_commit(self) -> None:
        runner = Mock(
            side_effect=[
                git_result(),
                git_result("allowed.txt\nforeign.txt\n"),
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            support = GitSupport(Path(temporary), runner=runner)
            with self.assertRaises(ExecutionError):
                support.commit_paths(["allowed.txt"], "Scoped commit")

        self.assertEqual(
            [call.args[0][1] for call in runner.call_args_list], ["add", "diff"]
        )

    def test_commit_paths_rejects_no_changes_before_commit(self) -> None:
        runner = Mock(side_effect=[git_result(), git_result("")])
        with tempfile.TemporaryDirectory() as temporary:
            support = GitSupport(Path(temporary), runner=runner)
            with self.assertRaises(ExecutionError):
                support.commit_paths(["allowed.txt"], "Scoped commit")

        self.assertEqual(
            [call.args[0][1] for call in runner.call_args_list], ["add", "diff"]
        )

    def test_commit_paths_rejects_invalid_scope_and_message_before_running_git(self) -> None:
        cases = [
            ([], "message"),
            (["../outside.txt"], "message"),
            (["/absolute.txt"], "message"),
            (["allowed.txt"], "  "),
            ("allowed.txt", "message"),
        ]
        for paths, message in cases:
            with self.subTest(paths=paths, message=message):
                runner = Mock()
                with tempfile.TemporaryDirectory() as temporary:
                    support = GitSupport(Path(temporary), runner=runner)
                    with self.assertRaises(DefinitionError):
                        support.commit_paths(paths, message)
                runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
