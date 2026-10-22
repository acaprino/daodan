"""CLI behaviour tests for the Daodan compiler."""

import builtins
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan_build import _publish_file, build_repository, main  # noqa: E402
from scripts.daodan.adapter import HOSTS  # noqa: E402
from scripts.daodan.overrides import source_digest  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


class CompilerCliTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        shutil.copytree(REPO_ROOT / "adapters", self.root / "adapters")
        shutil.copytree(VALID, self.root / "plugins/example")
        (self.root / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    def run_cli(self, *arguments) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = main([*arguments, "--root", str(self.root)])
        return code, out.getvalue()

    def output_bytes(self):
        roots = ("exports", ".claude-plugin", ".github", ".agents")
        outputs = {
            path.relative_to(self.root): path.read_bytes()
            for name in roots for path in (self.root / name).rglob("*")
            if path.is_file()
        }
        outputs[Path("package.json")] = (self.root / "package.json").read_bytes()
        return outputs

    def assert_build_rejected_before_read(self, target: Path, check: bool):
        attempted = []
        original_builtin, original_io = builtins.open, io.open
        resolved_target = target.resolve()

        def watch(original):
            def open_owned(file, mode="r", *args, **kwargs):
                if not isinstance(file, int) and Path(file).resolve() == resolved_target:
                    if "r" in mode or "+" in mode:
                        attempted.append(Path(file))
                        raise AssertionError("Out-of-root build input opened before rejection")
                return original(file, mode, *args, **kwargs)
            return open_owned

        with patch("builtins.open", watch(original_builtin)), patch("io.open", watch(original_io)):
            report = build_repository(self.root, HOSTS, check=check)
        self.assertTrue(report.issues, "A source escape must be a structured build failure")
        self.assertTrue(all(issue.code and issue.path and issue.message for issue in report.issues))
        self.assertNotIn("C01-owned-benign-content", repr(report.issues))
        self.assertEqual(attempted, [])

    def test_linked_skill_input_preserves_outputs_in_build_and_check(self):
        shutil.copytree(REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example", self.root / "plugins/example", dirs_exist_ok=True)
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        target = self.root / "owned-outside.bin"
        target.write_bytes(b"C01-owned-benign-content\x00\xff")
        member = self.root / "plugins/example/skills/tools/asset.bin"
        member.symlink_to(target)

        for check in (False, True):
            with self.subTest(check=check):
                self.assert_build_rejected_before_read(target, check)

                self.assertEqual(self.output_bytes(), before)

    def test_linked_kernel_ancestor_is_rejected_before_loading_manifest(self):
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        kernel = self.root / "plugins/example"
        target_directory = self.root / "owned-kernel"
        shutil.move(kernel, target_directory)
        kernel.symlink_to(target_directory, target_is_directory=True)

        self.assert_build_rejected_before_read(target_directory / "plugin.toml", False)

        self.assertEqual(self.output_bytes(), before)

    def test_linked_adapter_control_plane_is_rejected_before_loading(self):
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        member = self.root / "adapters/claude/capabilities.toml"
        target = self.root / "owned-capabilities.toml"
        target.write_bytes(member.read_bytes())
        member.unlink()
        member.symlink_to(target)

        self.assert_build_rejected_before_read(target, False)

        self.assertEqual(self.output_bytes(), before)

    def test_linked_package_loader_is_rejected_before_read_and_publication(self):
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        member = self.root / "adapters/opencode/templates/index.js"
        target = self.root / "owned-loader.js"
        target.write_bytes(b"// C01-owned-benign-content\n")
        member.unlink()
        member.symlink_to(target)

        self.assert_build_rejected_before_read(target, False)

        self.assertEqual(self.output_bytes(), before)

    def test_publication_then_check_is_clean(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_override_outcomes_and_registered_sources_gate_publication(self):
        """O03 real builds bind workflow and role claims before changing outputs."""
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        directory = self.root / "adapters/copilot/overrides/example/review"
        shutil.copytree(REPO_ROOT / "tests/fixtures/daodan/overrides/copilot/example/review",
                        directory)
        source = self.root / "plugins/example/workflows/review.md"
        manifest = directory / "override.toml"
        original = manifest.read_text(encoding="utf-8")
        original = re.sub(r'(?m)^source_paths = .*$',
                          'source_paths = ["plugins/example/workflows/review.md"]', original)
        original = re.sub(r'(?m)^reviewed_against = .*$',
                          f'reviewed_against = "{source_digest([source], self.root)}"', original)
        cases = (
            ("workflow:review", [], "override-drops-contract", "reviewers-use-isolated-contexts"),
            ("role:inspector", [], "override-drops-contract", "reviewers-use-isolated-contexts"),
            ("workflow:missing", ["reviewers-use-isolated-contexts"], "override-unknown-source", "workflow:missing"),
            ("skill:tools", [], "override-unknown-source", "skill:tools"),
        )
        for source_name, outcomes, code, detail in cases:
            content = re.sub(r'(?m)^source = .*$', f'source = "{source_name}"', original)
            content = re.sub(r'(?m)^contracts_preserved = .*$',
                             "contracts_preserved = " + json.dumps(outcomes), content)
            manifest.write_text(content, encoding="utf-8")
            for check in (False, True):
                with self.subTest(source=source_name, check=check):
                    report = build_repository(self.root, HOSTS, check=check)

                    self.assertTrue(report.has_failures)
                    diagnoses = [issue for issue in report.issues if issue.code == code]
                    self.assertTrue(diagnoses, report.issues)
                    self.assertTrue(any(detail in issue.message for issue in diagnoses))
                    self.assertEqual(self.output_bytes(), before)

        manifest.write_text(original, encoding="utf-8")
        code, output = self.run_cli()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_role_override_preserves_outcomes_of_cross_plugin_consumers(self):
        """O03 a provider role carries contracts from every consuming workflow."""
        consumer = self.root / "plugins/consumer"
        shutil.copytree(VALID, consumer)
        plugin_manifest = consumer / "plugin.toml"
        content = plugin_manifest.read_text(encoding="utf-8")
        plugin_manifest.write_text(content.replace('name = "example"', 'name = "consumer"')
                                  .replace('required = []', 'required = ["example"]'), encoding="utf-8")
        workflow = consumer / "workflows/review.toml"
        content = workflow.read_text(encoding="utf-8")
        workflow.write_text(content.replace('"role:inspector"', '"role:example/inspector"')
                            .replace('"reviewers-use-isolated-contexts"', '"consumer-report-delivered"'),
                            encoding="utf-8")
        directory = self.root / "adapters/copilot/overrides/example/review"
        shutil.copytree(REPO_ROOT / "tests/fixtures/daodan/overrides/copilot/example/review",
                        directory)
        source = self.root / "plugins/example/roles/inspector.md"
        manifest = directory / "override.toml"
        content = manifest.read_text(encoding="utf-8").replace('source = "workflow:review"',
                                                             'source = "role:inspector"')
        content = re.sub(r'(?m)^source_paths = .*$',
                         'source_paths = ["plugins/example/roles/inspector.md"]', content)
        content = re.sub(r'(?m)^reviewed_against = .*$',
                         f'reviewed_against = "{source_digest([source], self.root)}"', content)
        manifest.write_text(content, encoding="utf-8")

        rejected = build_repository(self.root, ("copilot",), check=True)

        self.assertEqual([(issue.code, issue.message) for issue in rejected.issues],
                         [("override-drops-contract", "consumer-report-delivered")])
        self.assertFalse((self.root / "exports").exists())
        manifest.write_text(content.replace('contracts_preserved = ["reviewers-use-isolated-contexts"]',
                                           'contracts_preserved = ["reviewers-use-isolated-contexts", '
                                           '"consumer-report-delivered"]'), encoding="utf-8")

        accepted = build_repository(self.root, ("copilot",), check=True)

        self.assertEqual(accepted.issues, ())
        self.assertTrue(accepted.drift, "Fresh fixture has no published packages")
        self.assertFalse((self.root / "exports").exists())

    def test_check_reports_drift_after_a_kernel_edit(self):
        self.assertEqual(self.run_cli()[0], 0)
        role = self.root / "plugins/example/roles/inspector.md"
        role.write_text(role.read_text(encoding="utf-8") + "\nEdited.\n", encoding="utf-8")
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("generated-drift", output)

    def test_check_reports_drift_when_output_is_missing(self):
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("generated-drift", output)

    def test_partial_publication_is_an_invocation_error(self):
        code, output = self.run_cli("--host", "claude")
        self.assertEqual(code, 2)
        self.assertIn("together", output)

    def test_partial_host_is_allowed_under_check(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--check", "--host", "claude")[0], 0)

    def test_validation_failure_writes_nothing(self):
        manifest = self.root / "plugins/example/plugin.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                '"repository.read"', '"telepathy.read"'
            ),
            encoding="utf-8",
        )
        code, output = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("unknown-capability", output)
        self.assertFalse((self.root / "exports").exists())

    def test_duplicate_identity_preserves_outputs_in_repeated_build_and_check(self):
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        roots = [self.root / "plugins/example", self.root / "plugins/example-copy"]
        shutil.copytree(VALID, roots[1])

        for check in (False, True):
            with self.subTest(check=check):
                diagnoses = []
                for _ in range(2):
                    report = build_repository(self.root, HOSTS, check=check)
                    diagnosis = io.StringIO()
                    report.write(diagnosis)
                    diagnoses.append(diagnosis.getvalue())

                    self.assertTrue(report.has_failures)
                    self.assertTrue(any("duplicate" in issue.code.lower() for issue in report.issues))
                    self.assertIn("example", diagnoses[-1])
                    for root in roots:
                        self.assertIn(str(root), diagnoses[-1])
                    self.assertEqual(self.output_bytes(), before)
                self.assertEqual(diagnoses[0], diagnoses[1])

    def test_all_three_hosts_are_published_together(self):
        self.assertEqual(self.run_cli()[0], 0)
        for host in ("claude", "copilot", "codex"):
            self.assertTrue((self.root / "exports" / host / "plugins/example").is_dir())
        self.assertTrue((self.root / ".claude-plugin/marketplace.json").is_file())
        self.assertTrue((self.root / ".github/plugin/marketplace.json").is_file())
        self.assertTrue((self.root / ".agents/plugins/marketplace.json").is_file())

    def test_opencode_package_ships_the_loader_and_its_manifest(self):
        self.assertEqual(self.run_cli()[0], 0)
        package = self.root / "exports/opencode"
        self.assertEqual(
            (package / "index.js").read_bytes(),
            (self.root / "adapters/opencode/templates/index.js").read_bytes(),
        )
        self.assertTrue((package / "package.json").is_file())
        self.assertTrue((package / "plugins/example/agents/inspector.md").is_file())

    def test_check_reports_drift_when_the_loader_is_edited(self):
        self.assertEqual(self.run_cli()[0], 0)
        loader = self.root / "exports/opencode/index.js"
        loader.write_text(loader.read_text(encoding="utf-8") + "// edited" + chr(10), encoding="utf-8")
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("index.js", output)

    def test_support_table_names_every_host(self):
        report = build_repository(self.root, ("claude", "copilot", "codex"), check=True)
        self.assertEqual({item.host for item in report.support}, {"claude", "copilot", "codex"})

    def test_retired_generated_plugin_is_drift_then_removed_on_every_host(self):
        self.assertEqual(self.run_cli()[0], 0)
        shutil.rmtree(self.root / "plugins/example")
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("plugins/example", output.replace("\\", "/"))
        code, output = self.run_cli()
        self.assertEqual(code, 0, output)
        for host in ("claude", "copilot", "codex", "pi", "opencode"):
            self.assertFalse((self.root / "exports" / host / "plugins/example").exists())
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_failed_validation_preserves_retired_and_current_outputs(self):
        self.assertEqual(self.run_cli()[0], 0)
        shutil.copytree(VALID, self.root / "plugins/remaining")
        manifest = self.root / "plugins/remaining/plugin.toml"
        manifest.write_text(manifest.read_text().replace('name = "example"', 'name = "remaining"')
                            .replace('"repository.read"', '"telepathy.read"'))
        shutil.rmtree(self.root / "plugins/example")
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*")
                  if path.is_file() and "plugins" not in path.relative_to(self.root).parts[:1]}
        self.assertEqual(self.run_cli()[0], 1)
        for path, content in before.items():
            self.assertEqual((self.root / path).read_bytes(), content)
        for host in ("claude", "copilot", "codex", "pi", "opencode"):
            self.assertTrue((self.root / "exports" / host / "plugins/example").is_dir())

    def test_unknown_or_mismatched_output_directory_is_never_pruned(self):
        self.assertEqual(self.run_cli()[0], 0)
        unknown = self.root / "exports/claude/plugins/user-files"
        unknown.mkdir()
        (unknown / "important.txt").write_text("preserve")
        self.assertEqual(self.run_cli()[0], 1)
        self.assertEqual((unknown / "important.txt").read_text(), "preserve")

    def test_mismatched_provenance_cannot_authorize_retirement(self):
        self.assertEqual(self.run_cli()[0], 0)
        shutil.rmtree(self.root / "plugins/example")
        provenance = self.root / "exports/claude/plugins/example/.daodan-provenance.json"
        document = json.loads(provenance.read_text())
        document["host"] = "codex"
        provenance.write_text(json.dumps(document))
        code, output = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("unsafe-generated-output", output)
        for host in ("claude", "copilot", "codex", "pi", "opencode"):
            self.assertTrue((self.root / "exports" / host / "plugins/example").is_dir())

    def test_linked_output_root_is_refused_without_touching_target(self):
        self.assertEqual(self.run_cli()[0], 0)
        generated = self.root / "exports/claude/plugins"
        target = self.root / "outside-generated"
        shutil.move(generated, target)
        try:
            generated.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        before = {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}
        self.assertEqual(self.run_cli()[0], 1)
        self.assertEqual({path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}, before)

    def test_build_reports_failed_publication_and_restores_the_affected_package(self):
        """C05 diagnostic control protects the actual builder error path."""
        self.assertEqual(self.run_cli()[0], 0)
        live = self.root / "exports/claude/plugins/example"
        before = {path.relative_to(live): path.read_bytes()
                  for path in live.rglob("*") if path.is_file()}
        original_rename = Path.rename
        attempted = []

        def fail_replacement(path, destination):
            if Path(destination) == live and path.name.endswith(".staging"):
                attempted.append(path)
                raise OSError("owned publication failure")
            return original_rename(path, destination)

        with patch.object(Path, "rename", fail_replacement), patch("scripts.daodan.render.time.sleep"):
            report = build_repository(self.root, HOSTS, check=False)

        self.assertTrue(attempted, "Fault must follow live-to-previous rename")
        self.assertTrue(report.has_failures)
        diagnostic = io.StringIO()
        report.write(diagnostic)
        self.assertIn("owned publication failure", diagnostic.getvalue())
        self.assertIn(str(live), diagnostic.getvalue())
        self.assertEqual(
            {path.relative_to(live): path.read_bytes()
             for path in live.rglob("*") if path.is_file()}, before)
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--check")[0], 0)

    def _assert_individual_catalog_write_preserves_old_bytes(self, fault_type):
        """C06 observes complete bytes through real build and file-write boundary."""
        self.assertEqual(self.run_cli()[0], 0)
        destinations = (
            ".claude-plugin/marketplace.json",
            ".github/plugin/marketplace.json",
            ".agents/plugins/marketplace.json",
            "package.json",
            "exports/opencode/package.json",
        )
        original_builtin, original_io = builtins.open, io.open
        for relative in destinations:
            target = self.root / relative
            before = target.read_bytes()
            injected = []
            signal = fault_type("owned catalog write failure")

            class InterruptedWriter:
                def __init__(writer, handle, path):
                    writer.handle, writer.path = handle, path

                def __getattr__(writer, name):
                    return getattr(writer.handle, name)

                def __enter__(writer):
                    writer.handle.__enter__()
                    return writer

                def __exit__(writer, *arguments):
                    return writer.handle.__exit__(*arguments)

                def write(writer, data):
                    raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
                    if not injected and raw.startswith(b"{") and len(raw) > 50:
                        writer.handle.write(data[:17])
                        writer.handle.flush()
                        injected.append(str(writer.path))
                        raise signal
                    return writer.handle.write(data)

            def watch(original):
                def open_owned(file, mode="r", *arguments, **keywords):
                    handle = original(file, mode, *arguments, **keywords)
                    if not isinstance(file, int) and any(flag in mode for flag in ("w", "a", "+")):
                        path = Path(file).absolute()
                        if path.parent == target.parent:
                            return InterruptedWriter(handle, path)
                    return handle
                return open_owned

            try:
                with patch("builtins.open", watch(original_builtin)), patch("io.open", watch(original_io)):
                    try:
                        build_repository(self.root, HOSTS, check=False)
                    except (OSError, KeyboardInterrupt, SystemExit):
                        pass

                with self.subTest(catalog=relative, fault=fault_type.__name__, contract="complete old bytes"):
                    self.assertEqual(len(injected), 1, "Catalog fault boundary was not reached")
                    self.assertEqual(target.read_bytes(), before)
                    json.loads(target.read_bytes())

                with self.subTest(catalog=relative, fault=fault_type.__name__, contract="later real build"):
                    code, output = self.run_cli()
                    self.assertEqual(code, 0, output)
                    self.assertEqual(self.run_cli("--check")[0], 0)
            finally:
                # Restore only this owned fixture so every red host case can execute.
                target.write_bytes(before)

    def test_interrupted_catalog_writes_preserve_complete_old_bytes_on_every_host(self):
        self._assert_individual_catalog_write_preserves_old_bytes(KeyboardInterrupt)

    def test_failed_catalog_writes_preserve_complete_old_bytes_on_every_host(self):
        self._assert_individual_catalog_write_preserves_old_bytes(OSError)



    def test_nonboolean_coordination_reports_structured_failure_before_publication(self):
        """C09 build and check preserve all five catalogs and existing packages."""
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        coordination = self.root / "adapters/codex/coordination.toml"
        original = coordination.read_text(encoding="utf-8")
        flags = {"isolated": "true", "parallel": "true",
                 "shared_tasks": "false", "peer_messaging": "false"}
        for flag, old_value in flags.items():
            for invalid in ('"false"', "0"):
                coordination.write_text(original.replace(
                    f"{flag} = {old_value}", f"{flag} = {invalid}", 1),
                    encoding="utf-8")
                for check in (False, True):
                    with self.subTest(flag=flag, value=invalid, check=check):
                        try:
                            report = build_repository(self.root, HOSTS, check=check)
                        finally:
                            self.assertEqual(self.output_bytes(), before)

                        self.assertTrue(report.has_failures)
                        diagnoses = [issue for issue in report.issues
                                     if issue.path == coordination]
                        self.assertTrue(diagnoses, "Diagnostic must name the offending TOML")
                        self.assertTrue(all(issue.code and issue.message for issue in diagnoses))
                        self.assertTrue(any(flag in issue.message and
                                            "boolean" in issue.message.lower()
                                            for issue in diagnoses))
        coordination.write_text(original, encoding="utf-8")
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_scalar_phase_elements_report_structured_failure_before_publication(self):
        """C10 cannot leak TypeError or publish from malformed phase metadata."""
        self.assertEqual(self.run_cli()[0], 0)
        before = self.output_bytes()
        sidecar = self.root / "plugins/example/workflows/review.toml"
        original = sidecar.read_text(encoding="utf-8")
        contract = original[original.index("[contract]"):]
        for invalid in ('"inspect"', "17", "true"):
            for index in (0, 1):
                leading = '{ id = "inspect" }, ' if index else ""
                sidecar.write_text('name = "review"\nentrypoint = "review.md"\n'
                                   f"phases = [{leading}{invalid}]\n\n" + contract,
                                   encoding="utf-8")
                for check in (False, True):
                    with self.subTest(value=invalid, index=index, check=check):
                        try:
                            report = build_repository(self.root, HOSTS, check=check)
                        finally:
                            self.assertEqual(self.output_bytes(), before)

                        self.assertTrue(report.has_failures)
                        diagnoses = [issue for issue in report.issues if issue.path == sidecar]
                        self.assertTrue(diagnoses, "Diagnostic must name the offending sidecar")
                        self.assertTrue(all(issue.code and issue.message for issue in diagnoses))
                        self.assertTrue(any("phase" in issue.message.lower()
                                            for issue in diagnoses))
                        self.assertTrue(any(re.search(rf"\b{index}\b", issue.message)
                                            for issue in diagnoses))
        sidecar.write_text(original, encoding="utf-8")
        self.assertEqual(self.run_cli("--check")[0], 0)



class ManifestPublicationTests(unittest.TestCase):
    def test_transient_manifest_sharing_violation_retries_the_same_complete_file(self):
        import os

        with tempfile.TemporaryDirectory(prefix="daodan-manifest-") as holder:
            root = Path(holder)
            manifest = root / "package.json"
            manifest.write_bytes(b"original manifest")
            original_replace = os.replace
            attempts = []

            def replace_after_sharing(source, destination):
                attempts.append(Path(source))
                self.assertEqual(Path(source).read_bytes(), b"complete new manifest")
                if len(attempts) == 1:
                    self.assertEqual(manifest.read_bytes(), b"original manifest")
                    error = OSError("transient Windows sharing violation")
                    error.winerror = 32
                    raise error
                return original_replace(source, destination)

            with patch("scripts.daodan_build.os.replace", replace_after_sharing), \
                    patch("scripts.daodan.render.time.sleep"):
                _publish_file(manifest, b"complete new manifest")

            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[0], attempts[1])
            self.assertEqual(manifest.read_bytes(), b"complete new manifest")
            self.assertEqual(list(root.iterdir()), [manifest])

    def test_persistent_manifest_publication_failure_preserves_the_original_and_cleans_temp(self):
        from scripts.daodan.render import RenderError

        with tempfile.TemporaryDirectory(prefix="daodan-manifest-") as holder:
            root = Path(holder)
            manifest = root / "package.json"
            manifest.write_bytes(b"original manifest")
            with patch("scripts.daodan_build.os.replace", side_effect=OSError("locked")) as replace, \
                    patch("scripts.daodan.render.time.sleep"):
                with self.assertRaises(RenderError):
                    _publish_file(manifest, b"complete new manifest")

            self.assertEqual(replace.call_count, 10)
            self.assertEqual(manifest.read_bytes(), b"original manifest")
            self.assertEqual(list(root.iterdir()), [manifest])

    def _locked_replace(self, winerror=32, errno_value=None):
        """A destination another process holds open: every rename fails the same way."""
        def always_locked(source, destination):
            error = OSError("held open by another process")
            if winerror is not None:
                error.winerror = winerror
            if errno_value is not None:
                error.errno = errno_value
            raise error
        return always_locked

    def test_a_persistent_sharing_violation_publishes_in_place_and_warns(self):
        # The host this repository ships to runs an indexer that keeps a root manifest
        # open without delete sharing and respawns when stopped, so the atomic replace is
        # not merely transiently impossible there: publication falls back to a verified
        # in-place write and says so, instead of never publishing at all.
        with tempfile.TemporaryDirectory(prefix="daodan-manifest-") as holder:
            root = Path(holder)
            manifest = root / "package.json"
            manifest.write_bytes(b"original manifest")
            with patch("scripts.daodan_build.os.replace", self._locked_replace()), \
                    patch("scripts.daodan.render.time.sleep"):
                warning = _publish_file(manifest, b"complete new manifest")

            self.assertEqual(manifest.read_bytes(), b"complete new manifest")
            self.assertIn("not atomically", warning)
            self.assertIn("package.json", warning)
            self.assertEqual(list(root.iterdir()), [manifest])

    def test_a_posix_busy_error_takes_the_same_verified_in_place_path(self):
        import errno as errno_module

        with tempfile.TemporaryDirectory(prefix="daodan-manifest-") as holder:
            manifest = Path(holder) / "marketplace.json"
            manifest.write_bytes(b"original")
            with patch("scripts.daodan_build.os.replace",
                       self._locked_replace(winerror=None,
                                            errno_value=errno_module.EBUSY)), \
                    patch("scripts.daodan.render.time.sleep"):
                warning = _publish_file(manifest, b"rendered")

            self.assertEqual(manifest.read_bytes(), b"rendered")
            self.assertIn("not atomically", warning)

    def test_an_in_place_publication_that_does_not_verify_restores_the_original(self):
        from scripts.daodan.render import RenderError

        with tempfile.TemporaryDirectory(prefix="daodan-manifest-") as holder:
            root = Path(holder)
            manifest = root / "package.json"
            manifest.write_bytes(b"original manifest")
            with patch("scripts.daodan_build.os.replace", self._locked_replace()), \
                    patch("scripts.daodan.render.time.sleep"), \
                    patch("scripts.daodan_build._read_back", return_value=b"a torn write"):
                with self.assertRaises(RenderError):
                    _publish_file(manifest, b"complete new manifest")

            self.assertEqual(manifest.read_bytes(), b"original manifest")
            self.assertEqual(list(root.iterdir()), [manifest])

    def test_a_held_destination_that_does_not_exist_yet_is_created_in_place(self):
        with tempfile.TemporaryDirectory(prefix="daodan-manifest-") as holder:
            root = Path(holder)
            manifest = root / "package.json"
            with patch("scripts.daodan_build.os.replace", self._locked_replace()), \
                    patch("scripts.daodan.render.time.sleep"):
                warning = _publish_file(manifest, b"complete new manifest")

            self.assertEqual(manifest.read_bytes(), b"complete new manifest")
            self.assertIn("not atomically", warning)
            self.assertEqual(list(root.iterdir()), [manifest])

    def test_a_warning_is_reported_and_never_counts_as_a_failure(self):
        from scripts.daodan.report import BuildReport, merge

        report = BuildReport(warnings=("published in place, not atomically: package.json",))
        self.assertFalse(report.has_failures)
        stream = io.StringIO()
        report.write(stream)
        self.assertEqual(stream.getvalue(),
                         "warning: published in place, not atomically: package.json\n")
        merged = merge([report, BuildReport(warnings=("second",))])
        self.assertEqual(merged.warnings,
                         ("published in place, not atomically: package.json", "second"))


if __name__ == "__main__":
    unittest.main()
