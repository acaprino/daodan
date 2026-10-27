"""Immutable types for the neutral Daodan control plane.

Every type here is host-neutral by construction: nothing names a Claude team
API, a Copilot subagent tool or a Codex dispatch primitive. Markdown remains the
behavioural source, so no type carries a prompt body.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SCHEMA = "daodan/v1"

Isolation = Literal["shared", "required"]
JoinPolicy = Literal["all-delivered", "best-effort"]
Concurrency = Literal["preferred", "required", "forbidden"]

ISOLATIONS: tuple[str, ...] = ("shared", "required")
JOIN_POLICIES: tuple[str, ...] = ("all-delivered", "best-effort")
CONCURRENCIES: tuple[str, ...] = ("preferred", "required", "forbidden")
INLINE_WORKER_REFERENCE = "work-controller/isolated-worker"
HOOK_EVENTS: tuple[str, ...] = ("session-start", "user-prompt-submit")


@dataclass(frozen=True)
class ContractSpec:
    inputs: tuple[str, ...]
    outcomes: tuple[str, ...]
    artifacts: tuple[str, ...]
    schemas: tuple[Path, ...] = ()
    shared_schemas: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhaseSpec:
    id: str
    needs: tuple[str, ...] = ()
    invoke: str | None = None
    role: str | None = None
    fanout: tuple[str, ...] = ()
    fanout_from: str | None = None
    isolation: Isolation = "shared"
    join: JoinPolicy | None = None
    concurrency: Concurrency = "preferred"
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()


@dataclass(frozen=True)
class DispatchSpec:
    """Workers a loaded method may dispatch, independently of phase scheduling."""

    roles: tuple[str, ...] = ()
    isolated: bool = False
    inline_workers: bool = False


@dataclass(frozen=True)
class WorkflowSpec:
    name: str
    entrypoint: Path
    phases: tuple[PhaseSpec, ...]
    contract: ContractSpec
    dispatch: DispatchSpec = DispatchSpec()

    def worker_references(self, local_roles: tuple[str, ...] = ()) -> tuple[str, ...]:
        """Derive the neutral worker union without assigning host identities."""
        references = set(self.dispatch.roles)
        if self.dispatch.inline_workers:
            references.add(INLINE_WORKER_REFERENCE)
        for phase in self.phases:
            references.update(reference.partition(":")[2] or reference for reference in phase.fanout)
            if phase.role:
                references.add(phase.role)
            if phase.fanout_from and not phase.role:
                references.update(local_roles)
        return tuple(sorted(references))


@dataclass(frozen=True)
class CapabilityRequirements:
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentIndex:
    skills: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    workflows: tuple[str, ...] = ()
    policies: tuple[str, ...] = ()


@dataclass(frozen=True)
class McpServerSpec:
    """One stdio MCP server the plugin ships and needs the host to start.

    The command and its arguments are written the way a kernel writes every
    path, with `${CLAUDE_PLUGIN_ROOT}` naming the installed package; each
    adapter decides whether it can render the declaration as a manifest the
    host starts on its own, or must ask the user to register it.
    """

    name: str
    command: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class HookSpec:
    """A bounded Python callback; adapters own event registration and launch syntax."""

    name: str
    event: str
    script: Path
    args: tuple[str, ...] = ()
    timeout: int = 10


@dataclass(frozen=True)
class PluginSpec:
    root: Path
    schema: str
    name: str
    version: str
    description: str
    license: str
    capabilities: CapabilityRequirements
    required_dependencies: tuple[str, ...]
    components: ComponentIndex
    workflows: tuple[WorkflowSpec, ...]
    mcp_servers: tuple[McpServerSpec, ...] = ()
    contract_exports: tuple[Path, ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    reviewer_compositions: tuple[tuple[str, tuple[str, ...]], ...] = ()
    hooks: tuple[HookSpec, ...] = ()

    @property
    def foreign_providers(self) -> dict[str, str]:
        """Base name to `name@marketplace` for each required provider of another marketplace."""
        return {item.partition("@")[0]: item for item in self.required_dependencies if "@" in item}


class ModelError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")
