"""Semantic validation of neutral Daodan plugin kernels.

The loader proves a control plane is well-formed TOML. This module proves it is
coherent: identities are kebab-case, every referenced path stays inside its
plugin, every component and dependency reference resolves, every capability
comes from the closed registry, workflow graphs are acyclic, and a workflow that
declares independent review actually asks for isolation and an all-delivered
barrier.

Passes run in a fixed order so diagnostics are deterministic.
"""

from __future__ import annotations

import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, Mapping, Sequence

from .model import INLINE_WORKER_REFERENCE, PluginSpec

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

#: The closed capability registry. A capability outside this set is a typo or an
#: unbound host mechanism, and either way no adapter can promise it.
CAPABILITY_REGISTRY: frozenset[str] = frozenset(
    {
        "repository.read",
        "repository.write",
        "shell.execute",
        "network.fetch",
        "contexts.isolate",
        "roles.dispatch",
        "execution.parallel",
        "tasks.share",
        "peers.message",
        "hooks.lifecycle",
        "mcp.servers",
    }
)

#: The capability a kernel must require when it declares `[[mcp.servers]]`,
#: so that a host with no way to start the server fails the build instead of
#: shipping a workflow whose tool calls can never connect.
MCP_CAPABILITY = "mcp.servers"

#: The only prefix an MCP server argument may use to name a shipped file: the
#: compiler copies every file under a declared skill and nothing else at the
#: kernel root, so a server kept anywhere else would exist in the checkout only.
MCP_SHIPPED_PREFIX = "${CLAUDE_PLUGIN_ROOT}/skills/"

#: Declaring this outcome is what makes a workflow's fan-out independent, and
#: therefore what makes isolation mandatory rather than an optimization.
INDEPENDENT_REVIEW_OUTCOME = "reviewers-use-isolated-contexts"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: Path
    message: str


