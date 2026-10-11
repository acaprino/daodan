"""Loader tests for the neutral Daodan plugin model."""

import builtins
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


class NeutralModelTests(unittest.TestCase):
    def assert_model_rejected_before_read(self, target: Path, action) -> None:
        attempted = []
        original_builtin, original_io = builtins.open, io.open
        resolved_target = target.resolve()

        def watch(original):
            def open_owned(file, mode="r", *args, **kwargs):
                if not isinstance(file, int) and Path(file).resolve() == resolved_target:
                    if "r" in mode or "+" in mode:
                        attempted.append(Path(file))
                        raise AssertionError("Out-of-root control plane opened before rejection")
                return original(file, mode, *args, **kwargs)
            return open_owned

        with patch("builtins.open", watch(original_builtin)), patch("io.open", watch(original_io)):
            with self.assertRaises(ModelError):
                action()
        self.assertEqual(attempted, [])

    def test_linked_control_plane_files_are_rejected_before_read(self):
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        for number, member in enumerate(("plugin.toml", "workflows/review.toml")):
            with self.subTest(member=member):
                kernel = temporary / f"kernel-{number}"
                shutil.copytree(VALID, kernel)
                selected = kernel / member
                target = temporary / f"owned-target-{number}.toml"
                target.write_bytes(selected.read_bytes())
                selected.unlink()
                selected.symlink_to(target)

                self.assert_model_rejected_before_read(target, lambda: load_plugin(kernel))

    def test_linked_workflow_ancestor_is_rejected_before_sidecar_read(self):
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        kernel = temporary / "kernel"
        shutil.copytree(VALID, kernel)
        target_directory = temporary / "owned-workflows"
        shutil.move(kernel / "workflows", target_directory)
        (kernel / "workflows").symlink_to(target_directory, target_is_directory=True)

        self.assert_model_rejected_before_read(
            target_directory / "review.toml", lambda: load_plugin(kernel)
        )

    def test_loads_plugin_and_workflow(self):
        plugin = load_plugin(VALID)
        self.assertEqual(plugin.name, "example")
        self.assertEqual(plugin.version, "1.2.3")
        self.assertEqual(plugin.workflows[0].phases[0].id, "inspect")
        self.assertEqual(plugin.workflows[0].phases[0].isolation, "required")
        self.assertEqual(plugin.workflows[0].phases[0].join, "all-delivered")
        self.assertEqual(plugin.workflows[0].contract.artifacts, ("report",))
        self.assertEqual(
            plugin.workflows[0].contract.schemas,
            (Path("contracts/reviewer-result.toml"),),
        )

    def test_capabilities_are_loaded_separately(self):
        plugin = load_plugin(VALID)
        self.assertEqual(
            plugin.capabilities.required,
            ("repository.read", "contexts.isolate", "roles.dispatch"),
        )
        self.assertEqual(plugin.capabilities.optional, ("execution.parallel",))

    def test_entrypoint_is_plugin_relative_and_normalized(self):
        plugin = load_plugin(VALID)
        self.assertEqual(plugin.workflows[0].entrypoint, Path("workflows/review.md"))

    def test_components_index_is_loaded(self):
        plugin = load_plugin(VALID)
        self.assertEqual(plugin.components.roles, ("inspector",))
        self.assertEqual(plugin.components.workflows, ("review",))
        self.assertEqual(plugin.components.skills, ())

    def test_unknown_top_level_key_is_rejected(self):
        with self.assertRaises(ModelError):
            load_plugin(self._mutated("prompt = \"do the thing\"\n"))

    def test_missing_required_table_is_rejected(self):
        with self.assertRaises(ModelError):
            load_plugin(self._mutated(drop="[capabilities]"))

    def _mutated(self, extra: str = "", drop: str | None = None) -> Path:
        import shutil
        import tempfile

        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        destination = temporary / "example"
        shutil.copytree(VALID, destination)
        manifest = destination / "plugin.toml"
        text = manifest.read_text(encoding="utf-8")
        if drop is not None:
            lines = text.splitlines(keepends=True)
            start = next(index for index, line in enumerate(lines) if line.strip() == drop)
            end = start + 1
            while end < len(lines) and not lines[end].startswith("["):
                end += 1
            text = "".join(lines[:start] + lines[end:])
        manifest.write_text(text + extra, encoding="utf-8")
        return destination


if __name__ == "__main__":
    unittest.main()
