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
import errno
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, AdapterError, load_adapter, resolve_support  # noqa: E402
from scripts.daodan.catalogs import (  # noqa: E402
    CATALOG_DESCRIPTION,
    CATALOG_NAME,
    assert_cross_host_identity,
    catalog_document,
    render_catalog,
)
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError, PluginSpec  # noqa: E402
from scripts.daodan.overrides import OverrideError, load_overrides, validate_override  # noqa: E402
from scripts.daodan.render import _rename_with_retry, RenderError, render_plugin, replace_tree, tree_digest  # noqa: E402
from scripts.daodan.provenance import KEYS, PROVENANCE_FILENAME  # noqa: E402
from scripts.daodan.report import BuildReport  # noqa: E402
from scripts.daodan.trust import scan_trust  # noqa: E402
from scripts.daodan.validate import (  # noqa: E402
    CAPABILITY_REGISTRY, SourcePathError, ValidationIssue, confined_source,
    source_members, validate_plugins,
)

LEGACY_CLAUDE_CATALOG = Path(".claude-plugin/marketplace.json")


def discover_plugins(root: Path) -> list[PluginSpec]:
    """Load every content kernel under ``plugins/``, in name order."""
    plugins_root = Path(root) / "plugins"
    confined_source(Path(root), plugins_root, allow_missing=True)
    if not plugins_root.is_dir():
        return []
    kernels = [path for path in source_members(plugins_root)
               if path.name == "plugin.toml" and path.parent.parent == plugins_root]
    return [load_plugin(kernel.parent) for kernel in kernels]


def marketplace_metadata(root: Path) -> tuple[str, str, str]:
    """Read marketplace name, description and version from the Claude catalog."""
    catalog = Path(root) / LEGACY_CLAUDE_CATALOG
    confined_source(Path(root), catalog, allow_missing=True)
    if catalog.is_file():
        document = json.loads(catalog.read_text(encoding="utf-8"))
        name = document.get("name")
        meta = document.get("metadata", {})
        description = meta.get("description")
        version = meta.get("version")
        return (
            name if isinstance(name, str) and name else CATALOG_NAME,
            description if isinstance(description, str) and description else CATALOG_DESCRIPTION,
            version if isinstance(version, str) else "0.0.0",
        )
    return CATALOG_NAME, CATALOG_DESCRIPTION, "0.0.0"


def marketplace_version(root: Path) -> str:
    """The single marketplace version every host catalog carries.

    It stays where it has always lived, `metadata.version` in the Claude
    catalog, so the existing bump workflow keeps working through the migration.
    """
    return marketplace_metadata(root)[2]


def _overrides_for(root: Path, host: str, plugin: PluginSpec):
    directory = Path(root) / "adapters" / host / "overrides" / plugin.name
    confined_source(Path(root) / "adapters" / host, directory, allow_missing=True)
    if not directory.is_dir():
        return ()
    return load_overrides(directory)


def _override_outcomes(
    plugin: PluginSpec, source: str, registry: dict[str, PluginSpec]
) -> frozenset[str] | None:
    """Bind preservation claims to the workflows affected by a registered target."""
    kind, separator, name = source.partition(":")
    if separator and kind == "workflow":
        for workflow in plugin.workflows:
            if workflow.name == name:
                return frozenset(workflow.contract.outcomes)
    elif separator and kind == "role" and name in plugin.components.roles:
        target = f"{plugin.name}/{name}"
        outcomes = set()
        for consumer in registry.values():
            for workflow in consumer.workflows:
                workers = {
                    reference if "/" in reference else f"{consumer.name}/{reference}"
                    for reference in workflow.worker_references(consumer.components.roles)
                }
                if target in workers:
                    outcomes.update(workflow.contract.outcomes)
        return frozenset(outcomes)
    return None


def build_repository(root: Path, hosts: tuple[str, ...], check: bool) -> BuildReport:
    """Validate every kernel and render, or verify, every host package."""
    try:
        return _build_repository(root, hosts, check)
    except (SourcePathError, AdapterError, OverrideError, RenderError) as error:
        return BuildReport(issues=(ValidationIssue(
            "unsafe-source-path" if isinstance(error, SourcePathError) else "build-input-error",
            getattr(error, "path", Path(root)),
            getattr(error, "message", str(error)),
        ),))


