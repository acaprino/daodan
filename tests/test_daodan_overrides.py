"""Tests for the fingerprinted semantic override gate."""

import builtins
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.overrides import (  # noqa: E402
    OverrideError,
    load_overrides,
    source_digest,
    validate_override,
)

FIXTURE = REPO_ROOT / "tests/fixtures/daodan/overrides/copilot/example/review"
SOURCE = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example/workflows/review.md"


class OverrideTests(unittest.TestCase):
    def assert_override_rejected_before_read(self, target: Path, action, error=None) -> None:
        attempted = []
        original_builtin, original_io = builtins.open, io.open
        resolved_target = target.resolve()

        def watch(original):
            def open_owned(file, mode="r", *args, **kwargs):
                if not isinstance(file, int) and Path(file).resolve() == resolved_target:
                    if "r" in mode or "+" in mode:
                        attempted.append(Path(file))
                        raise AssertionError("Out-of-root override opened before rejection")
                return original(file, mode, *args, **kwargs)
            return open_owned

        with patch("builtins.open", watch(original_builtin)), patch("io.open", watch(original_io)):
            if error is not None:
                with self.assertRaises(error):
                    action()
            else:
                issues = action()
                self.assertTrue(issues, "A linked source escape must produce a validation issue")
                self.assertTrue(all(issue.code and issue.path and issue.message for issue in issues))
        self.assertEqual(attempted, [])

    def test_linked_override_manifest_is_rejected_before_read(self):
        spec = self.load_fixture_override()
        manifest = spec.root / "override.toml"
        target = spec.root.parent / "owned-override.toml"
        target.write_bytes(manifest.read_bytes())
        manifest.unlink()
        manifest.symlink_to(target)

        self.assert_override_rejected_before_read(
            target, lambda: load_overrides(spec.root), OverrideError
        )

    def test_linked_override_replacement_is_rejected(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("repository.read",),
        )
        member = spec.root / spec.replacement
        target = spec.root.parent / "owned-replacement.md"
        target.write_bytes(member.read_bytes())
        member.unlink()
        member.symlink_to(target)

        self.assert_override_rejected_before_read(
            target, lambda: validate_override(spec, frozenset({"repository.read"}))
        )

    def test_linked_fingerprint_source_is_rejected_before_hashing(self):
        for ancestor in (False, True):
            with self.subTest(linked_ancestor=ancestor):
                spec = self.load_fixture_override(capabilities_affected=("repository.read",))
                repository = spec.root.parent
                kernel = repository / "plugins/example"
                shutil.copytree(SOURCE.parents[1], kernel)
                selected = kernel / "workflows/review.md"
                relative = selected.relative_to(repository)
                spec = replace(spec, source_paths=(relative,), reviewed_against=source_digest([selected]))
                if ancestor:
                    target_directory = repository / "owned-workflows"
                    shutil.move(selected.parent, target_directory)
                    selected.parent.symlink_to(target_directory, target_is_directory=True)
                    target = target_directory / selected.name
                else:
                    target = repository / "owned-source.md"
                    target.write_bytes(selected.read_bytes())
                    selected.unlink()
                    selected.symlink_to(target)

                self.assert_override_rejected_before_read(
                    target, lambda: validate_override(spec, frozenset({"repository.read"}), repository_root=repository)
                )

    def load_fixture_override(self, **replacements):
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        destination = temporary / "review"
        shutil.copytree(FIXTURE, destination)
        manifest = destination / "override.toml"
        lines = manifest.read_text(encoding="utf-8").splitlines()
        for key, value in replacements.items():
            rendered = (
                f"{key} = [" + ", ".join(f'"{item}"' for item in value) + "]"
                if isinstance(value, (tuple, list))
                else f'{key} = "{value}"'
            )
            lines = [rendered if line.startswith(f"{key} = ") else line for line in lines]
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return load_overrides(destination)[0]

    def test_changed_source_marks_override_stale(self):
        spec = self.load_fixture_override(reviewed_against="sha256:deadbeef")
        issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
        self.assertEqual([issue.code for issue in issues], ["stale-override"])

    def test_override_cannot_add_undeclared_capability(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("shell.execute",),
        )
        issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
        self.assertEqual([issue.code for issue in issues], ["override-capability-escalation"])

    def test_matching_fingerprint_and_declared_capability_passes(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("repository.read",),
        )
        self.assertEqual(
            validate_override(spec, declared_capabilities=frozenset({"repository.read"})), []
        )

    def test_replacement_outside_the_override_directory_is_rejected(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("repository.read",),
            replacement="../orchestrator.agent.md",
        )
        issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
        self.assertEqual([issue.code for issue in issues], ["override-escapes-directory"])

    def test_contract_absent_from_the_neutral_workflow_is_rejected(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("repository.read",),
        )
        issues = validate_override(
            spec,
            declared_capabilities=frozenset({"repository.read"}),
            declared_contracts=frozenset({"some-other-outcome"}),
        )
        self.assertEqual([issue.code for issue in issues], ["override-drops-contract"])

    def test_source_digest_is_order_independent_and_content_sensitive(self):
        other = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example/roles/inspector.md"
        self.assertEqual(source_digest([SOURCE, other]), source_digest([other, SOURCE]))
        self.assertNotEqual(source_digest([SOURCE]), source_digest([other]))


if __name__ == "__main__":
    unittest.main()
