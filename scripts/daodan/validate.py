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
        phases = {phase.id: phase for phase in workflow.phases}
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
                    visit(dependency)
            colors[phase_id] = "black"

        for phase_id in phases:
            visit(phase_id)
    return issues


def validate_execution_contracts(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for workflow in plugin.workflows:
        produced = {item for phase in workflow.phases for item in phase.produces}
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
            elif not argument.startswith(MCP_SHIPPED_PREFIX) or not (
                plugin.root / relative
            ).is_file():
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


def validate_plugins(
    plugins: Sequence[PluginSpec], capabilities: AbstractSet[str]
) -> list[ValidationIssue]:
    """Run every pass over every plugin, in a fixed order."""
    issues: list[ValidationIssue] = []
    registry = {plugin.name: plugin for plugin in plugins}
    for plugin in plugins:
        issues.extend(validate_identity(plugin))
        issues.extend(validate_paths(plugin))
        issues.extend(validate_components(plugin))
        issues.extend(validate_component_kinds(plugin))
        issues.extend(validate_dependencies(plugin, registry))
        issues.extend(validate_contract_exports(plugin, registry))
        issues.extend(validate_capabilities(plugin, capabilities))
        issues.extend(validate_mcp_servers(plugin))
        issues.extend(validate_workflow_graph(plugin))
        issues.extend(validate_execution_contracts(plugin))
    return issues
