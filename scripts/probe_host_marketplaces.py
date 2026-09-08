"""Validate the disposable native-host protocol probe fixtures.

The fixtures under ``tests/host-probes/`` are three throwaway single-plugin
marketplaces, one per host, used to establish what each native harness actually
supports before any adapter binding encodes an assumption. This module checks
their structure; the behavioural evidence table is filled in by hand after
running the probes in real host sessions (see ``tests/host-probes/README.md``).

Standard library only. Run directly for a report:

    python scripts/probe_host_marketplaces.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_ROOT = REPO_ROOT / "tests" / "host-probes"

HOSTS = ("claude", "copilot", "codex", "pi")

MARKETPLACE_PATH = {
    "claude": Path(".claude-plugin/marketplace.json"),
    "copilot": Path(".github/plugin/marketplace.json"),
    "codex": Path(".agents/plugins/marketplace.json"),
}

PLUGIN_MANIFEST_PATH = {
    "claude": Path(".claude-plugin/plugin.json"),
    "copilot": Path("plugin.json"),
    "codex": Path(".codex-plugin/plugin.json"),
}

REQUIRED_FILES = {
    "claude": (
        Path("plugins/probe/skills/probe/SKILL.md"),
        Path("plugins/probe/agents/probe-worker.md"),
        Path("plugins/probe/commands/probe-team.md"),
    ),
    "copilot": (
        Path("plugins/probe/skills/probe/SKILL.md"),
        Path("plugins/probe/agents/probe-coordinator.agent.md"),
        Path("plugins/probe/agents/probe-worker.agent.md"),
    ),
    "codex": (
        Path("plugins/probe/skills/probe/SKILL.md"),
        Path("plugins/probe/hooks/hooks.json"),
        Path("plugins/probe/.codex/agents/probe.toml"),
    ),
    "pi": (
        Path("plugins/probe/skills/probe/SKILL.md"),
        Path("plugins/probe/skills/probe-worker/SKILL.md"),
        Path("plugins/probe/prompts/daodan-probe-team.md"),
    ),
}

#: Pi installs a package rather than registering a marketplace, so its fixture is
#: a package manifest at the fixture root and there is no per-plugin manifest at
#: all. Everything else about the probe is the same.
PI_MANIFEST = Path("package.json")

PROBE_NAME = "daodan-probe"
PROBE_VERSION = "0.0.1"
PROBE_SOURCE = "./plugins/probe"
SINGLE_WORKER_CONTRACT = "Return exactly DAODAN_PROBE_OK."


def validate_pi_fixture(root: Path) -> list[str]:
    """Structural check for the package-shaped fixture.

    Pi registers what its globs reach, so the check that matters is that they
    reach the probe: a manifest naming the right package is not evidence that
    anything in it is loadable.
    """
    errors: list[str] = []
    manifest = root / PI_MANIFEST
    if not manifest.is_file():
        return [f"pi: missing {PI_MANIFEST.as_posix()}"]
    try:
        declared = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"pi: {PI_MANIFEST.as_posix()} is not valid JSON: {error}"]

    if declared.get("name") != PROBE_NAME:
        errors.append(f"pi: package name is {declared.get('name')!r}, expected {PROBE_NAME!r}")
    if declared.get("version") != PROBE_VERSION:
        errors.append(f"pi: package version is {declared.get('version')!r}")
    if "pi-package" not in declared.get("keywords", []):
        errors.append("pi: package is not tagged with the pi-package keyword")

    globs = declared.get("pi", {})
    for kind in ("skills", "prompts"):
        patterns = globs.get(kind, [])
        if not patterns:
            errors.append(f"pi: manifest declares no {kind} glob")
        reached = [
            path for pattern in patterns for path in root.glob(pattern.lstrip("./"))
        ]
        if not reached:
            errors.append(f"pi: the {kind} glob reaches nothing on disk")

    for relative in REQUIRED_FILES["pi"]:
        if not (root / relative).is_file():
            errors.append(f"pi: missing {relative.as_posix()}")

    worker = root / "plugins/probe/skills/probe-worker/SKILL.md"
    if worker.is_file() and "disable-model-invocation: true" not in worker.read_text(
        encoding="utf-8"
    ):
        errors.append("pi: the worker role skill is not hidden from the system prompt")
    return errors


def validate_fixture(root: Path, host: str) -> list[str]:
    """Return one message per structural defect in a probe fixture."""
    if host == "pi":
        return validate_pi_fixture(root)
    if host not in MARKETPLACE_PATH:
        return [f"{host}: unknown host"]

    errors: list[str] = []
    marketplace = root / MARKETPLACE_PATH[host]
    if not marketplace.is_file():
        return [f"{host}: missing {MARKETPLACE_PATH[host].as_posix()}"]

    try:
        catalog = json.loads(marketplace.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"{host}: {MARKETPLACE_PATH[host].as_posix()} is not valid JSON: {error}"]

    plugins = catalog.get("plugins", [])
    if len(plugins) != 1:
        errors.append(f"{host}: expected one probe plugin")
    else:
        entry = plugins[0]
        if entry.get("name") != PROBE_NAME:
            errors.append(f"{host}: plugin name is {entry.get('name')!r}, expected {PROBE_NAME!r}")
        if entry.get("version") != PROBE_VERSION:
            errors.append(f"{host}: plugin version is {entry.get('version')!r}, expected {PROBE_VERSION!r}")
        source = entry.get("source")
        if source != PROBE_SOURCE:
            errors.append(f"{host}: source is {source!r}, expected the repository-relative {PROBE_SOURCE!r}")

    manifest = root / "plugins/probe" / PLUGIN_MANIFEST_PATH[host]
    if not manifest.is_file():
        errors.append(f"{host}: missing plugins/probe/{PLUGIN_MANIFEST_PATH[host].as_posix()}")
    else:
        try:
            declared = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{host}: plugin manifest is not valid JSON: {error}")
        else:
            if declared.get("name") != PROBE_NAME:
                errors.append(f"{host}: plugin manifest name is {declared.get('name')!r}")
            if declared.get("version") != PROBE_VERSION:
                errors.append(f"{host}: plugin manifest version is {declared.get('version')!r}")

    for relative in REQUIRED_FILES[host]:
        if not (root / relative).is_file():
            errors.append(f"{host}: missing {relative.as_posix()}")

    skill = root / "plugins/probe/skills/probe/SKILL.md"
    if skill.is_file() and SINGLE_WORKER_CONTRACT not in skill.read_text(encoding="utf-8"):
        errors.append(f"{host}: probe skill does not state the single-worker output contract")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROBE_ROOT, help="probe fixture root")
    arguments = parser.parse_args(argv)

    failures = 0
    for host in HOSTS:
        errors = validate_fixture(arguments.root / host, host)
        failures += len(errors)
        if errors:
            for message in errors:
                print(message)
        else:
            print(f"{host}: ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
