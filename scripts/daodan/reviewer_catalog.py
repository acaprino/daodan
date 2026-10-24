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
    ("senior-review", "accessibility-auditor"),
    ("senior-review", "api-contract-auditor"),
    ("senior-review", "chicken-egg-detector"),
    ("senior-review", "cleanup-auditor"),
    ("senior-review", "code-auditor"),
    ("senior-review", "data-integrity-auditor"),
    ("senior-review", "distributed-flow-auditor"),
    ("senior-review", "logic-integrity-auditor"),
    ("senior-review", "operability-auditor"),
    ("senior-review", "performance-auditor"),
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
    ("senior-review", "authorization-auditor"),
    ("senior-review", "session-delegation-auditor"),
    ("senior-review", "secret-exposure-auditor"),
    ("senior-review", "input-validation-auditor"),
    ("senior-review", "untrusted-resource-auditor"),
    ("senior-review", "browser-security-auditor"),
    ("senior-review", "callback-authenticity-auditor"),
    ("senior-review", "ai-boundary-auditor"),
    ("senior-review", "audit-trail-auditor"),
    ("senior-review", "transaction-integrity-auditor"),
    ("senior-review", "schema-coherence-auditor"),
    ("senior-review", "cache-consistency-auditor"),
    ("senior-review", "data-representation-auditor"),
    ("senior-review", "data-retention-auditor"),
    ("senior-review", "message-delivery-auditor"),
    ("senior-review", "remote-effect-auditor"),
    ("senior-review", "service-resilience-auditor"),
    ("senior-review", "sql-efficiency-auditor"),
    ("senior-review", "algorithmic-cost-auditor"),
    ("senior-review", "asset-delivery-auditor"),
    ("senior-review", "capacity-quota-auditor"),
    ("senior-review", "runtime-cost-auditor"),
    ("senior-review", "observability-auditor"),
    ("senior-review", "service-health-auditor"),
    ("senior-review", "release-compatibility-auditor"),
    ("senior-review", "environment-binding-auditor"),
    ("senior-review", "feature-flag-auditor"),
    ("senior-review", "recovery-auditor"),
    ("senior-review", "accessible-navigation-auditor"),
    ("senior-review", "accessible-perception-auditor"),
    ("senior-review", "local-correctness-auditor"),
    ("senior-review", "local-concurrency-auditor"),
    ("senior-review", "application-reachability-auditor"),
    ("senior-review", "dependency-usage-auditor"),
    ("senior-review", "artifact-lifecycle-auditor"),
    ("testing", "test-suite-structure-auditor"),
    ("testing", "test-oracle-auditor"),
    ("testing", "test-reliability-auditor"),
    ("testing", "journey-protection-auditor"),
    ("testing", "contract-test-auditor"),
    ("testing", "capacity-test-auditor"),
    ("testing", "ai-evaluation-auditor"),
    ("react-development", "react-effects-auditor"),
    ("react-development", "react-render-cost-auditor"),
    ("react-development", "react-bundle-auditor"),
    ("react-development", "react-dataflow-auditor"),
    ("typescript-development", "type-soundness-auditor"),
    ("typescript-development", "typed-boundary-auditor"),
    ("platform-engineering", "browser-compatibility-auditor"),
    ("platform-engineering", "offline-lifecycle-auditor"),
    ("platform-engineering", "native-lifecycle-auditor"),
    ("platform-engineering", "desktop-bridge-auditor"),
    ("platform-engineering", "app-distribution-auditor"),
    ("abstraction-architect", "concept-ownership-auditor"),
    ("abstraction-architect", "abstraction-fit-auditor"),
    ("python-development", "python-semantics-auditor"),
)

# Prerequisites a role body states as a gate. An empty list means the prepared
# brief (target, diff, instructions and evidence pack) is sufficient.
PREREQUISITES: dict[str, list[str]] = {
    "senior-review:logic-integrity-auditor": [
        "one-of: interconnect-map (team-review/02-interconnect.md), scoped-semantic-context",
    ],
    "senior-review:premise-auditor": [
        "declared-mode: 1-blind (no maps, no peer findings), 2-full-context or 3-claim-check",
    ],
    "abstraction-architect:abstraction-architect-agent": ["candidate-bound-codebase-map"],
    "abstraction-architect:concept-ownership-auditor": ["candidate-bound-codebase-map"],
    "abstraction-architect:abstraction-fit-auditor": ["candidate-bound-codebase-map"],
    "testing:test-suite-auditor": ["prepared-test-suite-context"],
    "testing:test-suite-structure-auditor": ["prepared-test-suite-context"],
    "testing:test-reliability-auditor": ["prepared-test-suite-context"],
}

