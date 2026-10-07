"""Native catalog rendering, one catalog per host.

Every host names the same plugins at the same versions. That identity is the
whole point of a universal marketplace, so a version mismatch is rejected before
serialization rather than shipped and noticed later. The shape may differ: three
hosts take a plugin listing, and Pi takes a package manifest that globs the
rendered tree, because Pi installs a package and has no marketplace to list into.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from .adapter import HOSTS
from .model import PluginSpec

CATALOG_NAME = "daodan"

CATALOG_DESCRIPTION = (
    "Daodan: a coherent AI development harness for project changes, meaningful "
    "tests, durable knowledge and verified evidence, with independent specialists."
)

OWNER = {"name": "Alfio Caprino"}


class CatalogError(ValueError):
    pass


def _source(host: str, name: str) -> object:
    """Return the host-native source reference for one plugin.

    The three hosts with a catalog take a repository-relative path string; Pi
    has no source field at all and reuses this shape as the root of its globs.
    Codex was specified
    as `{"source": "local", "path": ...}`, and that shape is silently ignored:
    the marketplace registers, and then every plugin in it is "not found".
    Measured against codex-cli 0.149.1, which lists a plugin only when `source`
    is the path itself.
    """
    return f"./exports/{host}/plugins/{name}"


MCP_MANIFEST = ".mcp.json"


def package_components(root: Path) -> dict[str, object]:
    """Declared component paths for a rendered Claude package.

    Includes the `mcpServers` pointer when the package carries a rendered
    `.mcp.json`, so the catalog names the server file the way the package
    ships it and never from a hand-maintained entry.
    """
    components: dict[str, object] = {}
    for kind in ("agents", "commands"):
        directory = root / kind
        if directory.is_dir():
            paths = [f"./{kind}/{item.name}" for item in sorted(directory.glob("*.md"))]
            if paths:
                components[kind] = paths
    skills = root / "skills"
    if skills.is_dir():
        paths = [
            f"./skills/{item.name}"
            for item in sorted(skills.iterdir())
            if (item / "SKILL.md").is_file()
        ]
        if paths:
            components["skills"] = paths
    if (root / MCP_MANIFEST).is_file():
        components["mcpServers"] = f"./{MCP_MANIFEST}"
    return components


def catalog_document(
    host: str,
    plugins: Sequence[PluginSpec],
    version: str,
    packages: Mapping[str, Path] | None = None,
) -> Mapping[str, object]:
    if host not in HOSTS:
        raise CatalogError(f"unknown host {host!r}")

    ordered = sorted(plugins, key=lambda plugin: plugin.name)
    seen: dict[str, str] = {}
    for plugin in ordered:
        if plugin.name in seen and seen[plugin.name] != plugin.version:
            raise CatalogError(
                f"{plugin.name}: version mismatch {seen[plugin.name]} against {plugin.version}"
            )
        seen[plugin.name] = plugin.version

    entries = []
    for plugin in ordered:
        entry: dict[str, object] = {
            "name": plugin.name,
            "description": plugin.description,
            "version": plugin.version,
            "license": plugin.license,
            "author": dict(OWNER),
            "dependencies": list(plugin.required_dependencies),
        }
        # A host that needs its components declared gets them from the package
        # that was just rendered, never from a hand-maintained list.
        if packages is not None and plugin.name in packages:
            entry.update(package_components(packages[plugin.name]))
        source = _source(host, plugin.name)
        if isinstance(source, dict):
            entry.update(source)
        else:
            entry["source"] = source
        entries.append(entry)

    document: dict[str, object] = {
        "name": CATALOG_NAME,
        "metadata": {"description": CATALOG_DESCRIPTION, "version": version},
        "owner": OWNER,
        "plugins": entries,
    }

    # Cross-marketplace dependencies are blocked unless the root catalog names
    # the marketplaces it trusts, and only the root's allowlist applies. Since
    # every such dependency is already declared in a kernel, the allowlist is
    # derivable: computing it is what stops a plugin from being uninstallable
    # because someone forgot to widen a hand-maintained list.
    foreign = sorted(
        {
            dependency.partition("@")[2]
            for plugin in ordered
            for dependency in plugin.required_dependencies
            if "@" in dependency
        }
    )
    if foreign:
        document["allowCrossMarketplaceDependenciesOn"] = foreign
    return document


#: The npm package name Pi installs the whole marketplace as.
PI_PACKAGE = "daodan"


def _pi_manifest(document):
    """Pi's catalog, which is an npm manifest rather than a plugin listing.

    Pi has no marketplace: it installs one package, from npm, git or a local
    path, and reads the manifest at that package's root. So the catalog for this
    host is the repository-root `package.json`, and instead of enumerating
    plugins it globs the rendered tree. `private` states that publication is by
    git tag rather than by registry, and is the one field to flip the day npm is
    added.
    """
    tree = _source("pi", "*")
    manifest = {
        "name": PI_PACKAGE,
        "version": document["metadata"]["version"],
        "private": True,
        "description": CATALOG_DESCRIPTION,
        "keywords": ["pi-package"],
        "pi": {"prompts": [f"{tree}/prompts"], "skills": [f"{tree}/skills"]},
    }
    return (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")


#: The npm package name OpenCode installs the whole marketplace as, and the
#: schema version of the `daodan` key its loader reads.
OPENCODE_PACKAGE = "daodan"
OPENCODE_MANIFEST_SCHEMA = 1


def _opencode_entry(plugin: PluginSpec, package: Path | None) -> dict[str, object]:
    """What the OpenCode loader needs to register one plugin.

    Names and descriptions are read from the rendered package rather than from
    the kernel, so the manifest describes exactly what ships. Permissions are
    derived from the kernel role's `tools` line, because the rendered agent
    carries them as YAML the loader would otherwise have to parse.
    """
    # Imported here: render imports this module for OWNER.
    from .render import PLUGIN_ROOT_PLACEHOLDER, _frontmatter, _one_line, opencode_permissions

    entry: dict[str, object] = {"root": f"plugins/{plugin.name}"}
    dependencies = [item for item in plugin.required_dependencies if "@" not in item]
    if dependencies:
        entry["dependencies"] = dependencies
    # A package that was never rendered (missing output under --check, or a
    # build stopped by validation) contributes its identity only; the drift
    # gate reports the missing package itself.
    if package is None or not package.is_dir():
        return entry

    def described(relative: str) -> dict[str, str]:
        meta, _ = _frontmatter((package / relative).read_text(encoding="utf-8"))
        return {key: _one_line(value.strip("'\"")) for key, value in meta.items()}

    skills = []
    for skill in plugin.components.skills:
        relative = f"skills/{skill}/SKILL.md"
        meta = described(relative)
        skills.append(
            {
                "id": f"{plugin.name}:{skill}",
                "name": meta.get("name", skill),
                "description": meta.get("description", ""),
                "file": relative,
            }
        )
    agents = []
    for role in plugin.components.roles:
        relative = f"agents/{role}.md"
        kernel, _ = _frontmatter((plugin.root / "roles" / f"{role}.md").read_text(encoding="utf-8"))
        agents.append(
            {
                "id": f"{plugin.name}:{role}",
                "description": described(relative).get("description", ""),
                "file": relative,
                "permissions": opencode_permissions(kernel.get("tools", "")),
            }
        )
    commands = []
    for workflow in plugin.components.workflows:
        relative = f"commands/{workflow}.md"
        commands.append(
            {
                "name": f"{plugin.name}:{workflow}",
                "description": described(relative).get("description", ""),
                "file": relative,
            }
        )
    servers = [
        {
            "name": server.name,
            "command": [
                server.command,
                *(PLUGIN_ROOT_PLACEHOLDER.sub("<plugin-root>", arg) for arg in server.args),
            ],
        }
        for server in plugin.mcp_servers
    ]
    for key, items in (("skills", skills), ("agents", agents), ("commands", commands), ("mcp", servers)):
        if items:
            entry[key] = items
    return entry


def _opencode_manifest(document, plugins: Sequence[PluginSpec], packages) -> bytes:
    """OpenCode's catalog, which is the plugin package's own npm manifest.

    OpenCode V2 has no marketplace: a package arrives as a plugin whose default
    export registers what it ships. The fixed loader beside this file does that
    from the `daodan` key, so everything plugin-specific is data here and none
    of it is generated code. `private` states that publication is by git tag,
    installed through npm's `::path:` selector.
    """
    ordered = sorted(plugins, key=lambda plugin: plugin.name)
    manifest = {
        "name": OPENCODE_PACKAGE,
        "version": document["metadata"]["version"],
        "private": True,
        "description": CATALOG_DESCRIPTION,
        "license": "MIT",
        "type": "module",
        "main": "index.js",
        "keywords": ["opencode-plugin"],
        "daodan": {
            "schema": OPENCODE_MANIFEST_SCHEMA,
            "plugins": {
                plugin.name: _opencode_entry(
                    plugin, (packages or {}).get(plugin.name)
                )
                for plugin in ordered
            },
        },
    }
    return (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def render_catalog(
    host: str,
    plugins: Sequence[PluginSpec],
    version: str,
    packages: Mapping[str, Path] | None = None,
) -> bytes:
    """Serialize one host catalog deterministically.

    Every host gets the same neutral document, which is what the identity gate
    compares. Only the serialization differs.
    """
    document = catalog_document(host, plugins, version, packages)
    if host == "pi":
        return _pi_manifest(document)
    if host == "opencode":
        return _opencode_manifest(document, plugins, packages)
    return (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("utf-8")


def assert_cross_host_identity(catalogs: Mapping[str, Mapping[str, object]]) -> None:
    """Fail unless every host lists the same plugins at the same versions."""
    reference: dict[str, str] | None = None
    for host, catalog in sorted(catalogs.items()):
        versions = {entry["name"]: entry["version"] for entry in catalog["plugins"]}
        if reference is None:
            reference = versions
        elif versions != reference:
            raise CatalogError(f"{host}: catalog identity differs from its peers")


def merge_into_legacy(
    existing: Mapping[str, object],
    plugins: Sequence[PluginSpec],
    host: str,
    packages: Mapping[str, Path],
) -> Mapping[str, object]:
    """Fold compiled entries into a catalog that still carries hand-written ones.

    Migration keeps the live Claude marketplace installable while plugins move to
    neutral kernels one at a time, so a compiled plugin replaces its own entry
    and nothing else in the catalog moves.
    """
    merged = json.loads(json.dumps(existing))
    compiled = {plugin.name: plugin for plugin in plugins}
    entries = []
    for entry in merged.get("plugins", []):
        plugin = compiled.pop(entry["name"], None)
        if plugin is not None:
            entry = dict(entry)
            entry["version"] = plugin.version
            entry["description"] = plugin.description
            entry["license"] = plugin.license
            source = _source(host, plugin.name)
            if isinstance(source, dict):
                entry.update(source)
            else:
                entry["source"] = source
            for kind in ("agents", "skills", "commands", "mcpServers"):
                entry.pop(kind, None)
            entry.update(package_components(packages[plugin.name]))
        entries.append(entry)
    for name in sorted(compiled):
        plugin = compiled[name]
        entry = {
            "name": plugin.name,
            "description": plugin.description,
            "version": plugin.version,
            "license": plugin.license,
            "dependencies": list(plugin.required_dependencies),
        }
        source = _source(host, plugin.name)
        if isinstance(source, dict):
            entry.update(source)
        else:
            entry["source"] = source
        entry.update(package_components(packages[plugin.name]))
        entries.append(entry)
    merged["plugins"] = entries
    return merged
