"""Fingerprinted semantic overrides.

Every semantic divergence between hosts lives in an override under
``adapters/<host>/overrides/``, never as a quiet edit inside a rendered package.
An override carries the digest of the neutral source it was reviewed against, so
when that source moves the override is reported stale rather than silently
serving a superseded meaning.

An override can select a different declared mechanism. It can never add a tool,
MCP server, LSP server, hook or capability the kernel did not declare.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, Iterable, Mapping

from .validate import SourcePathError, ValidationIssue, confined_source, source_members

OVERRIDE_MANIFEST = "override.toml"

REQUIRED_KEYS = (
    "source",
    "source_paths",
    "reason",
    "strategy",
    "reviewed_against",
    "contracts_preserved",
    "capabilities_affected",
    "replacement",
)


@dataclass(frozen=True)
class OverrideSpec:
    root: Path
    source: str
    source_paths: tuple[Path, ...]
    reason: str
    strategy: str
    reviewed_against: str
    contracts_preserved: tuple[str, ...]
    capabilities_affected: tuple[str, ...]
    replacement: Path


class OverrideError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def source_digest(paths: Iterable[Path], repository_root: Path | None = None) -> str:
    """Digest a set of neutral source files, path and content, order-independently."""
    from .render import RenderError, digest_bytes

    ordered = sorted(paths, key=lambda item: item.as_posix())
    for path in ordered:
        try:
            confined_source(repository_root if repository_root is not None else path.parent, path)
        except SourcePathError as error:
            raise OverrideError(error.path, error.message) from error
    digest = hashlib.sha256()
    for path in ordered:
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        try:
            digest.update(digest_bytes(path, repository_root))
        except RenderError as error:
            raise OverrideError(path, str(error)) from error
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _strings(path: Path, table: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = table[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise OverrideError(path, f"{key} must be an array of strings")
    return tuple(value)


def load_override(manifest: Path) -> OverrideSpec:
    try:
        confined_source(manifest.parent, manifest)
    except SourcePathError as error:
        raise OverrideError(error.path, error.message) from error
    try:
        with manifest.open("rb") as handle:
            table = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise OverrideError(manifest, f"invalid TOML: {error}") from error
    except OSError as error:
        raise OverrideError(manifest, f"cannot read source: {error}") from error

    for key in REQUIRED_KEYS:
        if key not in table:
            raise OverrideError(manifest, f"override requires {key!r}")
    unknown = sorted(set(table) - set(REQUIRED_KEYS))
    if unknown:
        raise OverrideError(manifest, f"unknown override key(s): {', '.join(unknown)}")

    for key in ("source", "reason", "strategy", "reviewed_against", "replacement"):
        if not isinstance(table[key], str):
            raise OverrideError(manifest, f"{key} must be a string")

    return OverrideSpec(
        root=manifest.parent,
        source=table["source"],
        source_paths=tuple(Path(item) for item in _strings(manifest, table, "source_paths")),
        reason=table["reason"],
        strategy=table["strategy"],
        reviewed_against=table["reviewed_against"],
        contracts_preserved=_strings(manifest, table, "contracts_preserved"),
        capabilities_affected=_strings(manifest, table, "capabilities_affected"),
        replacement=Path(table["replacement"]),
    )


def load_overrides(path: Path) -> tuple[OverrideSpec, ...]:
    """Load every override manifest at or under ``path``, in path order."""
    root = Path(path)
    try:
        confined_source(root, root, allow_missing=True)
        if not root.exists():
            return ()
        members = source_members(root)
    except SourcePathError as error:
        raise OverrideError(error.path, error.message) from error
    if root / OVERRIDE_MANIFEST in members:
        return (load_override(root / OVERRIDE_MANIFEST),)
    manifests = [member for member in members if member.name == OVERRIDE_MANIFEST]
    return tuple(load_override(manifest) for manifest in manifests)


def validate_override(
    spec: OverrideSpec,
    declared_capabilities: AbstractSet[str],
    declared_contracts: AbstractSet[str] | None = None,
    repository_root: Path | None = None,
) -> list[ValidationIssue]:
    """Report every reason this override may not be applied."""
    issues: list[ValidationIssue] = []
    manifest = spec.root / OVERRIDE_MANIFEST
    base = Path(repository_root) if repository_root is not None else Path.cwd()

    replacement = spec.replacement
    if replacement.is_absolute() or ".." in replacement.parts:
        issues.append(
            ValidationIssue("override-escapes-directory", manifest, replacement.as_posix())
        )
    else:
        try:
            confined_source(spec.root, spec.root / replacement, allow_missing=True)
        except SourcePathError as error:
            issues.append(ValidationIssue("override-escapes-directory", error.path, error.message))
        else:
            if not (spec.root / replacement).is_file():
                issues.append(
                    ValidationIssue("override-missing-replacement", manifest, replacement.as_posix())
                )

    sources_valid = True
    for path in spec.source_paths:
        if path.is_absolute() or ".." in path.parts:
            issues.append(ValidationIssue("override-source-outside-repository", manifest, path.as_posix()))
            sources_valid = False
            continue
        try:
            confined_source(base, base / path, allow_missing=True)
        except SourcePathError as error:
            issues.append(ValidationIssue("unsafe-source-path", error.path, error.message))
            sources_valid = False
            continue
        if not (base / path).is_file():
            issues.append(ValidationIssue("override-missing-source", manifest, path.as_posix()))
            sources_valid = False
    if sources_valid:
        try:
            current = source_digest([base / path for path in spec.source_paths], base)
        except OverrideError as error:
            issues.append(ValidationIssue("unsafe-source-path", error.path, error.message))
            current = spec.reviewed_against
        if current != spec.reviewed_against:
            issues.append(ValidationIssue("stale-override", manifest, spec.source))

    escalated = [
        capability
        for capability in spec.capabilities_affected
        if capability not in declared_capabilities
    ]
    for capability in escalated:
        issues.append(ValidationIssue("override-capability-escalation", manifest, capability))

    if declared_contracts is not None:
        preserved = frozenset(spec.contracts_preserved)
        for contract in sorted(declared_contracts - preserved):
            issues.append(ValidationIssue("override-drops-contract", manifest, contract))
        for contract in sorted(preserved - declared_contracts):
            issues.append(ValidationIssue("override-unknown-contract", manifest, contract))

    return issues