def _build_repository(root: Path, hosts: tuple[str, ...], check: bool) -> BuildReport:
    root = Path(root)
    issues: list[ValidationIssue] = []
    drift: list[Path] = []
    support = []

    # Preflight all source trees before any parser, fingerprint or drift render.
    for scanned in ("plugins", "adapters"):
        directory = root / scanned
        confined_source(root, directory, allow_missing=True)
        if directory.is_dir():
            issues.extend(scan_trust(directory, frozenset()))
    if issues:
        return BuildReport(issues=tuple(issues))

    try:
        plugins = discover_plugins(root)
    except ModelError as error:
        return BuildReport(issues=(ValidationIssue("model-error", error.path, error.message),))

    issues.extend(validate_plugins(plugins, CAPABILITY_REGISTRY))
    if issues:
        return BuildReport(issues=tuple(issues))
    plugin_registry = {plugin.name: plugin for plugin in plugins}

    catalogs = {}
    catalog_name, catalog_description, version = marketplace_metadata(root)
    prepared = []
    retired = []
    host_overrides = {}
    for host in hosts:
        adapter = load_adapter(root / "adapters", host)
        host_overrides[host] = {plugin.name: _overrides_for(root, host, plugin) for plugin in plugins}
        stale, ownership_issues = _retired_packages(root, adapter, set(plugin_registry))
        retired.extend(stale)
        issues.extend(ownership_issues)
        if check:
            drift.extend(stale)
        packages = {
            plugin.name: root / adapter.layout["root"] / "plugins" / plugin.name
            for plugin in plugins
        }
        catalogs[host] = catalog_document(
            host, plugins, version, packages, name=catalog_name, description=catalog_description
        )
        for plugin in plugins:
            overrides = host_overrides[host][plugin.name]
            declared = frozenset(plugin.capabilities.required) | frozenset(
                plugin.capabilities.optional
            )
            for override in overrides:
                outcomes = _override_outcomes(plugin, override.source, plugin_registry)
                if outcomes is None:
                    issues.append(ValidationIssue(
                        "override-unknown-source", override.root / "override.toml", override.source
                    ))
                    continue
                issues.extend(validate_override(
                    override, declared, declared_contracts=outcomes, repository_root=root
                ))

            if issues:
                continue

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
            prepared.append((plugin, adapter, live, overrides))

    if len(catalogs) == len(HOSTS):
        assert_cross_host_identity(catalogs)

    if issues:
        return BuildReport(issues=tuple(issues), drift=tuple(drift), support=tuple(support))

    # Both modes derive catalogs from the same complete rendered candidate.
    # A live package can legitimately lack a newly declared component under
    # --check; reading its metadata would turn ordinary drift into a traceback.
    # Render every host before changing any live package or retiring any output.
    with tempfile.TemporaryDirectory(prefix="daodan-build-") as holder:
        staging = Path(holder)
        staged_packages = {}
        try:
            for plugin, adapter, live, overrides in prepared:
                target = staging / adapter.host / plugin.name
                render_plugin(plugin, adapter, target, overrides, root / "adapters", plugin_registry, host_overrides[adapter.host])
                staged_packages[(adapter.host, plugin.name)] = target
                if check and (not live.is_dir() or tree_digest(target) != tree_digest(live)):
                    drift.append(live)
        except RenderError as error:
            return BuildReport(issues=(ValidationIssue("render-error", root, str(error)),),
                               support=tuple(support))

        files = []
        warnings = []
        for host in hosts:
            adapter = load_adapter(root / "adapters", host)
            packages = {plugin.name: staged_packages[(host, plugin.name)] for plugin in plugins}
            catalog_path = root / adapter.layout["marketplace"]
            rendered = _render_host_catalog(root, adapter, host, plugins, version, catalog_path,
                                            packages,
                                            name=catalog_name, description=catalog_description)
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
                warning = _publish_file(live_file, content)
                if warning:
                    warnings.append(warning)
            for obsolete in retired:
                # Ownership and every resolved boundary were checked before rendering.
                shutil.rmtree(obsolete)

    return BuildReport(issues=tuple(issues), drift=tuple(drift), support=tuple(support),
                       warnings=tuple(warnings))