METHOD_BINDINGS: tuple[dict[str, object], ...] = (
    {
        "id": "senior-review:python-method",
        "dimension": "python",
        "role": "work-controller:isolated-worker",
        "skills": [
            "python-development:python-refactor-method",
            "python-development:python-dead-code",
        ],
        "mode": "audit-only",
        "members": ["python-development:python-semantics-auditor",
                    "senior-review:application-reachability-auditor"],
        "trigger_when": "target includes .py or .pyi files, or the relevant package declares pyproject.toml, setup.py, uv.lock or requirements*.txt",
    },
    {
        "id": "senior-review:dependencies-method",
        "dimension": "dependencies",
        "role": "work-controller:isolated-worker",
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


def method_body(binding: dict) -> str:
    """Bind existing audit methods; detection stays in their owning skills."""
    skills = ", ".join(f"`{name}`" for name in binding["skills"])
    return (f"# {binding['id']}\n\nLoad {skills} from verified installed providers. "
            "Apply their audit-only checks to the assigned scope and candidate; preserve "
            "their required inputs and evidence. Do not apply remediation. "
            "Use the supplied common review conventions and delivery contract.\n")


def reviewer_catalog(registry, host: str, roles_layout: str | None, *, adapter=None, adapters_root=None, role_overrides=None) -> dict:
    """The catalog for one host package, from the loaded kernel registry."""
    from .render import _package_context, rendered_role_text, _kernel_digest, digest_bytes, _inline_role_scope
    from .role_bodies import resolve_role
    from .adapter import load_adapter
    from pathlib import Path
    if adapter is None:
        adapters_root = Path(__file__).resolve().parents[2] / "adapters"
        adapter = load_adapter(adapters_root, host)

    entries: list[dict[str, object]] = []
    kernel_hashes = {}

    def kernel_hash(name):
        if name not in kernel_hashes:
            kernel_hashes[name] = _kernel_digest(registry[name])
        return kernel_hashes[name]
    for provider_name, role in REVIEWER_ROLES:
        provider = registry.get(provider_name)
        if provider is None:
            raise ReviewerCatalogError(f"reviewer provider is not loaded: {provider_name}")
        if role not in provider.components.roles:
            raise ReviewerCatalogError(f"reviewer role is not registered: {provider_name}:{role}")
        try:
            resolved = resolve_role(registry, provider_name, role)
        except (OSError, ValueError) as error:
            raise ReviewerCatalogError(f"cannot resolve reviewer role: {provider_name}:{role}: {error}") from error
        from .role_bodies import role_text
        meta, body = _parse_role(role_text(resolved))
        for override in (role_overrides or {}).get(provider_name, ()):
            if override.source == f"role:{role}":
                meta, _ = _parse_role((override.root / override.replacement).read_text(encoding="utf-8"))
        description = meta.get("description", "")
        trigger_when, do_not_trigger_when = _triggers(description)
        if resolved["composed"]:
            trigger_when = resolved["trigger_when"]
        entry: dict[str, object] = {
            "id": f"{provider_name}:{role}",
            "kind": "role",
            "provider": provider_name,
            "provider_version": provider.version,
            "role": role,
            "file": f"roles/{role}.md",
            "description": description,
            "operation_scope": _inline_role_scope(meta).strip(),
            "trigger_when": trigger_when,
            "do_not_trigger_when": do_not_trigger_when,
            "prerequisites": list(dict.fromkeys(value for member in resolved["members"]
                                                for value in PREREQUISITES.get(member, []))),
            "source_hashes": {**resolved["source_hashes"],
                              **{f"{part['owner']}/kernel": kernel_hash(part["owner"])
                                 for part in resolved["parts"]}},
            "body_sha256": "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }
        if resolved["composed"]:
            entry["members"] = resolved["members"]
        for override in (role_overrides or {}).get(provider_name, ()):
            if override.source == f"role:{role}":
                entry["source_hashes"][f"{provider_name}/override:{role}"] = "sha256:" + hashlib.sha256(
                    digest_bytes(override.root / override.replacement, override.root)).hexdigest()
        if roles_layout:
            relative = render_path(roles_layout, {
                **_package_context(provider, host), "role": role}).as_posix()
            host_text = rendered_role_text(provider, role, registry, adapter, adapters_root,
                                           role_overrides=role_overrides)
            entry["host_binding"] = {"host": host, "id": f"{provider_name}:{role}", "file": relative,
                                     "root_reference": adapter.layout.get("plugin_root_reference", "${CLAUDE_PLUGIN_ROOT}"),
                                     "sha256": "sha256:" + hashlib.sha256(host_text.encode()).hexdigest()}
        entries.append(entry)
    for binding in METHOD_BINDINGS:
        from .render import _host_text, _operational_binding
        provider = registry["senior-review"]
        text = _host_text(method_body(binding), adapter,
                          operational_binding=_operational_binding(adapter, adapters_root)).rstrip() + "\n"
        hashes = {}
        for skill in binding["skills"]:
            name, component = skill.split(":")
            if name not in registry or component not in registry[name].components.skills:
                raise ReviewerCatalogError(f"method skill unavailable: {skill}")
            hashes[name] = kernel_hash(name)
        entries.append({
            **binding,
            "kind": "method-binding",
            "provider": provider.name,
            "provider_version": provider.version,
            "operation_scope": _inline_role_scope(
                resolve_role(registry, "work-controller", "isolated-worker")["metadata"]).strip(),
            "source_hashes": hashes,
            "host_binding": {"host": host, "id": binding["id"],
                             "file": f"skills/review-preparation/references/method-bindings/{binding['dimension']}.md",
                             "root_reference": adapter.layout.get("plugin_root_reference", "${CLAUDE_PLUGIN_ROOT}"),
                             "sha256": "sha256:" + hashlib.sha256(text.encode()).hexdigest()},
            "prerequisites": [],
            "do_not_trigger_when": "",
        })
    return {"schema": CATALOG_SCHEMA, "host": host, "entries": entries}
