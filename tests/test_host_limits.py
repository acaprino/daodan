"""Every rendered skill must fit the ceilings its host enforces.

A host can reject a package the compiler considers correct. Pi caps a skill
description at 1024 characters and reports anything longer as a skill conflict
when the agent starts, which is a runtime failure no gate here could see: the
build passed, `--check` passed, every linter passed, and `ai-tooling`'s
`prompt-engineering` description still shipped at 1030 characters until a user
hit it.

The ceilings are host facts, so they are declared in `adapters/<host>/layout.toml`
under `[limits]` rather than here. This module renders every kernel for every
host that declares one and measures the files that host registers as skills,
which is why it reads the rendered artifact instead of the kernel: a role is a
skill on Pi, and its description reaches the package flattened onto one line by
the compiler rather than as the kernel wrote it.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from scripts.daodan_build import discover_plugins  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"

BLOCK_SCALARS = {">", "|", ">-", "|-"}


def folded_description(text: str) -> str | None:
    """Return a SKILL.md description the way the host's YAML parser sees it.

    Only what the frontmatter of a generated skill actually uses is handled: a
    plain scalar on one line, or a folded or literal block. A folded block joins
    its lines with spaces, and clip chomping keeps one trailing newline, which
    is the character that put the measured 1030 one over Pi's own count.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    lines = text[4:end].split("\n")
    for index, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        scalar = line[len("description:") :].strip()
        if scalar not in BLOCK_SCALARS:
            return scalar.strip("'\"")
        block = []
        for continuation in lines[index + 1 :]:
            if continuation.strip() and not continuation.startswith("  "):
                break
            block.append(continuation.strip())
        while block and not block[-1]:
            block.pop()
        joined = (" " if scalar.startswith(">") else "\n").join(part for part in block if part)
        return joined if scalar.endswith("-") else joined + "\n"
    return None


class HostLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = Path(tempfile.mkdtemp())
        cls.plugins = discover_plugins(REPO_ROOT)
        cls.hosts = {}
        for host in HOSTS:
            adapter = load_adapter(ADAPTERS, host)
            if not adapter.limits:
                continue
            cls.hosts[host] = adapter
            for plugin in cls.plugins:
                staging = cls.temp / host / plugin.name
                render_plugin(plugin, adapter, staging, adapters_root=ADAPTERS)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp, ignore_errors=True)

    def test_a_host_declares_a_ceiling(self):
        """Pi's ceiling is what this module exists for, so losing it is a failure."""
        self.assertIn("pi", self.hosts)
        self.assertEqual(self.hosts["pi"].limits["skill_description"], 1024)

    def test_every_plugin_renders_at_least_one_skill(self):
        """A measurement over an empty set passes for the wrong reason."""
        for host in self.hosts:
            measured = list((self.temp / host).rglob("skills/*/SKILL.md"))
            self.assertGreater(len(measured), 100, host)

    def test_skill_descriptions_fit_the_host_ceiling(self):
        for host, adapter in self.hosts.items():
            limit = adapter.limits.get("skill_description")
            if limit is None:
                continue
            for package in sorted((self.temp / host).iterdir()):
                for skill in sorted(package.rglob("skills/*/SKILL.md")):
                    description = folded_description(skill.read_text(encoding="utf-8"))
                    self.assertIsNotNone(
                        description, f"{host}: {skill.relative_to(self.temp / host)} has no description"
                    )
                    self.assertLessEqual(
                        len(description),
                        limit,
                        f"{host}: {skill.relative_to(self.temp / host)} description is "
                        f"{len(description)} characters, over the {limit} this host accepts. "
                        f"Shorten it in the kernel under plugins/{package.name}/.",
                    )


if __name__ == "__main__":
    unittest.main()
