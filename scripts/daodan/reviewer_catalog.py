"""Compile the portable reviewer catalog shipped with senior-review.

The catalog is a compile-time projection of role kernels. It never reads a
plugin at review runtime: render.py writes it into the senior-review package,
and review preparation reads that one JSON resource. Markdown remains the
behaviour; this module only extracts identity, triggers and digests.
"""
from __future__ import annotations

import hashlib
import re

from .templates import render_path

CATALOG_SCHEMA = "daodan/reviewer-catalog/v1"


class ReviewerCatalogError(ValueError):
    pass


# Reviewer roles senior-review can dispatch: its own dimensions plus the named
# roles of its mandatory providers that review preparation binds. Providers
# whose review value is a method rather than a role (python-development,
# dependency-audit) appear below as method bindings through the declared
# isolated worker, never as invented roles.
REVIEWER_ROLES: tuple[tuple[str, str], ...] = (
    ("senior-review", "api-contract-auditor"),
    ("senior-review", "chicken-egg-detector"),
    ("senior-review", "cleanup-auditor"),
    ("senior-review", "code-auditor"),
    ("senior-review", "data-integrity-auditor"),
    ("senior-review", "distributed-flow-auditor"),
    ("senior-review", "logic-integrity-auditor"),
    ("senior-review", "premise-auditor"),
    ("senior-review", "resource-lifecycle-auditor"),
    ("senior-review", "security-auditor"),
    ("senior-review", "temporal-resilience-auditor"),
    ("senior-review", "ui-race-auditor"),
    ("repo-hygiene", "workspace-auditor"),
    ("testing", "test-suite-auditor"),
    ("abstraction-architect", "abstraction-architect-agent"),
    ("react-development", "react-performance-optimizer"),
    ("typescript-development", "type-safety-auditor"),
    ("platform-engineering", "platform-reviewer"),
)

# Prerequisites a role body states as a gate. An empty list means the prepared
# brief (target, diff, instructions and evidence pack) is sufficient.
PREREQUISITES: dict[str, list[str]] = {
    "senior-review:logic-integrity-auditor": [
        "one-of: interconnect-map (team-review/02-interconnect.md), scoped-semantic-context",
    ],
    "senior-review:premise-auditor": [
        "declared-mode: 1-blind (no maps, no peer findings) or 2-full-context",
    ],
}

METHOD_BINDINGS: tuple[dict[str, object], ...] = (
    {
        "id": "senior-review:python-method",
        "dimension": "python",
        "role": "project-protocol:isolated-worker",
        "skills": [
            "python-development:python-refactor-method",
            "python-development:python-dead-code",
        ],
        "mode": "audit-only",
        "trigger_when": "target includes .py or .pyi files, or the relevant package declares pyproject.toml, setup.py, uv.lock or requirements*.txt",
    },
    {
        "id": "senior-review:dependencies-method",
        "dimension": "dependencies",
        "role": "project-protocol:isolated-worker",
        "skills": ["dependency-audit:dependency-audit"],
        "mode": "audit-only",
        "trigger_when": "candidate changes a manifest or lockfile",
    },
)

_TRIGGER = re.compile(r"TRIGGER WHEN:\s*(.*?)(?:\s+DO NOT TRIGGER WHEN:\s*(.*))?$", re.DOTALL)


def _parse_role(text: str) -> tuple[dict[str, str], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        return {}, normalized
    end = normalized.find("\n---\n", 4)
    if end == -1:
        raise ReviewerCatalogError("role frontmatter has no closing delimiter")
    meta: dict[str, str] = {}
    key: str | None = None
    for line in normalized[4:end].split("\n"):
        if line[:1] not in {" ", "\t"} and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            meta[key] = value.strip()
        elif key is not None and line.strip():
            meta[key] = f"{meta[key]} {line.strip()}".strip()
    for name, value in meta.items():
        if value.startswith((">", "|")):
            meta[name] = value[1:].strip()
    return meta, normalized[end + 5:]


def _triggers(description: str) -> tuple[str, str]:
    match = _TRIGGER.search(description or "")
    if not match:
        return "", ""
    return " ".join(match.group(1).split()), " ".join((match.group(2) or "").split())


def reviewer_catalog(registry, host: str, roles_layout: str | None) -> dict:
    """The catalog for one host package, from the loaded kernel registry."""
    from .render import _package_context

    entries: list[dict[str, object]] = []
    for provider_name, role in REVIEWER_ROLES:
        provider = registry.get(provider_name)
        if provider is None:
            raise ReviewerCatalogError(f"reviewer provider is not loaded: {provider_name}")
        if role not in provider.components.roles:
            raise ReviewerCatalogError(f"reviewer role is not registered: {provider_name}:{role}")
        source = provider.root / "roles" / f"{role}.md"
        try:
            text = source.read_text(encoding="utf-8")
        except OSError as error:
            raise ReviewerCatalogError(f"cannot read reviewer role: {source}") from error
        meta, body = _parse_role(text)
        description = meta.get("description", "")
        trigger_when, do_not_trigger_when = _triggers(description)
        entry: dict[str, object] = {
            "id": f"{provider_name}:{role}",
            "kind": "role",
            "provider": provider_name,
            "provider_version": provider.version,
            "role": role,
            "file": f"roles/{role}.md",
            "description": description,
            "trigger_when": trigger_when,
            "do_not_trigger_when": do_not_trigger_when,
            "prerequisites": PREREQUISITES.get(f"{provider_name}:{role}", []),
            "body_sha256": "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }
        if roles_layout:
            relative = render_path(roles_layout, {
                **_package_context(provider, host), "role": role}).as_posix()
            entry["host_binding"] = {"host": host, "id": f"{provider_name}:{role}", "file": relative}
        entries.append(entry)
    for binding in METHOD_BINDINGS:
        entries.append({
            **binding,
            "kind": "method-binding",
            "prerequisites": [],
            "do_not_trigger_when": "",
        })
    return {"schema": CATALOG_SCHEMA, "host": host, "entries": entries}
