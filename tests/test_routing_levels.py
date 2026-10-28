"""Pins the S-1 routing level table against the real kernels.

`docs/specs/2026-10-28-chat-entry-routing-design.md` (SHA-256 42b8070f...eb58)
sets three levels: workflows (plus keywords where listed), keywords only, and
nothing. `docs/specs/2026-10-28-chat-entry-routing-plan.md` section 3 names the
exact keyword targets and section 4's wave 7 (T8a to T8h) groups the kernel
declarations. No real kernel declares `[routing]` until that wave, so every
group test here is expected to fail, naming the plugins that still declare
none; `test_internal_providers_do_not_route` is green now and stays green
after, since those plugins never gain a `[routing]` table.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin  # noqa: E402

HOOK_CAPABILITY = "hooks.lifecycle"

# Workflows, plus keywords where listed (S-1 table; plan section 3).
WORKFLOW_LEVEL = {
    "daodan": frozenset(),
    "research": frozenset({"science-based-approach"}),
    "digital-marketing": frozenset(),
    "trading-broker-integration": frozenset({"ibkr", "mt5"}),
    "frontend-review": frozenset(),
    "pwa-expert": frozenset(),
    "rag-development": frozenset(),
    "stripe": frozenset(),
    "opentelemetry": frozenset(),
    "ai-tooling": frozenset(),
    "system-utils": frozenset(),
    "learning": frozenset(),
    "grabber-development": frozenset(),
    "marketplace-ops": frozenset(),
}

# Keywords only (S-1 table; plan section 3).
KEYWORD_LEVEL = {
    "react-development": frozenset({"react-best-practices"}),
    "python-development": frozenset({
        "python-engineer",
        "pytest-patterns",
        "pydantic-v2",
        "uv-package-manager",
        "async-python-patterns",
        "python-packaging",
        "python-performance-optimization",
    }),
    "typescript-development": frozenset({
        "typescript-write", "mastering-typescript", "knip", "type-safety-rules",
    }),
    "kotlin-development": frozenset({"kotlin-specialist"}),
    "docker": frozenset({"multi-stage-dockerfile"}),
    "tauri-development": frozenset({"tauri", "rust-engineer"}),
    "messaging": frozenset({"rabbitmq-production"}),
    "business": frozenset({"saas-business-plan", "legal-advisor", "privacy-doc-generator"}),
    "app-analyzer": frozenset({"app-analyzer"}),
    "dependency-audit": frozenset({"dependency-audit"}),
    "project-delivery": frozenset({"adr-method", "frd-method"}),
    "libgdx-development": frozenset({"libgdx-development"}),
    "obsidian-development": frozenset({"obsidian-plugin-development"}),
    "xterm": frozenset({"xtermjs-skill"}),
    "browser-extensions": frozenset({"firefox-extension-dev"}),
    "csp": frozenset({"or-tools-expert"}),
}

EXPECTED = {
    **{name: (True, targets) for name, targets in WORKFLOW_LEVEL.items()},
    **{name: (False, targets) for name, targets in KEYWORD_LEVEL.items()},
}

# Wave 7's T8a to T8h groups (plan section 4).
GROUPS = {
    "a": ("daodan", "research", "digital-marketing", "trading-broker-integration"),
    "b": ("frontend-review", "pwa-expert", "rag-development", "stripe"),
    "c": ("opentelemetry", "ai-tooling", "system-utils", "learning"),
    "d": ("grabber-development", "marketplace-ops", "react-development", "python-development"),
    "e": ("typescript-development", "kotlin-development", "docker", "tauri-development"),
    "f": ("messaging", "business", "app-analyzer", "dependency-audit"),
    "g": ("project-delivery", "libgdx-development", "obsidian-development", "xterm"),
    "h": ("browser-extensions", "csp"),
}


def _load(name):
    return load_plugin(REPO_ROOT / "plugins" / name)


class RoutingLevels(unittest.TestCase):
    """Pins which plugins route and how; red until wave 7 declares `[routing]`."""

    def _check_group(self, names):
        plugins = {name: _load(name) for name in names}
        missing = [name for name, plugin in plugins.items() if plugin.routing is None]
        self.assertFalse(missing, f"{', '.join(missing)} declares no [routing]")
        for name, plugin in plugins.items():
            workflows, targets = EXPECTED[name]
            with self.subTest(plugin=name):
                self.assertEqual(plugin.routing.workflows, workflows)
                self.assertEqual(
                    frozenset(keyword.target for keyword in plugin.routing.keywords), targets,
                )
                self.assertIn(HOOK_CAPABILITY, plugin.capabilities.optional)

    def test_group_a(self):
        self._check_group(GROUPS["a"])

    def test_group_b(self):
        self._check_group(GROUPS["b"])

    def test_group_c(self):
        self._check_group(GROUPS["c"])

    def test_group_d(self):
        self._check_group(GROUPS["d"])

    def test_group_e(self):
        self._check_group(GROUPS["e"])

    def test_group_f(self):
        self._check_group(GROUPS["f"])

    def test_group_g(self):
        self._check_group(GROUPS["g"])

    def test_group_h(self):
        self._check_group(GROUPS["h"])

    def test_internal_providers_do_not_route(self):
        kernels = sorted((REPO_ROOT / "plugins").glob("*/plugin.toml"))
        for kernel in kernels:
            name = kernel.parent.name
            if name in EXPECTED:
                continue
            with self.subTest(plugin=name):
                self.assertIsNone(load_plugin(kernel.parent).routing)


if __name__ == "__main__":
    unittest.main()
