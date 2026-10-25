"""The Office entries ship with the `daodan` entry plugin, not with `office`.

Since the Office integration into the Daodan marketplace, `office` ships the
methods, the roles and the contracts, and its seven entries are `daodan`
workflows: every command of this marketplace lives in the `daodan` plugin, and
the other plugins keep skills, roles and contracts (see
`docs/superpowers/specs/2026-10-19-command-set-design.md`). These helpers render
the entries each Office contract test reads, so the assertions stay on the
artifact a host installs, and on the plugin that owns it.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402

DAODAN = REPO_ROOT / "plugins/daodan"
ADAPTERS = REPO_ROOT / "adapters"

#: The seven entries the Office methods are driven by, as `daodan` workflows.
ENTRY_NAMES = ("start", "presentation", "document", "workbook", "verify", "fix", "theme")

_LAYOUT = {
    "claude": "commands/{name}.md",
    "copilot": "prompts/{name}.prompt.md",
    "codex": "skills/{name}-workflow/SKILL.md",
    "pi": "prompts/daodan-{name}.md",
    "opencode": "commands/{name}.md",
}


def entry_plugin(names: Iterable[str] = ENTRY_NAMES):
    """The `daodan` plugin reduced to the named Office entries."""
    plugin = load_plugin(DAODAN)
    workflows = tuple(
        next(item for item in plugin.workflows if item.name == name) for name in names
    )
    return replace(plugin, workflows=workflows)


def render_entries(root, names: Iterable[str] = ENTRY_NAMES) -> Mapping[str, Path]:
    """Render one `daodan` package per host carrying only those entries."""
    plugin = entry_plugin(names)
    packages = {}
    for host in HOSTS:
        package = Path(root) / host / "daodan"
        render_plugin(plugin, load_adapter(ADAPTERS, host), package, adapters_root=ADAPTERS)
        packages[host] = package
    return packages


def entry_path(package, host: str, name: str) -> Path:
    """Where the host's package carries the entry a coordinator agent holds."""
    coordinator = Path(package) / "agents" / f"{name}-coordinator.agent.md"
    if host == "copilot" and coordinator.is_file():
        return coordinator
    return Path(package) / _LAYOUT[host].format(name=name)
