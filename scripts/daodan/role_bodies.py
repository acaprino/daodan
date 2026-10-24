"""Resolve canonical role bodies without inventing detection instructions."""
from __future__ import annotations

import hashlib
import re

from .composition import assemble_body
from .reviewer_catalog import _parse_role, _triggers
from .validate import confined_source

IDENTITY = re.compile(r"[a-z][a-z0-9-]*:[a-z][a-z0-9-]*\Z")
INDEPENDENT = frozenset({"premise-auditor", "finding-verifier", "review-critic"})


class RoleBodyError(ValueError):
    pass


def resolve_role(registry: dict, owner: str, role: str) -> dict:
    """Flatten a declared DAG in first occurrence order; retain provider roots."""
    parts, hashes, seen = [], {}, set()

    def visit(package, name, ancestors):
        identity = f"{package}:{name}"
        if not IDENTITY.fullmatch(identity):
            raise RoleBodyError(f"invalid role identity: {identity}")
        plugin = registry.get(package)
        if plugin is None or name not in plugin.components.roles:
            raise RoleBodyError(f"unregistered role: {identity}")
        if identity in ancestors:
            raise RoleBodyError(f"composition cycle: {' -> '.join((*ancestors, identity))}")
        if ancestors and name in INDEPENDENT:
            raise RoleBodyError(f"independent process role cannot be composed: {identity}")
        members = dict(plugin.reviewer_compositions).get(name)
        if members is not None:
            if len(members) != len(set(members)):
                raise RoleBodyError(f"duplicate direct composition member: {identity}")
            if not members:
                raise RoleBodyError(f"empty composition: {identity}")
            for member in members:
                if not IDENTITY.fullmatch(member):
                    raise RoleBodyError(f"invalid composition member: {member}")
                provider, child = member.split(":")
                if provider != package and provider not in plugin.required_dependencies:
                    raise RoleBodyError(f"undeclared composition provider: {identity} -> {provider}")
                visit(provider, child, (*ancestors, identity))
        elif identity not in seen:
            path = confined_source(plugin.root, plugin.root / "roles" / f"{name}.md")
            text = path.read_text(encoding="utf-8")
            metadata, body = _parse_role(text)
            parts.append({"id": identity, "owner": package, "source": f"roles/{name}.md",
                          "metadata": metadata, "body": body, "text": text,
                          "root_reference": "${CLAUDE_PLUGIN_ROOT}" if package == owner
                                            else f"<{package}-plugin-root>"})
            hashes[f"{package}/roles/{name}.md"] = "sha256:" + hashlib.sha256(text.encode()).hexdigest()
            seen.add(identity)

    visit(owner, role, ())
    composed = role in dict(registry[owner].reviewer_compositions)
    if composed:
        activation = [when for p in parts
                      if (when := _triggers(p["metadata"].get("description", ""))[0])]
        tools = [p["metadata"].get("tools") for p in parts]
        # Member triggers feed the reviewer catalog only; in the host description they
        # broke Pi's 1024-character ceiling and loaded every member's text each session.
        metadata = {"name": role, "model": "inherit", "color": "blue",
                    "description": "Composed review of "
                    + ", ".join(dict(registry[owner].reviewer_compositions)[role])
                    + ". TRIGGER WHEN: a review coordinator dispatches this composition."
                    + " DO NOT TRIGGER WHEN: no member applies; missing required input remains a coverage gap."}
        # Absence of a restriction means unrestricted, not an empty permission set.
        if all(t is not None for t in tools):
            metadata["tools"] = ", ".join(dict.fromkeys(t.strip().strip("\"'") for row in tools
                                                      for t in row.strip("[] ").split(",") if t.strip()))
        for part in parts:
            if part["metadata"].get("model", "inherit") != "inherit":
                raise RoleBodyError(f"composition requires compatible inherited models: {part['id']}")
    else:
        metadata = parts[0]["metadata"]
    return {"metadata": metadata, "parts": parts, "members": [p["id"] for p in parts],
            "source_hashes": hashes, "composed": composed,
            "trigger_when": "any member applies: " + "; ".join(activation) + "." if composed else None}


def role_text(resolved: dict) -> str:
    if not resolved["composed"]:
        return resolved["parts"][0]["text"]
    metadata = resolved["metadata"]
    header = "---\n" + "\n".join(
        f"{key}: >\n  {value}" if key == "description" else f"{key}: {value}"
        for key, value in metadata.items()) + "\n---\n\n"
    from .render import _inline_role_scope
    parts = [{**part, "operation_scope": _inline_role_scope(part["metadata"])}
             for part in resolved["parts"]]
    return header + assemble_body(parts, [])