def _publish_file(destination: Path, content: bytes) -> str | None:
    """Publish one complete file with an owned temporary sibling.

    The atomic replace stays the only path that guarantees a reader never sees a partial
    file. It returns ``None`` when that path succeeded, and a warning naming the file
    when the destination was held open by another process and had to be written in place
    instead, so the report says which publication was not atomic.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp",
                                    dir=destination.parent)
    temporary = Path(name)
    os.close(handle)
    try:
        temporary.write_bytes(content)
        try:
            _rename_with_retry(temporary, destination, replace_existing=True)
        except OSError as error:
            if not _is_sharing_violation(error):
                raise
            _publish_in_place(destination, content)
            return (f"published in place, not atomically: {destination} is held open by "
                    f"another process ({error.strerror or error})")
    except OSError as error:
        raise RenderError(f"could not publish {destination}: {error}") from error
    finally:
        temporary.unlink(missing_ok=True)
    return None


# A rename needs delete sharing on the destination. Windows reports its absence as a
# sharing violation, POSIX as a busy or denied file; anything else (a missing parent, an
# unwritable volume) is a real failure and must not take the in-place path.
SHARING_WINERRORS = frozenset({5, 32, 33})
SHARING_ERRNOS = frozenset(
    value for value in (getattr(errno, name, None) for name in ("EBUSY", "EACCES", "EPERM"))
    if value is not None)


def _is_sharing_violation(error: OSError) -> bool:
    if getattr(error, "winerror", None) in SHARING_WINERRORS:
        return True
    return error.errno in SHARING_ERRNOS


def _read_back(destination: Path) -> bytes:
    return destination.read_bytes()


def _publish_in_place(destination: Path, content: bytes) -> None:
    """Overwrite a file another process holds open, then prove the bytes are complete.

    A host indexer that opens a repository-root manifest without delete sharing makes
    every rename of it fail for as long as the process lives, and such a process is
    supervised: measured on 2026-10-22, Tri-Tech Code's ``tritech-indexd`` respawned
    within seconds of being stopped and re-locked the root, so publication of the root
    manifest was impossible on the very host this repository ships to. Writing in place
    is the only publication left there. It keeps the guarantee that matters, that the
    file on disk is exactly the rendered content, by backing the previous bytes up,
    verifying the result and restoring on any mismatch. What it cannot guarantee is that
    a concurrent reader sees no intermediate state, which is why the caller records a
    warning instead of passing silently.
    """
    backup = None
    if destination.is_file():
        handle, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".previous",
                                        dir=destination.parent)
        os.close(handle)
        backup = Path(name)
        shutil.copyfile(destination, backup)
    try:
        with open(destination, "r+b" if backup is not None else "wb") as handle:
            handle.write(content)
            handle.truncate()
            handle.flush()
            os.fsync(handle.fileno())
        if _read_back(destination) != content:
            raise RenderError(f"in-place publication of {destination} did not verify "
                              "against the rendered bytes")
    except BaseException:
        if backup is not None:
            shutil.copyfile(backup, destination)
        raise
    finally:
        if backup is not None:
            backup.unlink(missing_ok=True)


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
        confined_source(root / "adapters" / adapter.host / "templates", source)
        raw = source.read_bytes().replace(b"\r\n", b"\n")
        files.append((root / adapter.layout["root"] / name, raw))
    return files


def _render_host_catalog(root, adapter, host, plugins, version, catalog_path: Path,
                         packages=None, *,
                         name: str = CATALOG_NAME, description: str = CATALOG_DESCRIPTION) -> bytes:
    """Serialize current kernel and adapter authority, never saved registrations."""
    packages = packages if packages is not None else {
        plugin.name: root / adapter.layout["root"] / "plugins" / plugin.name
        for plugin in plugins
    }
    confined_source(root, catalog_path, allow_missing=True)
    return render_catalog(
        host, plugins, version, packages, layout=adapter.layout, name=name, description=description
    )


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