class SourcePathError(ValueError):
    """A source cannot be consumed inside its declared filesystem boundary."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def confined_source(root: Path, path: Path, *, allow_missing: bool = False) -> Path:
    """Validate metadata before reading a source, preserving its original spelling.

    Reject internal links too, consistently with the catalog's source binding.
    Reparse attributes cover Windows junctions without requiring is_junction.
    This check does not protect against hostile concurrent filesystem mutation.
    """
    root, path = Path(root), Path(path)
    boundary, candidate = root.absolute(), path.absolute()
    if ".." in candidate.parts or not candidate.is_relative_to(boundary):
        raise SourcePathError(path, "source path escapes its declared root")
    attributes = None
    for ancestor in (candidate, *candidate.parents):
        try:
            current = ancestor.lstat()
        except FileNotFoundError:
            if ancestor == candidate and not allow_missing:
                raise SourcePathError(path, "source does not exist") from None
            continue
        except OSError as error:
            raise SourcePathError(path, f"cannot inspect source metadata: {error}") from error
        if (stat.S_ISLNK(current.st_mode) or
                getattr(current, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise SourcePathError(ancestor, "linked source or ancestor is forbidden")
        if ancestor == candidate:
            attributes = current
    if attributes is not None and not (
        stat.S_ISREG(attributes.st_mode) or stat.S_ISDIR(attributes.st_mode)
    ):
        raise SourcePathError(path, "source is not a regular file or directory")
    try:
        if not candidate.resolve().is_relative_to(boundary.resolve()):
            raise SourcePathError(path, "resolved source escapes its declared root")
    except (OSError, RuntimeError) as error:
        raise SourcePathError(path, f"cannot resolve source metadata: {error}") from error
    return path


def source_members(root: Path) -> tuple[Path, ...]:
    """Validate a deterministic member set before any caller consumes its bytes."""
    root = confined_source(root, root)
    if not root.is_dir():
        raise SourcePathError(root, "source root is not a directory")
    files: list[Path] = []
    pending = [root]
    while pending:
        directory = confined_source(root, pending.pop())
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.as_posix())
        except OSError as error:
            raise SourcePathError(directory, f"cannot enumerate source metadata: {error}") from error
        for path in children:
            confined_source(root, path)
            if path.is_dir():
                pending.append(path)
            else:
                files.append(path)
    return tuple(sorted(files, key=lambda item: item.as_posix()))


def _is_escaping(reference: str) -> bool:
    candidate = Path(reference.replace("\\", "/"))
    return candidate.is_absolute() or ".." in candidate.parts


def _split_reference(reference: str) -> tuple[str, str]:
    """Split ``kind:name`` into its parts, defaulting the kind to ``role``."""
    kind, separator, name = reference.partition(":")
    if not separator:
        return "role", kind
    return kind, name


def validate_identity(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    if not KEBAB.match(plugin.name):
        issues.append(ValidationIssue("non-kebab-identity", manifest, plugin.name))
    for group, names in (
        ("skills", plugin.components.skills),
        ("roles", plugin.components.roles),
        ("workflows", plugin.components.workflows),
        ("policies", plugin.components.policies),
    ):
        for name in names:
            if not KEBAB.match(name):
                issues.append(
                    ValidationIssue("non-kebab-identity", manifest, f"components.{group}: {name}")
                )
    return issues


def validate_paths(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    try:
        source_members(plugin.root)
    except SourcePathError as error:
        issues.append(ValidationIssue("unsafe-source-path", error.path, error.message))
    for group, names in (
        ("skills", plugin.components.skills),
        ("roles", plugin.components.roles),
        ("workflows", plugin.components.workflows),
        ("policies", plugin.components.policies),
    ):
        for name in names:
            if _is_escaping(name):
                issues.append(
                    ValidationIssue("path-outside-plugin", manifest, f"components.{group}: {name}")
                )
    for workflow in plugin.workflows:
        for reference in (workflow.entrypoint, *workflow.contract.schemas):
            if _is_escaping(reference.as_posix()):
                issues.append(
                    ValidationIssue("path-outside-plugin", workflow.entrypoint, reference.as_posix())
                )
        for phase in workflow.phases:
            for reference in phase.fanout:
                _, name = _split_reference(reference)
                if _is_escaping(name):
                    issues.append(
                        ValidationIssue("path-outside-plugin", workflow.entrypoint, reference)
                    )
    return issues


def validate_components(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    resources = [
        *(plugin.root / "roles" / f"{name}.md" for name in plugin.components.roles
          if not _is_escaping(name)),
        *(plugin.root / "policies" / f"{name}.toml" for name in plugin.components.policies
          if not _is_escaping(name)),
        *(plugin.root / "skills" / name / "SKILL.md" for name in plugin.components.skills
          if not _is_escaping(name)),
        *(plugin.root / resource for workflow in plugin.workflows
          for resource in (workflow.entrypoint, *workflow.contract.schemas)),
    ]
    for resource in resources:
        try:
            confined_source(plugin.root, resource, allow_missing=True)
        except SourcePathError as error:
            issues.append(ValidationIssue("unsafe-source-path", error.path, error.message))
    if issues:
        return issues
    # Duplicates within one kind. Across kinds, see validate_component_kinds.
    for names in (
        plugin.components.skills,
        plugin.components.roles,
        plugin.components.workflows,
        plugin.components.policies,
    ):
        seen: set[str] = set()
        for name in names:
            if name in seen:
                issues.append(ValidationIssue("duplicate-component", manifest, name))
            seen.add(name)

    for name in plugin.components.roles:
        if _is_escaping(name):
            continue
        if not (plugin.root / "roles" / f"{name}.md").is_file():
            issues.append(
                ValidationIssue("missing-component-file", manifest, f"roles/{name}.md")
            )
    for name in plugin.components.policies:
        if _is_escaping(name):
            continue
        if not (plugin.root / "policies" / f"{name}.toml").is_file():
            issues.append(
                ValidationIssue("missing-component-file", manifest, f"policies/{name}.toml")
            )
    for name in plugin.components.skills:
        if _is_escaping(name):
            continue
        if not (plugin.root / "skills" / name / "SKILL.md").is_file():
            issues.append(
                ValidationIssue("missing-component-file", manifest, f"skills/{name}/SKILL.md")
            )
    for workflow in plugin.workflows:
        if not (plugin.root / workflow.entrypoint).is_file():
            issues.append(
                ValidationIssue(
                    "missing-component-file", manifest, workflow.entrypoint.as_posix()
                )
            )
        for schema in workflow.contract.schemas:
            if not (plugin.root / schema).is_file():
                issues.append(
                    ValidationIssue("missing-component-file", manifest, schema.as_posix())
                )
    return issues


def validate_dependencies(
    plugin: PluginSpec, registry: Mapping[str, PluginSpec] | None = None
) -> list[ValidationIssue]:
    """Static fan-out roles must resolve inside this plugin or a required dependency.

    There is no optional local dependency by policy, so a role that resolves
    nowhere is a broken package rather than a degraded one.
    """
    issues: list[ValidationIssue] = []
    roles = set(plugin.components.roles)
    dependencies = set(plugin.required_dependencies)
    required_names = {item.partition("@")[0] for item in dependencies}
    optional_names: set[str] = set()
    for dependency in plugin.optional_dependencies:
        owner, separator, marketplace = dependency.partition("@")
        if not separator or not KEBAB.fullmatch(owner) or not KEBAB.fullmatch(marketplace):
            issues.append(ValidationIssue("invalid-optional-dependency", plugin.root / "plugin.toml",
                                          f"Optional dependencies require name@marketplace: {dependency}"))
        elif owner == plugin.name or (registry is not None and owner in registry):
            issues.append(ValidationIssue("optional-local-dependency", plugin.root / "plugin.toml",
                                          f"Local providers must be required: {dependency}"))
        if owner in required_names:
            issues.append(ValidationIssue("conflicting-dependency", plugin.root / "plugin.toml",
                                          f"Provider is both required and optional: {owner}"))
        if owner in optional_names:
            issues.append(ValidationIssue("duplicate-optional-dependency", plugin.root / "plugin.toml", owner))
        optional_names.add(owner)
    for workflow in plugin.workflows:
        references = [f"role:{role}" for role in workflow.dispatch.roles]
        if workflow.dispatch.inline_workers:
            references.append(f"role:{INLINE_WORKER_REFERENCE}")
        if workflow.dispatch.roles or workflow.dispatch.inline_workers:
            if "roles.dispatch" not in plugin.capabilities.required:
                issues.append(ValidationIssue("dispatch-without-capability", workflow.entrypoint,
                                              "Method dispatch requires roles.dispatch"))
        if len(set(workflow.dispatch.roles)) != len(workflow.dispatch.roles):
            issues.append(ValidationIssue("duplicate-dispatch-role", workflow.entrypoint, "Duplicate method role"))
        for reference in workflow.dispatch.roles:
            owner, separator, role = reference.partition("/")
            if (not KEBAB.fullmatch(owner) or (separator and not KEBAB.fullmatch(role))):
                issues.append(ValidationIssue("invalid-dispatch-role", workflow.entrypoint, reference))
        for phase in workflow.phases:
            references.extend(phase.fanout)
            if phase.role is not None:
                references.append(f"role:{phase.role}")
        for reference in references:
            kind, name = _split_reference(reference)
            if kind != "role":
                continue
            owner, separator, role = name.partition("/")
            if separator:
                if owner != plugin.name and owner not in dependencies:
                    issues.append(
                        ValidationIssue("undeclared-dependency", workflow.entrypoint, reference)
                    )
                elif registry is not None:
                    provider = registry.get(owner)
                    if provider is None:
                        issues.append(ValidationIssue("unknown-role-provider", workflow.entrypoint, reference))
                    elif role not in provider.components.roles:
                        issues.append(ValidationIssue("unknown-role", workflow.entrypoint, reference))
            elif name not in roles:
                issues.append(ValidationIssue("unknown-role", workflow.entrypoint, reference))
    return issues


def validate_contract_exports(
    plugin: PluginSpec, registry: Mapping[str, PluginSpec]
) -> list[ValidationIssue]:
    """A shared schema is a declared provider resource, never a copied consumer file."""
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    seen: set[Path] = set()
    for exported in plugin.contract_exports:
        if exported in seen:
            issues.append(ValidationIssue("duplicate-contract-export", manifest, exported.as_posix()))
        seen.add(exported)
        if (_is_escaping(exported.as_posix()) or len(exported.parts) < 2
                or exported.parts[0] != "contracts" or exported.suffix != ".toml"):
            issues.append(ValidationIssue("invalid-contract-export", manifest, exported.as_posix()))
            continue
        resource = plugin.root / exported
        try:
            confined_source(plugin.root, resource, allow_missing=True)
        except SourcePathError as error:
            issues.append(ValidationIssue("invalid-contract-export", error.path, error.message))
            continue
        if not resource.is_file():
            issues.append(ValidationIssue("missing-contract-export", manifest, exported.as_posix()))
        elif not resource.resolve().is_relative_to(plugin.root.resolve()):
            issues.append(ValidationIssue("invalid-contract-export", manifest, exported.as_posix()))
    for workflow in plugin.workflows:
        for reference in workflow.contract.shared_schemas:
            owner, separator, path = reference.partition("/")
            candidate = Path(path)
            if (not separator or not KEBAB.fullmatch(owner) or _is_escaping(path)
                    or len(candidate.parts) < 2 or candidate.parts[0] != "contracts"
                    or candidate.suffix != ".toml"):
                issues.append(ValidationIssue("invalid-shared-schema", workflow.entrypoint, reference))
                continue
            if owner not in plugin.required_dependencies:
                issues.append(ValidationIssue("undeclared-schema-provider", workflow.entrypoint, reference))
                continue
            provider = registry.get(owner)
            if provider is None:
                issues.append(ValidationIssue("unknown-schema-provider", workflow.entrypoint, reference))
            elif candidate not in provider.contract_exports:
                issues.append(ValidationIssue("unexported-shared-schema", workflow.entrypoint, reference))
    return issues


def validate_capabilities(
    plugin: PluginSpec, capabilities: AbstractSet[str]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    declared = list(plugin.capabilities.required) + list(plugin.capabilities.optional)
    for capability in declared:
        if capability not in capabilities:
            issues.append(ValidationIssue("unknown-capability", manifest, capability))
    overlap = sorted(set(plugin.capabilities.required) & set(plugin.capabilities.optional))
    for capability in overlap:
        issues.append(ValidationIssue("capability-declared-twice", manifest, capability))
    return issues


def validate_workflow_graph(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for workflow in plugin.workflows:
        phase_ids: set[str] = set()
        for phase in workflow.phases:
            if phase.id in phase_ids:
                issues.append(ValidationIssue(
                    "duplicate-phase-id", workflow.entrypoint, phase.id
                ))
            phase_ids.add(phase.id)
        if len(phase_ids) != len(workflow.phases):
            continue
        phases = {phase.id: phase for phase in workflow.phases}
        positions = {phase.id: index for index, phase in enumerate(workflow.phases)}
        colors = {phase_id: "white" for phase_id in phases}

        def visit(phase_id: str) -> None:
            if colors[phase_id] == "gray":
                issues.append(ValidationIssue("workflow-cycle", workflow.entrypoint, phase_id))
                return
            if colors[phase_id] == "black":
                return
            colors[phase_id] = "gray"
            for dependency in phases[phase_id].needs:
                if dependency not in phases:
                    issues.append(
                        ValidationIssue("unknown-phase", workflow.entrypoint, dependency)
                    )
                else:
                    if positions[dependency] >= positions[phase_id]:
                        issues.append(ValidationIssue(
                            "non-prior-phase-dependency", workflow.entrypoint,
                            f"{phase_id}: prerequisite {dependency!r} "
                            "must be declared earlier",
                        ))
                    visit(dependency)
            colors[phase_id] = "black"

        for phase_id in phases:
            visit(phase_id)
    return issues


def validate_execution_contracts(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for workflow in plugin.workflows:
        produced = {item for phase in workflow.phases for item in phase.produces}
        available: set[str] = set()
        independent = INDEPENDENT_REVIEW_OUTCOME in workflow.contract.outcomes
        for phase in workflow.phases:
            if phase.invoke is not None:
                issues.append(ValidationIssue("unsupported-workflow-invoke", workflow.entrypoint, phase.id))
            has_fanout = bool(phase.fanout or phase.fanout_from)
            if phase.fanout and phase.fanout_from:
                issues.append(ValidationIssue("ambiguous-fanout", workflow.entrypoint, phase.id))
            if has_fanout and phase.join is None:
                issues.append(ValidationIssue("fanout-needs-join", workflow.entrypoint, phase.id))
            if phase.fanout_from and phase.fanout_from not in produced:
                issues.append(
                    ValidationIssue(
                        "unknown-fanout-selection", workflow.entrypoint, phase.fanout_from
                    )
                )
            elif phase.fanout_from and phase.fanout_from not in available:
                issues.append(ValidationIssue(
                    "unavailable-fanout-selection", workflow.entrypoint,
                    f"{phase.id}: {phase.fanout_from} "
                    "must be produced by an earlier phase",
                ))
            if independent and has_fanout and phase.isolation != "required":
                issues.append(
                    ValidationIssue(
                        "independent-fanout-needs-isolation", workflow.entrypoint, phase.id
                    )
                )
            for item in phase.consumes:
                if item not in produced:
                    issues.append(
                        ValidationIssue("unproduced-artifact", workflow.entrypoint, item)
                    )
                elif item not in available:
                    issues.append(ValidationIssue(
                        "unavailable-artifact", workflow.entrypoint,
                        f"{phase.id}: {item} must be produced by an earlier phase",
                    ))
            available.update(phase.produces)
        for artifact in workflow.contract.artifacts:
            if f"artifact:{artifact}" not in produced:
                issues.append(
                    ValidationIssue("unproduced-artifact", workflow.entrypoint, artifact)
                )
    return issues


def validate_mcp_servers(plugin: PluginSpec) -> list[ValidationIssue]:
    """An MCP server is a capability the host must supply and a file the package must ship.

    Declaring servers without requiring `mcp.servers` would let a host with no
    binding render the package and ship a workflow that can never connect;
    requiring the capability without a server is a declaration nothing backs.
    A server started from a path the compiler does not copy is the defect the
    bundled-path linter's third pass exists for, caught here at the source.
    """
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    required = MCP_CAPABILITY in plugin.capabilities.required
    if plugin.mcp_servers and not required:
        issues.append(
            ValidationIssue("mcp-capability-undeclared", manifest, MCP_CAPABILITY)
        )
    if required and not plugin.mcp_servers:
        issues.append(
            ValidationIssue("mcp-capability-without-servers", manifest, MCP_CAPABILITY)
        )
    seen: set[str] = set()
    for server in plugin.mcp_servers:
        where = f"mcp.servers: {server.name}"
        if not KEBAB.match(server.name):
            issues.append(ValidationIssue("non-kebab-identity", manifest, where))
        if server.name in seen:
            issues.append(ValidationIssue("duplicate-mcp-server", manifest, where))
        seen.add(server.name)
        if not server.command.strip():
            issues.append(ValidationIssue("mcp-server-without-command", manifest, where))
        for argument in server.args:
            if not argument.startswith("${CLAUDE_PLUGIN_ROOT}/"):
                continue
            relative = argument[len("${CLAUDE_PLUGIN_ROOT}/") :]
            if _is_escaping(relative):
                issues.append(ValidationIssue("path-outside-plugin", manifest, argument))
                continue
            try:
                confined_source(plugin.root, plugin.root / relative, allow_missing=True)
            except SourcePathError as error:
                issues.append(ValidationIssue("unsafe-source-path", error.path, error.message))
                continue
            if not argument.startswith(MCP_SHIPPED_PREFIX) or not (plugin.root / relative).is_file():
                issues.append(
                    ValidationIssue("mcp-server-file-not-shipped", manifest, argument)
                )
    return issues


#: The component kinds that share no name inside a plugin, in report order.
COMPONENT_KINDS: tuple[str, ...] = ("skills", "roles", "workflows")


def validate_component_kinds(plugin: PluginSpec) -> list[ValidationIssue]:
    """Refuse a name that names two kinds of component inside one plugin.

    OpenCode lists skills and agents in one `@` menu, so a skill and a role of
    the same name render as two identical entries that insert different things.
    The rule is general rather than host-specific, because a name meaning two
    things in one plugin is ambiguous to every reader of a body that cites it.
    A role beside a same-topic skill takes `-agent`; a skill beside a
    same-topic workflow takes `-method`.
    """
    manifest = plugin.root / "plugin.toml"
    kinds_by_name: dict[str, list[str]] = {}
    for kind in COMPONENT_KINDS:
        for name in dict.fromkeys(getattr(plugin.components, kind)):
            kinds_by_name.setdefault(name, []).append(kind)
    return [
        ValidationIssue(
            "component-name-shared-across-kinds", manifest, f"{name}: {', '.join(kinds)}"
        )
        for name, kinds in sorted(kinds_by_name.items())
        if len(kinds) > 1
    ]


def _duplicate_plugin_issues(plugins: Sequence[PluginSpec]) -> list[ValidationIssue]:
    """Reject ambiguous names before a registry can discard a physical kernel."""
    roots_by_name: dict[str, list[Path]] = {}
    for plugin in plugins:
        roots_by_name.setdefault(plugin.name, []).append(plugin.root)
    issues: list[ValidationIssue] = []
    for name, roots in sorted(roots_by_name.items()):
        if len(roots) < 2:
            continue
        ordered = sorted(roots, key=lambda root: root.as_posix())
        issues.append(ValidationIssue(
            "duplicate-plugin-name", ordered[0] / "plugin.toml",
            f"Duplicate plugin name {name!r}: {', '.join(str(root) for root in ordered)}",
        ))
    return issues


def validate_plugins(
    plugins: Sequence[PluginSpec], capabilities: AbstractSet[str]
) -> list[ValidationIssue]:
    """Run every pass over every plugin, in a fixed order."""
    issues = _duplicate_plugin_issues(plugins)
    if issues:
        return issues
    registry = {plugin.name: plugin for plugin in plugins}
    for plugin in plugins:
        issues.extend(validate_identity(plugin))
        path_issues = validate_paths(plugin)
        issues.extend(path_issues)
        if path_issues:
            # Metadata parsers must not run over an unbound source tree.
            continue
        issues.extend(validate_components(plugin))
        issues.extend(validate_component_kinds(plugin))
        from .skill_catalog import validate_skill_metadata
        issues.extend(validate_skill_metadata(plugin))
        issues.extend(validate_dependencies(plugin, registry))
        issues.extend(validate_contract_exports(plugin, registry))
        issues.extend(validate_capabilities(plugin, capabilities))
        issues.extend(validate_mcp_servers(plugin))
        issues.extend(validate_workflow_graph(plugin))
        issues.extend(validate_execution_contracts(plugin))
    return issues
