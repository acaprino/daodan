"""Reproducibility and rollback tests for the package renderer."""

import json
import builtins
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.overrides import source_digest  # noqa: E402
from scripts.daodan.render import (  # noqa: E402
    RenderError,
    publish_plugin,
    render_plugin,
    replace_tree,
    tree_digest,
)

ADAPTERS = REPO_ROOT / "adapters"
VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)

    def compile_fixture(self, host: str) -> Path:
        live = self.temp / f"live-{host}-{len(list(self.temp.iterdir()))}"
        publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, host), live)
        return live

    def compile_invalid_fixture(self, live: Path) -> None:
        adapter = load_adapter(ADAPTERS, "codex")
        bindings = dict(adapter.bindings)
        bindings["contexts.isolate"] = replace(bindings["contexts.isolate"], state="unsupported")
        publish_plugin(load_plugin(VALID), replace(adapter, bindings=bindings), live)

    def assert_rejected_before_read(self, target: Path, action) -> None:
        """C01 requires confinement before the filesystem byte-read boundary."""
        attempted = []
        original_builtin = builtins.open
        original_io = io.open
        resolved_target = target.resolve()

        def watch(original):
            def open_owned(file, mode="r", *args, **kwargs):
                if not isinstance(file, int) and Path(file).resolve() == resolved_target:
                    if "r" in mode or "+" in mode:
                        attempted.append(Path(file))
                        raise AssertionError("Out-of-root source was opened before rejection")
                return original(file, mode, *args, **kwargs)
            return open_owned

        with patch("builtins.open", watch(original_builtin)), patch("io.open", watch(original_io)):
            with self.assertRaises(RenderError):
                action()
        self.assertEqual(attempted, [])

    def test_linked_binary_skill_member_is_rejected_before_read_and_publish(self):
        kernel = self.temp / "kernel"
        shutil.copytree(REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example", kernel)
        target = self.temp / "owned-outside.bin"
        target.write_bytes(b"benign C01 fixture\x00\xff")
        (kernel / "skills/tools/assets").mkdir()
        (kernel / "skills/tools/assets/asset.bin").symlink_to(target)
        plugin = load_plugin(kernel)
        adapter = load_adapter(ADAPTERS, "claude")
        live = self.temp / "live"
        live.mkdir()
        (live / "sentinel").write_bytes(b"previous published bytes")

        self.assert_rejected_before_read(
            target, lambda: publish_plugin(plugin, adapter, live)
        )

        self.assertEqual((live / "sentinel").read_bytes(), b"previous published bytes")
        self.assertEqual(sorted(path.name for path in live.iterdir()), ["sentinel"])

    def test_selected_kernel_resources_are_rejected_before_read_when_linked_outside(self):
        members = (
            "roles/inspector.md",
            "workflows/review.md",
            "contracts/reviewer-result.toml",
            "skills/tools/SKILL.md",
            "skills/tools/scripts/server.py",
            "policies/write-confinement.toml",
            "ordinary-unused.bin",
        )
        for number, member in enumerate(members):
            with self.subTest(member=member):
                kernel = self.temp / f"kernel-{number}"
                shutil.copytree(REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example", kernel)
                plugin = load_plugin(kernel)
                if member.startswith("policies/"):
                    plugin = replace(plugin, components=replace(plugin.components, policies=("write-confinement",)))
                selected = kernel / member
                selected.parent.mkdir(parents=True, exist_ok=True)
                if selected.exists():
                    selected.unlink()
                target = self.temp / f"owned-target-{number}.txt"
                target.write_bytes(b"benign external fixture\n")
                selected.symlink_to(target)
                adapter = load_adapter(ADAPTERS, "claude")

                self.assert_rejected_before_read(
                    target, lambda: render_plugin(plugin, adapter, self.temp / f"staging-{number}")
                )

    def test_linked_role_directory_is_rejected_before_reading_its_member(self):
        kinds = ("symlink", "junction") if os.name == "nt" else ("symlink",)
        for kind in kinds:
            with self.subTest(link_kind=kind):
                kernel = self.temp / f"kernel-{kind}"
                shutil.copytree(VALID, kernel)
                plugin = load_plugin(kernel)
                target_directory = self.temp / f"owned-roles-{kind}"
                link = kernel / "roles"
                self.assertTrue(link.resolve().is_relative_to(self.temp.resolve()))
                self.assertTrue(target_directory.resolve().is_relative_to(self.temp.resolve()))
                shutil.move(link, target_directory)
                if kind == "symlink":
                    link.symlink_to(target_directory, target_is_directory=True)
                else:
                    environment = {
                        **os.environ,
                        "DAODAN_C01_LINK": str(link),
                        "DAODAN_C01_TARGET": str(target_directory),
                    }
                    created = subprocess.run(
                        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                         "New-Item -ItemType Junction -Path $env:DAODAN_C01_LINK -Target $env:DAODAN_C01_TARGET -ErrorAction Stop | Out-Null"],
                        env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(created.returncode, 0, created.stderr)
                    self.addCleanup(link.rmdir)
                    self.assertTrue(link.lstat().st_file_attributes & 0x400)
                self.assertEqual(link.resolve(), target_directory.resolve())
                adapter = load_adapter(ADAPTERS, "claude")

                self.assert_rejected_before_read(
                    target_directory / "inspector.md",
                    lambda: render_plugin(plugin, adapter, self.temp / f"staging-{kind}"),
                )

    def test_linked_adapter_templates_are_rejected_before_read(self):
        for number, name in enumerate(("plugin.json.tmpl", "worker.agent.md.tmpl", "team-workflow.md.tmpl")):
            with self.subTest(template=name):
                adapters = self.temp / f"adapters-{number}"
                shutil.copytree(ADAPTERS, adapters)
                host = "copilot" if name == "worker.agent.md.tmpl" else "claude"
                adapter = load_adapter(adapters, host)
                selected = adapters / host / "templates" / name
                target = self.temp / f"owned-template-{number}.txt"
                target.write_bytes(selected.read_bytes())
                selected.unlink()
                selected.symlink_to(target)
                plugin = load_plugin(VALID)

                self.assert_rejected_before_read(
                    target, lambda: render_plugin(plugin, adapter, self.temp / f"staging-{number}", adapters_root=adapters)
                )

    def test_linked_policy_implementation_is_rejected_before_read(self):
        adapters = self.temp / "adapters"
        shutil.copytree(ADAPTERS, adapters)
        kernel = self.temp / "kernel"
        shutil.copytree(VALID, kernel)
        (kernel / "policies").mkdir()
        (kernel / "policies/write-confinement.toml").write_text('root = "owned"\n', encoding="utf-8")
        plugin = load_plugin(kernel)
        plugin = replace(plugin, components=replace(plugin.components, policies=("write-confinement",)))
        adapter = load_adapter(adapters, "copilot")
        member = adapters / "copilot/policies/xray-guard/xray_guard.py"
        target = self.temp / "owned-policy.txt"
        target.write_bytes(b"benign policy fixture\n")
        member.unlink()
        member.symlink_to(target)

        self.assert_rejected_before_read(
            target, lambda: render_plugin(plugin, adapter, self.temp / "staging", adapters_root=adapters)
        )

    def test_ordinary_skill_resources_are_preserved_on_every_host(self):
        kernel = self.temp / "kernel"
        shutil.copytree(REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example", kernel)
        resources = kernel / "skills/tools/assets"
        resources.mkdir()
        (resources / "asset.bin").write_bytes(b"benign C01 fixture\x00\xff\r\n")
        (resources / "guide.txt").write_bytes(b"first line\r\nsecond line\r")
        plugin = load_plugin(kernel)

        for host in HOSTS:
            with self.subTest(host=host):
                live = self.temp / host
                publish_plugin(plugin, load_adapter(ADAPTERS, host), live)

                self.assertEqual((live / "skills/tools/assets/asset.bin").read_bytes(), b"benign C01 fixture\x00\xff\r\n")
                self.assertEqual((live / "skills/tools/assets/guide.txt").read_bytes(), b"first line\nsecond line\n")

    def test_equal_inputs_produce_equal_bytes(self):
        first = self.compile_fixture("claude")
        second = self.compile_fixture("claude")
        self.assertEqual(tree_digest(first), tree_digest(second))

    def test_hosts_produce_different_trees(self):
        self.assertNotEqual(
            tree_digest(self.compile_fixture("claude")),
            tree_digest(self.compile_fixture("copilot")),
        )

    def test_failed_validation_keeps_live_tree(self):
        live = self.temp / "live"
        live.mkdir()
        (live / "sentinel").write_text("old", encoding="utf-8")
        with self.assertRaises(RenderError):
            self.compile_invalid_fixture(live)
        self.assertEqual((live / "sentinel").read_text(encoding="utf-8"), "old")

    def test_nothing_is_written_outside_the_destination(self):
        old = {Path("sentinel.bin"): b"old published bytes\x00\xff",
               Path("nested/old.txt"): b"old nested publication\n"}
        foreign = {Path("foreign.bin"): b"foreign sibling\x00\xfe",
                   Path("foreign-dir/keep.txt"): b"foreign nested sibling\n"}
        for outcome in ("success", "validation-error", "publication-error"):
            with self.subTest(outcome=outcome):
                parent = self.temp / outcome
                live = parent / "live"
                (live / "nested").mkdir(parents=True)
                (parent / "foreign-dir").mkdir()
                for path, content in old.items():
                    (live / path).write_bytes(content)
                for path, content in foreign.items():
                    (parent / path).write_bytes(content)
                before = {path.name for path in parent.iterdir()}
                observed_backup = []
                original_rename = Path.rename

                def fail_publication(path, destination):
                    if path.name.endswith(".staging") and Path(destination) == live:
                        previous = parent / ".live.previous"
                        observed_backup.append({item.relative_to(previous): item.read_bytes()
                                                for item in previous.rglob("*") if item.is_file()})
                        raise OSError("owned publication failure")
                    return original_rename(path, destination)

                if outcome == "validation-error":
                    with self.assertRaises(RenderError):
                        self.compile_invalid_fixture(live)
                elif outcome == "publication-error":
                    with patch.object(Path, "rename", fail_publication), \
                            patch("scripts.daodan.render.time.sleep"):
                        with self.assertRaises(RenderError):
                            publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, "claude"), live)
                else:
                    publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, "claude"), live)

                # The stable OS-lock sibling is intentional; staging/backup are temporary.
                expected_names = before if outcome == "validation-error" else before | {".live.lock"}
                self.assertEqual({path.name for path in parent.iterdir()}, expected_names)
                self.assertEqual({path: (parent / path).read_bytes() for path in foreign}, foreign)
                if outcome == "success":
                    self.assertTrue((live / "agents/inspector.md").is_file())
                    self.assertTrue((live / ".claude-plugin/plugin.json").is_file())
                    self.assertFalse((live / "sentinel.bin").exists())
                else:
                    self.assertEqual({item.relative_to(live): item.read_bytes()
                                      for item in live.rglob("*") if item.is_file()}, old)
                if outcome == "publication-error":
                    self.assertTrue(observed_backup, "The backup branch was not exercised")
                    self.assertTrue(all(snapshot == old for snapshot in observed_backup))


    def test_provenance_has_exactly_the_declared_keys(self):
        live = self.compile_fixture("claude")
        provenance = json.loads(
            (live / ".daodan-provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sorted(provenance),
            [
                "adapterVersion",
                "coreDigest",
                "harnessStrategies",
                "host",
                "overrides",
                "plugin",
                "version",
            ],
        )
        self.assertEqual(provenance["host"], "claude")
        self.assertEqual(provenance["plugin"], "example")
        self.assertEqual(provenance["version"], "1.2.3")
        self.assertEqual(provenance["harnessStrategies"], {"review": "native-team"})
        self.assertTrue(provenance["coreDigest"].startswith("sha256:"))
        self.assertEqual(len(provenance["coreDigest"].split(":")[1]), 64)

    def test_core_digest_is_independent_of_checkout_location(self):
        """The digest is a property of the kernel, not of where it sits.

        It used to hash absolute paths and raw bytes, so the same source hashed
        differently on a Windows checkout and a Linux runner, and CI reported
        drift against a tree that was identical.
        """
        first = render_plugin(
            load_plugin(VALID), load_adapter(ADAPTERS, "claude"), self.temp / "staging"
        ).core_digest

        elsewhere = self.temp / "relocated" / "example"
        shutil.copytree(VALID, elsewhere)
        second = render_plugin(
            load_plugin(elsewhere), load_adapter(ADAPTERS, "claude"), self.temp / "staging2"
        ).core_digest
        self.assertEqual(first, second)

    def test_core_digest_ignores_line_endings(self):
        crlf = self.temp / "crlf" / "example"
        shutil.copytree(VALID, crlf)
        for path in crlf.rglob("*"):
            if path.is_file():
                path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(
            render_plugin(
                load_plugin(VALID), load_adapter(ADAPTERS, "claude"), self.temp / "s1"
            ).core_digest,
            render_plugin(
                load_plugin(crlf), load_adapter(ADAPTERS, "claude"), self.temp / "s2"
            ).core_digest,
        )

    def test_generated_text_is_lf_normalized(self):
        live = self.compile_fixture("claude")
        for path in live.rglob("*.md"):
            self.assertNotIn(b"\r\n", path.read_bytes())

    def test_replace_tree_restores_the_previous_tree_on_failure(self):
        live = self.temp / "swap"
        live.mkdir()
        (live / "sentinel").write_text("old", encoding="utf-8")
        staging = self.temp / "staging-missing"
        with self.assertRaises(RenderError):
            replace_tree(staging, live)
        self.assertEqual((live / "sentinel").read_text(encoding="utf-8"), "old")


    def test_cancellation_immediately_after_first_live_move_restores_the_publication(self):
        """Interrupt after the real first rename returns, before the next source line."""
        live, staging = self.temp / "first-move-live", self.temp / "first-move-staging"
        previous = self.temp / ".first-move-live.previous"
        old = {Path("sentinel.bin"): b"old exact bytes\x00\xff\r\n",
               Path("nested/old.txt"): b"old nested publication\n"}
        new = {Path("replacement.bin"): b"complete new publication\x00\xfe"}
        (live / "nested").mkdir(parents=True)
        staging.mkdir()
        for path, content in old.items():
            (live / path).write_bytes(content)
        for path, content in new.items():
            (staging / path).write_bytes(content)
        cancellation = KeyboardInterrupt("owned interruption immediately after first move")
        observed = []
        original_trace = sys.gettrace()

        def interrupt_after_real_move(frame, event, argument):
            if event == "line" and frame.f_code is replace_tree.__code__ and \
                    previous.is_dir() and not live.exists() and not observed:
                observed.append({item.relative_to(previous): item.read_bytes()
                                 for item in previous.rglob("*") if item.is_file()})
                sys.settrace(None)
                raise cancellation
            return interrupt_after_real_move

        try:
            sys.settrace(interrupt_after_real_move)
            with self.assertRaises(KeyboardInterrupt) as caught:
                replace_tree(staging, live)
        finally:
            sys.settrace(original_trace)

        self.assertIs(caught.exception, cancellation)
        self.assertEqual(observed, [old], "The real first move must have completed")
        self.assertTrue(live.is_dir(), "Cancellation left the published path absent")
        self.assertEqual({item.relative_to(live): item.read_bytes()
                          for item in live.rglob("*") if item.is_file()}, old)
        self.assertEqual({item.relative_to(staging): item.read_bytes()
                          for item in staging.rglob("*") if item.is_file()}, new)
        self.assertFalse(previous.exists())

        replace_tree(staging, live)

        self.assertEqual({item.relative_to(live): item.read_bytes()
                          for item in live.rglob("*") if item.is_file()}, new)

    def test_error_before_first_live_move_keeps_live_and_staging_complete(self):
        live, staging = self.temp / "before-move-live", self.temp / "before-move-staging"
        previous = self.temp / ".before-move-live.previous"
        live.mkdir()
        staging.mkdir()
        (live / "old.bin").write_bytes(b"complete old bytes\x00\xff")
        (staging / "new.bin").write_bytes(b"complete new bytes\x00\xfe")
        error = OSError("owned first move failure")
        original_rename = Path.rename

        def reject_first_move(path, destination):
            if path == live and Path(destination) == previous:
                raise error
            return original_rename(path, destination)

        with patch.object(Path, "rename", reject_first_move), \
                patch("scripts.daodan.render.time.sleep"):
            with self.assertRaises(RenderError) as caught:
                replace_tree(staging, live)

        self.assertIs(caught.exception.__cause__, error)
        self.assertEqual((live / "old.bin").read_bytes(), b"complete old bytes\x00\xff")
        self.assertEqual((staging / "new.bin").read_bytes(), b"complete new bytes\x00\xfe")
        self.assertFalse(previous.exists())

        replace_tree(staging, live)

        self.assertEqual((live / "new.bin").read_bytes(), b"complete new bytes\x00\xfe")

    def test_cancellation_after_live_move_restores_bytes_and_preserves_signal(self):
        """C05 observes old bytes after mutation and the original cancellation."""
        class OwnedCancellation(BaseException):
            pass

        for number, signal in enumerate((KeyboardInterrupt("cancel"), SystemExit(23),
                                         OwnedCancellation("cancel"))):
            with self.subTest(signal=type(signal).__name__):
                live = self.temp / f"cancel-live-{number}"
                staging = self.temp / f"cancel-staging-{number}"
                live.mkdir()
                (live / "nested").mkdir()
                old = {Path("sentinel"): b"old bytes\x00\xff",
                       Path("nested/guide.txt"): b"old nested bytes\n"}
                for path, content in old.items():
                    (live / path).write_bytes(content)
                staging.mkdir()
                (staging / "sentinel").write_bytes(b"new publication")
                original_rename = Path.rename
                observations = []

                def cancel_at_publish(path, destination):
                    if path == staging and Path(destination) == live:
                        previous = live.parent / f".{live.name}.previous"
                        observations.append({
                            item.relative_to(previous): item.read_bytes()
                            for item in previous.rglob("*") if item.is_file()
                        })
                        raise signal
                    return original_rename(path, destination)

                with patch.object(Path, "rename", cancel_at_publish):
                    with self.assertRaises(type(signal)) as caught:
                        replace_tree(staging, live)

                self.assertIs(caught.exception, signal)
                self.assertEqual(observations, [old])
                self.assertTrue(live.is_dir(), "Cancellation left the live path absent")
                self.assertEqual(
                    {item.relative_to(live): item.read_bytes()
                     for item in live.rglob("*") if item.is_file()}, old)
                replace_tree(staging, live)
                self.assertEqual((live / "sentinel").read_bytes(), b"new publication")

    def _assert_process_owner_releases_publication(self, end_owner):
        """C07 pauses a real owned publisher at the filesystem rename boundary."""
        import time

        live = self.temp / "process-live"
        staging = self.temp / "owner-staging"
        competing = self.temp / "competing-staging"
        live.mkdir()
        (live / "sentinel").write_bytes(b"previous publication")
        for path in (staging, competing):
            path.mkdir()
            (path / "sentinel").write_bytes(b"next publication")
        ready, stop = self.temp / "ready", self.temp / "stop"
        child_code = r"""
import sys
import time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
from scripts.daodan.render import replace_tree
live, staging, ready, stop = map(Path, sys.argv[2:])
original_rename = Path.rename
def pause_owned_rename(path, destination):
    if path == live:
        ready.write_text("ownership acquired", encoding="utf-8")
        deadline = time.monotonic() + 10
        while not stop.exists():
            if time.monotonic() >= deadline:
                raise RuntimeError("Owned child stop deadline expired")
            time.sleep(0.01)
        raise KeyboardInterrupt("owned cancellation")
    return original_rename(path, destination)
try:
    with patch.object(Path, "rename", pause_owned_rename):
        replace_tree(staging, live)
except KeyboardInterrupt:
    print("owned cancellation propagated", flush=True)
"""
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", child_code, str(REPO_ROOT), str(live),
             str(staging), str(ready), str(stop)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists(), "Child did not reach publication boundary")
            self.assertIsNone(child.poll())

            with self.assertRaises(RenderError):
                replace_tree(competing, live)

            self.assertEqual((live / "sentinel").read_bytes(), b"previous publication")
            self.assertEqual((competing / "sentinel").read_bytes(), b"next publication")
            if end_owner == "cancel":
                stop.write_text("cancel", encoding="utf-8")
            else:
                child.kill()
            stdout, stderr = child.communicate(timeout=3)
            if end_owner == "cancel":
                self.assertEqual(child.returncode, 0, stderr)
                self.assertIn("owned cancellation propagated", stdout)
            else:
                self.assertNotEqual(child.returncode, 0)
            self.assertEqual((live / "sentinel").read_bytes(), b"previous publication")

            replace_tree(competing, live)

            self.assertEqual((live / "sentinel").read_bytes(), b"next publication")
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=3)

    def test_normal_child_cancellation_releases_publication_ownership(self):
        self._assert_process_owner_releases_publication("cancel")

    def test_child_death_releases_publication_ownership_for_a_later_publish(self):
        self._assert_process_owner_releases_publication("death")


    def test_child_death_after_live_move_preserves_old_bytes_across_failed_recovery(self):
        """A later failed publication must keep the last complete tree recoverable."""
        import time

        live = self.temp / "recovery-live"
        owner_staging = self.temp / "interrupted-staging"
        next_staging = self.temp / "recovery-staging"
        previous = self.temp / ".recovery-live.previous"
        old = {Path("sentinel.bin"): b"complete old publication\x00\xff\r\n",
               Path("nested/guide.txt"): b"complete old nested bytes\n"}
        live.mkdir()
        (live / "nested").mkdir()
        for path, content in old.items():
            (live / path).write_bytes(content)
        for staging in (owner_staging, next_staging):
            staging.mkdir()
            (staging / "sentinel.bin").write_bytes(b"complete replacement\x00\xfe")
        ready, stop = self.temp / "recovery-ready", self.temp / "recovery-stop"
        child_code = r"""
import sys
import time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
from scripts.daodan.render import replace_tree
live, staging, ready, stop = map(Path, sys.argv[2:])
original_rename = Path.rename
def pause_after_live_move(path, destination):
    if path == staging and Path(destination) == live:
        ready.write_text("live moved; replacement not published", encoding="utf-8")
        deadline = time.monotonic() + 20
        while not stop.exists():
            if time.monotonic() >= deadline:
                raise RuntimeError("Owned recovery child stop deadline expired")
            time.sleep(0.01)
        raise KeyboardInterrupt("owned recovery cancellation")
    return original_rename(path, destination)
try:
    with patch.object(Path, "rename", pause_after_live_move):
        replace_tree(staging, live)
except KeyboardInterrupt:
    pass
"""
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", child_code, str(REPO_ROOT), str(live),
             str(owner_staging), str(ready), str(stop)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 10
            while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists(), "Child did not reach the post-move boundary")
            self.assertIsNone(child.poll())
            self.assertFalse(live.exists(), "Child must actually have moved the live tree")
            self.assertEqual(
                {item.relative_to(previous): item.read_bytes()
                 for item in previous.rglob("*") if item.is_file()}, old)

            child.kill()
            _, stderr = child.communicate(timeout=3)
            self.assertNotEqual(child.returncode, 0, stderr)
            original_rename = Path.rename
            old_retained_at_failure = []

            def fail_next_publication(path, destination):
                if path == next_staging and Path(destination) == live:
                    snapshots = [
                        {item.relative_to(root): item.read_bytes()
                         for item in root.rglob("*") if item.is_file()}
                        for root in (live, previous) if root.is_dir()
                    ]
                    old_retained_at_failure.append(old in snapshots)
                    raise OSError("owned recovery replacement failure")
                return original_rename(path, destination)

            with patch.object(Path, "rename", fail_next_publication), \
                    patch("scripts.daodan.render.time.sleep"):
                with self.assertRaises(RenderError):
                    replace_tree(next_staging, live)
            recoverable_after_failure = [
                {item.relative_to(root): item.read_bytes()
                 for item in root.rglob("*") if item.is_file()}
                for root in (live, previous) if root.is_dir()
            ]
            replace_tree(next_staging, live)

            self.assertTrue(old_retained_at_failure, "The recovery fault was not exercised")
            self.assertTrue(
                all(old_retained_at_failure),
                "Recovery discarded complete old bytes before replacement succeeded",
            )
            self.assertIn(old, recoverable_after_failure,
                          "Failed recovery lost the last complete publication")
            self.assertEqual(
                {item.relative_to(live): item.read_bytes()
                 for item in live.rglob("*") if item.is_file()},
                {Path("sentinel.bin"): b"complete replacement\x00\xfe"},
            )
        finally:
            if child.poll() is None:
                stop.write_text("cancel", encoding="utf-8")
                try:
                    child.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
            child.communicate(timeout=3)

    @unittest.skipUnless(os.name == "nt", "Windows ACL regression")
    def test_published_tree_inherits_the_store_acl(self):
        store = Path(tempfile.gettempdir()) / f"daodan-render-{uuid.uuid4().hex}"
        store.mkdir()
        self.addCleanup(shutil.rmtree, store, True)
        live = store / "example"

        publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, "codex"), live)

        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& { param($target) (Get-Item -LiteralPath $target).GetAccessControl().AreAccessRulesProtected }",
                str(live),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            (completed.returncode, completed.stdout.strip()),
            (0, "False"),
            completed.stderr.strip(),
        )


if __name__ == "__main__":
    unittest.main()
