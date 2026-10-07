"""The Daodan compiler entry point.

    python scripts/daodan_build.py            # publish every host
    python scripts/daodan_build.py --check    # fail on drift, write nothing

Exit codes: 0 clean, 1 drift or validation failure, 2 invocation error.

Publication always builds every host together: a marketplace that
ships one host ahead of the others is exactly the drift this compiler exists to
prevent. Selecting a subset is a development affordance, and only under
``--check``.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support  # noqa: E402
from scripts.daodan.catalogs import (  # noqa: E402
    assert_cross_host_identity,
    catalog_document,
    merge_into_legacy,
    render_catalog,
)
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError, PluginSpec  # noqa: E402
from scripts.daodan.overrides import load_overrides, validate_override  # noqa: E402
from scripts.daodan.render import RenderError, render_plugin, replace_tree, tree_digest  # noqa: E402
from scripts.daodan.provenance import KEYS, PROVENANCE_FILENAME  # noqa: E402
from scripts.daodan.report import BuildReport  # noqa: E402
from scripts.daodan.trust import scan_trust  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY, ValidationIssue, validate_plugins  # noqa: E402

LEGACY_CLAUDE_CATALOG = Path(".claude-plugin/marketplace.json")


def discover_plugins(root: Path) -> list[PluginSpec]:
    """Load every content kernel under ``plugins/``, in name order."""
    plugins_root = Path(root) / "plugins"
    if not plugins_root.is_dir():
        return []
    kernels = sorted(plugins_root.glob("*/plugin.toml"), key=lambda item: item.as_posix())
    return [load_plugin(kernel.parent) for kernel in kernels]


def marketplace_version(root: Path) -> str:
    """The single marketplace version every host catalog carries.

    It stays where it has always lived, `metadata.version` in the Claude
    catalog, so the existing bump workflow keeps working through the migration.
    """
    catalog = Path(root) / LEGACY_CLAUDE_CATALOG
    if catalog.is_file():
        document = json.loads(catalog.read_text(encoding="utf-8"))
        version = document.get("metadata", {}).get("version")
        if isinstance(version, str):
            return version
    return "0.0.0"


def _overrides_for(root: Path, host: str, plugin: PluginSpec):
    directory = Path(root) / "adapters" / host / "overrides" / plugin.name
    if not directory.is_dir():
        return ()
    return load_overrides(directory)


def build_repository(root: Path, hosts: tuple[str, ...], check: bool) -> BuildReport:
    """Validate every kernel and render, or verify, every host package."""
    root = Path(root)
    issues: list[ValidationIssue] = []
    drift: list[Path] = []
    support = []

    try:
        plugins = discover_plugins(root)
    except ModelError as error:
        return BuildReport(issues=(ValidationIssue("model-error", error.path, error.message),))

    issues.extend(validate_plugins(plugins, CAPABILITY_REGISTRY))
    plugin_registry = {plugin.name: plugin for plugin in plugins}
    for scanned in ("plugins", "adapters"):
        directory = root / scanned
        if directory.is_dir():
            issues.extend(scan_trust(directory, frozenset()))

    catalogs = {}
    version = marketplace_version(root)
    prepared = []
    retired = []
    for host in hosts:
        adapter = load_adapter(root / "adapters", host)
        stale, ownership_issues = _retired_packages(root, adapter, set(plugin_registry))
        retired.extend(stale)
        issues.extend(ownership_issues)
        if check:
            drift.extend(stale)
        packages = {
            plugin.name: root / adapter.layout["root"] / "plugins" / plugin.name
            for plugin in plugins
        }
        catalogs[host] = catalog_document(host, plugins, version, packages)
        for plugin in plugins:
            overrides = _overrides_for(root, host, plugin)
            declared = frozenset(plugin.capabilities.required) | frozenset(
                plugin.capabilities.optional
            )
            for override in overrides:
                issues.extend(validate_override(override, declared, repository_root=root))

            report = resolve_support(plugin, adapter)
            support.append(report)
            if report.state == "unsupported":
                issues.append(
                    ValidationIssue(
                        "unsupported-required-plugin",
                        plugin.root,
                        f"{host}: {', '.join(report.missing_capabilities) or 'no coordination strategy'}",
                    )
                )
                continue

            live = root / adapter.layout["root"] / "plugins" / plugin.name
            if check:
                if _package_drifted(plugin, adapter, live, overrides, root, plugin_registry):
                    drift.append(live)
            else:
                prepared.append((plugin, adapter, live, overrides))

    if len(catalogs) == len(HOSTS):
        assert_cross_host_identity(catalogs)

    if issues:
        return BuildReport(issues=tuple(issues), drift=tuple(drift), support=tuple(support))

    # Render every host before changing any live package or retiring any output.
    with tempfile.TemporaryDirectory(prefix="daodan-build-") as holder:
        staging = Path(holder)
        staged_packages = {}
        try:
            for plugin, adapter, live, overrides in prepared:
                target = staging / adapter.host / plugin.name
                render_plugin(plugin, adapter, target, overrides, root / "adapters", plugin_registry)
                staged_packages[(adapter.host, plugin.name)] = target
        except RenderError as error:
            return BuildReport(issues=(ValidationIssue("render-error", root, str(error)),),
                               support=tuple(support))

        files = []
        for host in hosts:
            adapter = load_adapter(root / "adapters", host)
            packages = {plugin.name: staged_packages.get((host, plugin.name),
                        root / adapter.layout["root"] / "plugins" / plugin.name) for plugin in plugins}
            catalog_path = root / adapter.layout["marketplace"]
            removed = {path.name for path in retired if path.parent == root / adapter.layout["root"] / "plugins"}
            rendered = _render_host_catalog(root, adapter, host, plugins, version, catalog_path,
                                            packages, removed)
            files.append((catalog_path, rendered))
            files.extend(_package_files(root, adapter))
        if check:
            for live_file, content in files:
                if not live_file.is_file() or live_file.read_bytes() != content:
                    drift.append(live_file)
        else:
            for plugin, adapter, live, _ in prepared:
                live.parent.mkdir(parents=True, exist_ok=True)
                sibling = Path(tempfile.mkdtemp(prefix=f".{live.name}.", suffix=".staging", dir=live.parent))
                try:
                    shutil.copytree(staged_packages[(adapter.host, plugin.name)], sibling, dirs_exist_ok=True)
                    replace_tree(sibling, live)
                finally:
                    shutil.rmtree(sibling, ignore_errors=True)
            for live_file, content in files:
                live_file.parent.mkdir(parents=True, exist_ok=True)
                live_file.write_bytes(content)
            for obsolete in retired:
                # Ownership and every resolved boundary were checked before rendering.
                shutil.rmtree(obsolete)

    return BuildReport(issues=tuple(issues), drift=tuple(drift), support=tuple(support))


def _retired_packages(root, adapter, active):
    """Recognize retired generated trees by their own validated provenance.

    A directory name or an old catalog entry alone never authorizes deletion.
    Unknown trees and links stop publication. No path outside this adapter's
    generated plugin root can enter the retirement list.
    """
    root = Path(root).absolute()
    generated = root / adapter.layout["root"] / "plugins"
    expected = root / "exports" / adapter.host / "plugins"
    issues = []
    retired = []
    if generated != expected or not generated.resolve().is_relative_to(root.resolve() / "exports"):
        return [], [ValidationIssue("unsafe-generated-output", generated, "Generated plugin root escaped exports")]
    for ancestor in (root / "exports", expected.parent, expected):
        if ancestor.is_symlink() or getattr(ancestor, "is_junction", lambda: False)():
            return [], [ValidationIssue("unsafe-generated-output", ancestor, "Generated output root is a link")]
    if not generated.exists():
        return [], []
    for directory in sorted(generated.iterdir()):
        linked = directory.is_symlink() or getattr(directory, "is_junction", lambda: False)()
        if linked or not directory.resolve().is_relative_to(generated.resolve()):
            issues.append(ValidationIssue("unsafe-generated-output", directory, "Generated package is a link or escaped its root"))
            continue
        if not directory.is_dir() or directory.name in active:
            continue
        provenance = directory / PROVENANCE_FILENAME
        try:
            if provenance.is_symlink() or getattr(provenance, "is_junction", lambda: False)():
                raise ValueError("Linked provenance")
            document = json.loads(provenance.read_text(encoding="utf-8"))
            valid = (tuple(sorted(document)) == KEYS and document["host"] == adapter.host
                     and document["plugin"] == directory.name
                     and isinstance(document["version"], str)
                     and isinstance(document["adapterVersion"], str)
                     and isinstance(document["harnessStrategies"], dict)
                     and isinstance(document["overrides"], list)
                     and isinstance(document["coreDigest"], str)
                     and re.fullmatch(r"sha256:[0-9a-f]{64}", document["coreDigest"]) is not None)
            if not valid:
                raise ValueError("Provenance does not identify this generated package")
            if any(path.is_symlink() or getattr(path, "is_junction", lambda: False)()
                   for path in directory.rglob("*")):
                raise ValueError("Package contains links")
        except (OSError, ValueError, TypeError, KeyError) as error:
            issues.append(ValidationIssue("unsafe-generated-output", directory,
                                          f"Cannot retire a tree without matching provenance: {error}"))
            continue
        retired.append(directory)
    return retired, issues


def _package_files(root: Path, adapter) -> list[tuple[Path, bytes]]:
    """Files a host package carries once at its root, copied from the adapter.

    OpenCode's loader is the case: fixed code shipped beside the manifest it
    reads, so a rebuild must reproduce it byte for byte like any other output.
    Text is normalized to LF, as every rendered file is.
    """
    names = [item.strip() for item in adapter.layout.get("package_files", "").split(",") if item.strip()]
    files = []
    for name in names:
        source = root / "adapters" / adapter.host / "templates" / name
        raw = source.read_bytes().replace(b"\r\n", b"\n")
        files.append((root / adapter.layout["root"] / name, raw))
    return files


def _render_host_catalog(root, adapter, host, plugins, version, catalog_path: Path,
                         packages=None, retired=frozenset()) -> bytes:
    """Serialize one host catalog, folding into a legacy one while migration runs.

    Until every plugin is a neutral kernel, the live Claude catalog still carries
    hand-written entries for the plugins that have not moved yet. Overwriting it
    with the compiled catalog would uninstall them, so compiled entries are
    merged into it instead and the generated catalog is written whole only once
    nothing legacy is left.
    """
    packages = packages if packages is not None else {
        plugin.name: root / adapter.layout["root"] / "plugins" / plugin.name
        for plugin in plugins
    }
    compiled = {plugin.name for plugin in plugins}
    if catalog_path.is_file():
        existing = json.loads(catalog_path.read_text(encoding="utf-8"))
        existing["plugins"] = [entry for entry in existing.get("plugins", []) if entry["name"] not in retired]
        legacy = [
            entry for entry in existing.get("plugins", []) if entry["name"] not in compiled
        ]
        if legacy:
            document = merge_into_legacy(existing, plugins, host, packages)
            return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return render_catalog(host, plugins, version, packages)


def _package_drifted(plugin, adapter, live: Path, overrides, root: Path, plugin_registry=None) -> bool:
    if not live.is_dir():
        return True
    holder = Path(tempfile.mkdtemp())
    try:
        staging = holder / live.name
        try:
            render_plugin(plugin, adapter, staging, overrides, root / "adapters", plugin_registry)
        except RenderError:
            return True
        return tree_digest(staging) != tree_digest(live)
    finally:
        shutil.rmtree(holder, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", action="append", choices=HOSTS)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--support", action="store_true", help="print the per-host support table")
    arguments = parser.parse_args(argv)

    hosts = tuple(arguments.host or HOSTS)
    if not arguments.check and set(hosts) != set(HOSTS):
        parser.print_usage(sys.stderr)
        sys.stderr.write(f"publication always builds {', '.join(HOSTS)} together\n")
        return 2

    report = build_repository(arguments.root, hosts, arguments.check)
    report.write(sys.stdout)
    if arguments.support:
        report.write_support(sys.stdout)
    return 1 if report.has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
