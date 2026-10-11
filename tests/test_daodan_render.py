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
        live = self.temp / "live"
        self.compile_fixture("claude")
        publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, "claude"), live)
        self.assertFalse((self.temp / ".previous").exists())

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
