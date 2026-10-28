"""Routing text: the entry lines one host injects for a plugin with `[routing]`.

The text is derived at build time from the kernel's routing declaration and its
workflow frontmatter, so nothing in it is listed by hand. Kernels are
host-neutral, so the entry identity of each component kind on each host lives
here; a host absent from `IDENTITIES` delivers no routing text.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Mapping

from .adapter import HostAdapter
from .model import PluginSpec
from .templates import render_template

#: The most characters one plugin's routing text may hold on one host.
MAX_CHARACTERS = 9000
#: The entry plugin whose preamble adds the primary-entry facts.
ENTRY_PLUGIN = "daodan"
#: Categories a keyword term may not carry: they break, hide or reorder a line.
UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})

_CLAUDE_IDENTITIES = {
    "workflow": "/${plugin}:${workflow_name}",
    "skill": "${plugin}:${skill}",
    "role": "${plugin}:${role}",
}
#: Entry identity per host and component kind; None is a kind the host does not
#: register (Codex passes roles inline, docs/hosts.md "Component and entry mapping").
IDENTITIES: Mapping[str, Mapping[str, str | None]] = {
    "claude": _CLAUDE_IDENTITIES,
    "opencode": _CLAUDE_IDENTITIES,
    "codex": {"workflow": "${workflow_name}", "skill": "${skill}", "role": None},
}

_TEMPLATES = Path(__file__).resolve().parent
_CLAUSE = re.compile(r"(?:DO NOT )?TRIGGER WHEN:")
_POINTER = re.compile(r"\(use ([^()]*)\)")
_POINTER_NAME = re.compile(r"(?:/([a-z0-9][a-z0-9-]*):)?([a-z0-9][a-z0-9-]*)")
_LIST_SEPARATOR = re.compile(r"(, | or )")
_FIRST_SENTENCE = re.compile(r".*?[.!?](?=\s|$)")


def _identity(adapter: HostAdapter, plugin: str, kind: str, name: str) -> str | None:
    template = IDENTITIES[adapter.host][kind]
    if template is None:
        return None
    context = {"plugin": plugin, kind: name}
    if kind == "workflow":
        context["workflow_name"] = render_template(
            adapter.layout.get("workflow_name", "${workflow}"), {"plugin": plugin, "workflow": name}
        )
    return render_template(template, context)


def _description(plugin: PluginSpec, workflow_name: str) -> str:
    # Imported here, as catalogs.py does: render may import this module.
    from .render import _frontmatter, _read_text, _unquote

    workflow = next(item for item in plugin.workflows if item.name == workflow_name)
    meta, _ = _frontmatter(_read_text(plugin.root / workflow.entrypoint, plugin.root))
    return " ".join(_unquote(meta.get("description", "")).split())


def _clauses(description: str) -> tuple[str | None, str | None]:
    """The first TRIGGER WHEN and DO NOT TRIGGER WHEN conditions, each up to the next marker."""
    matches = list(_CLAUSE.finditer(description))
    found: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(description)
        found.setdefault(match.group(0), description[match.end():end].strip())
    return found.get("TRIGGER WHEN:"), found.get("DO NOT TRIGGER WHEN:")


def _pointer_identity(
    name: str, plugin: PluginSpec, adapter: HostAdapter, plugins: Mapping[str, PluginSpec]
) -> str | None:
    """A pointer name as a host identity, when it is a workflow of this or a required plugin."""
    match = _POINTER_NAME.fullmatch(name)
    if match is None:
        return None
    owner_name, workflow = match.group(1) or plugin.name, match.group(2)
    if owner_name == plugin.name:
        owner: PluginSpec | None = plugin
    elif owner_name in plugin.required_dependencies:
        owner = plugins.get(owner_name)
    else:
        return None
    if owner is None or workflow not in {item.name for item in owner.workflows}:
        return None
    return _identity(adapter, owner.name, "workflow", workflow)


def _exclusion(
    clause: str, plugin: PluginSpec, adapter: HostAdapter, plugins: Mapping[str, PluginSpec]
) -> str | None:
    """The clause with every pointer rewritten, or None when any pointer cannot be."""
    pointers = list(_POINTER.finditer(clause))
    if not pointers:
        return None
    parts: list[str] = []
    position = 0
    for match in pointers:
        pieces = _LIST_SEPARATOR.split(match.group(1))
        for index in range(0, len(pieces), 2):
            identity = _pointer_identity(pieces[index], plugin, adapter, plugins)
            if identity is None:
                return None
            pieces[index] = identity
        parts.append(f"{clause[position:match.start()]}(use {''.join(pieces)})")
        position = match.end()
    return "".join(parts) + clause[position:]


def _workflow_line(
    name: str, plugin: PluginSpec, adapter: HostAdapter, plugins: Mapping[str, PluginSpec]
) -> str:
    identity = _identity(adapter, plugin.name, "workflow", name)
    description = _description(plugin, name)
    trigger, clause = _clauses(description)
    if trigger is not None:
        text = f"TRIGGER WHEN: {trigger}"
    else:
        sentence = _FIRST_SENTENCE.match(description)
        text = sentence.group(0) if sentence else description
    exclusion = _exclusion(clause, plugin, adapter, plugins) if clause else None
    if exclusion is not None:
        text = f"{text} DO NOT TRIGGER WHEN: {exclusion}"
    return f"- `{identity}`: {text}" if text else f"- `{identity}`"


def _target_kind(plugin: PluginSpec, target: str) -> str:
    if target in {item.name for item in plugin.workflows}:
        return "workflow"
    if target in plugin.components.skills:
        return "skill"
    if target in plugin.components.roles:
        return "role"
    raise ValueError(f"{plugin.name}: routing target {target!r} is not a component of the plugin")


def _template(name: str, plugin: PluginSpec) -> str:
    return render_template((_TEMPLATES / name).read_text(encoding="utf-8"), {"plugin": plugin.name}).strip()


def routing_text(
    plugin: PluginSpec, adapter: HostAdapter, plugins: Mapping[str, PluginSpec]
) -> str | None:
    """One plugin's routing text for one host, or None when that host gets no line.

    `plugins` maps names to the other kernels, so a pointer to a required
    plugin's workflow resolves only when that workflow exists.
    """
    routing = plugin.routing
    if routing is None:
        return None
    for keyword in routing.keywords:
        for term in keyword.words:
            if any(unicodedata.category(char) in UNSAFE_CATEGORIES for char in term):
                raise ValueError(
                    f"{plugin.name}: routing term {term!r} carries a control, format or "
                    "line separator character"
                )
    if adapter.host not in IDENTITIES:
        return None
    lines: list[str] = []
    if routing.workflows:
        lines.extend(_workflow_line(workflow.name, plugin, adapter, plugins)
                     for workflow in sorted(plugin.workflows, key=lambda item: item.name))
    for keyword in routing.keywords:
        kind = _target_kind(plugin, keyword.target)
        identity = _identity(adapter, plugin.name, kind, keyword.target)
        if identity is not None:
            agent = " (agent to dispatch)" if kind == "role" else ""
            lines.append(f"- {', '.join(keyword.words)}: `{identity}`{agent}")
    if not lines:
        return None
    preamble = [_template("routing_preamble.md", plugin)]
    if plugin.name == ENTRY_PLUGIN:
        preamble.append(_template("routing_daodan.md", plugin))
    text = "\n\n".join([*preamble, "\n".join(lines)]) + "\n"
    if len(text) > MAX_CHARACTERS:
        raise ValueError(
            f"{plugin.name}: routing text for {adapter.host} holds {len(text)} characters, "
            f"more than {MAX_CHARACTERS}"
        )
    return text
