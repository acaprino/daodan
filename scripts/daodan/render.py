"""Deterministic rendering and transactional publication of host packages.

Two properties are load-bearing. **Equal inputs produce equal bytes**, so a
rebuild that changes nothing produces no diff and a drift check is meaningful.
And **a partial host tree is never written**: everything renders under a
temporary directory beside the live tree, every validator runs there, and only
then does one rename make it live.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import tomllib
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .adapter import HostAdapter, resolve_support, select_coordination
from .catalogs import OWNER
from .model import PluginSpec, WorkflowSpec
from .overrides import OverrideSpec
from .provenance import ADAPTER_VERSION, write_provenance
from .templates import render_path, render_template
from .validate import MCP_CAPABILITY, SourcePathError, confined_source, source_members

#: The strategy of a host that starts a plugin-declared MCP server from a
#: manifest at the package root, and the strategy of a host that does not and
#: must be told by the user instead.
MCP_MANIFEST_STRATEGY = "mcp-manifest"
MCP_REGISTRATION_STRATEGY = "mcp-registration"
MCP_MANIFEST = ".mcp.json"

NUL = bytes([0])


def is_text(raw: bytes) -> bool:
    """Whether this content is text, asked of the content itself.

    Deciding by extension was a whitelist that kept being incomplete: the helper
    scripts a skill ships (`.py`, `.js`, `.sh`) fell outside it, were copied
    byte-for-byte, and carried whatever line endings the checkout happened to
    have. CI then reported drift on exactly those four plugins.
    """
    if NUL in raw:
        return False
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True

#: Build artifacts are never content. A kernel that has been run from carries
#: them, and copying them would publish a local machine's state.
IGNORED_DIRECTORIES: frozenset[str] = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache"})
IGNORED_SUFFIXES: frozenset[str] = frozenset({".pyc", ".pyo", ".orig", ".rej"})


def _is_artifact(relative: Path) -> bool:
    return (
        any(part in IGNORED_DIRECTORIES for part in relative.parts)
        or relative.suffix in IGNORED_SUFFIXES
    )

DEFAULT_MANIFEST_TEMPLATE = """{
  "description": "${description}",
  "license": "${license}",
  "name": "${plugin}",
  "version": "${version}"
}
"""


class RenderError(RuntimeError):
    """Raised before a generated tree becomes live."""


def _source(path: Path, root: Path | None = None, *, allow_missing: bool = False) -> Path:
    try:
        return confined_source(root if root is not None else path.parent, path,
                               allow_missing=allow_missing)
    except SourcePathError as error:
        raise RenderError(str(error)) from error


def _source_members(root: Path) -> tuple[Path, ...]:
    try:
        return source_members(root)
    except SourcePathError as error:
        raise RenderError(str(error)) from error


def _read_text(path: Path, root: Path | None = None) -> str:
    try:
        return _source(path, root).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RenderError(f"cannot read source text {path}: {error}") from error


@dataclass(frozen=True)
class RenderResult:
    plugin: str
    host: str
    staging_root: Path
    files: tuple[Path, ...]
    core_digest: str
    harness_strategies: tuple[tuple[str, str], ...]
    overrides: tuple[str, ...]


def tree_digest(root: Path) -> str:
    """Digest a whole tree by relative path and content."""
    digest = hashlib.sha256()
    for path in sorted(
        _source_members(Path(root)),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        try:
            digest.update(_source(path, root).read_bytes())
        except OSError as error:
            raise RenderError(f"cannot read source {path}: {error}") from error
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _kernel_files(plugin: PluginSpec) -> list[Path]:
    return sorted(
        (
            path
            for path in _source_members(plugin.root)
            if not _is_artifact(path.relative_to(plugin.root))
        ),
        key=lambda item: item.as_posix(),
    )


def digest_bytes(path: Path, root: Path | None = None) -> bytes:
    """Content for hashing, with text line endings normalized to LF.

    A digest over raw bytes is not reproducible across platforms: the same kernel
    checked out on Windows carries CRLF and on Linux LF, so one source produced
    two digests and CI reported drift against a tree that was in fact identical.
    Normalizing here makes the digest a property of the content rather than of
    the checkout.
    """
    try:
        raw = _source(path, root).read_bytes()
    except OSError as error:
        raise RenderError(f"cannot read source {path}: {error}") from error
    if not is_text(raw):
        return raw
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _kernel_digest(plugin: PluginSpec, members: Sequence[Path] | None = None) -> str:
    digest = hashlib.sha256()
    for path in _kernel_files(plugin) if members is None else members:
        digest.update(path.relative_to(plugin.root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_bytes(path, plugin.root))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _write_text(destination: Path, content: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    destination.write_bytes(normalized.encode("utf-8"))


def _copy(source: Path, destination: Path, source_root: Path | None = None) -> None:
    raw = digest_bytes(source, source_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if is_text(raw):
        _write_text(destination, raw.decode("utf-8"))
    else:
        destination.write_bytes(raw)


#: Neutral role tools, mapped onto each host's vocabulary. The kernel never names
#: a host tool, so these tables are where a Claude-shaped agent becomes a
#: Copilot- or OpenCode-shaped one. They sit together so that a tool added to one
#: is visibly missing from the other.
COPILOT_TOOLS = {
    "Read": "search",
    "Glob": "search",
    "Grep": "search",
    "Write": "edit",
    "Edit": "edit",
    "NotebookEdit": "edit",
    "Bash": "runCommands",
    "WebFetch": "fetch",
    "WebSearch": "fetch",
    "Agent": "agent",
    "Task": "agent",
}

#: OpenCode V2 permission actions. A V2 permission list is ordered and the last
#: matching rule wins.
OPENCODE_PERMISSIONS = {
    "Read": "read",
    "Glob": "glob",
    "Grep": "grep",
    "Write": "edit",
    "Edit": "edit",
    "NotebookEdit": "edit",
    "Bash": "shell",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
    "Agent": "subagent",
    "Task": "subagent",
}

#: The marker the OpenCode loader replaces with the installed package's absolute
#: path. A rule scoped to it is how a role reads its own skill references, which
#: live in OpenCode's package cache, outside the project.
OPENCODE_PACKAGE_ROOT = "<package-root>"


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a Markdown body from its frontmatter, flattening multiline scalars."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return {}, normalized
    end = normalized.find("\n---\n", 4)
    if end == -1:
        return {}, normalized
    block = normalized[4:end]
    body = normalized[end + 5 :]

    meta: dict[str, str] = {}
    key: str | None = None
    for line in block.split("\n"):
        if line[:1] not in {" ", "\t"} and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            meta[key] = value.strip()
        elif key is not None and line.strip():
            meta[key] = f"{meta[key]} {line.strip()}".strip()
    for name, value in meta.items():
        if value.startswith(">") or value.startswith("|"):
            meta[name] = value[1:].strip()
    return meta, body


def _one_line(value: str) -> str:
    """Frontmatter scalars are rendered inline, so they may not carry breaks or quotes."""
    return " ".join(value.replace("'", "").split())


def _declared_tools(value: str) -> list[str]:
    return [item.strip() for item in value.strip("[] ").split(",") if item.strip()]


def opencode_permissions(tools: str) -> list[dict[str, str]]:
    """A role's `tools` line as an OpenCode V2 permission list.

    A role with no `tools` line declares no restriction, so it gets only the
    package allowance below, and the loader appends that to V2's defaults
    rather than replacing them. A list that starts with a deny-all is a
    restriction, and the loader puts it in place of the defaults: everything
    denied first, each declared tool allowed after it in first-seen order, then
    `skill`, because every role may load a skill. Both kinds end with an
    `external_directory` allowance scoped to the package, because the package
    lives in OpenCode's cache, outside every project, and without it a role is
    refused (or, under the defaults, asked about) the very references its body
    tells it to read. That allowance is never `*`.
    """
    package = {
        "action": "external_directory",
        "resource": f"{OPENCODE_PACKAGE_ROOT}/**",
        "effect": "allow",
    }
    declared = _declared_tools(tools)
    if not declared:
        return [package]
    rules = [{"action": "*", "resource": "*", "effect": "deny"}]
    seen: set[str] = set()
    for item in declared:
        action = OPENCODE_PERMISSIONS.get(item)
        if action and action not in seen:
            seen.add(action)
            rules.append({"action": action, "resource": "*", "effect": "allow"})
    rules.append({"action": "skill", "resource": "*", "effect": "allow"})
    rules.append(package)
    return rules


def _yaml_rules(rules: Sequence[Mapping[str, str]]) -> str:
    """An inline YAML list for frontmatter, empty when there is nothing to list."""
    if not rules:
        return " []"
    lines = [""]
    for rule in rules:
        lines.append(f"  - action: \"{rule['action']}\"")
        lines.append(f"    resource: \"{rule['resource']}\"")
        lines.append(f"    effect: {rule['effect']}")
    return "\n".join(lines)


ROLE_OPERATIONS = {
    "Read": "read files",
    "Glob": "discover file paths",
    "Grep": "search file contents",
    "Write": "create or overwrite files",
    "Edit": "edit existing files",
    "NotebookEdit": "edit notebooks",
    "Bash": "execute shell commands",
    "WebFetch": "retrieve web pages",
    "WebSearch": "search the web",
    "Agent": "dispatch declared workers",
    "Task": "dispatch declared workers",
}


def _inline_role_scope(meta: Mapping[str, str]) -> str:
    """Preserve an inline role's neutral allowlist without foreign frontmatter."""
    if "tools" not in meta:
        return "This role declares no additional tool restriction; retain the active session's permissions.\n\n"
    declared = [item.strip().strip("\"'") for item in _declared_tools(meta["tools"])]
    unknown = sorted(set(declared) - ROLE_OPERATIONS.keys())
    if unknown:
        raise RenderError(f"inline role: unbound tool(s): {', '.join(unknown)}")
    operations = list(dict.fromkeys(ROLE_OPERATIONS[item] for item in declared))
    scope = "; ".join(operations) if operations else "no file, shell, web or worker operations"
    return (f"Declared role operation allowlist: {scope}. Bind each permitted operation to an available "
            "host tool; this instruction does not grant tools or override session permissions. "
            "Do not use operations omitted from this list.\n\n")


def _copilot_tools(value: str | None) -> str | None:
    """Preserve an omitted restriction; reject an explicit unbound tool."""
    if value is None:
        return None
    declared = [item.strip().strip("\"'") for item in _declared_tools(value)]
    unknown = sorted(set(declared) - COPILOT_TOOLS.keys())
    if unknown:
        raise RenderError(f"copilot: unbound role tool(s): {', '.join(unknown)}")
    mapped = list(dict.fromkeys(COPILOT_TOOLS[item] for item in declared))
    return ", ".join(f"'{item}'" for item in mapped)


#: The two placeholders a kernel may use that are Claude's vocabulary rather
#: than the marketplace's. The bundled-path linter requires the first, because
#: it is the form that survives installation on Claude; each adapter's layout
#: says what it becomes on that host, and how the host is told to read it.
PLUGIN_ROOT_PLACEHOLDER = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}")
ARGUMENTS_PLACEHOLDER = re.compile(r"\$ARGUMENTS\b")
DEFAULT_PLUGIN_ROOT_REFERENCE = "${CLAUDE_PLUGIN_ROOT}"
DEFAULT_ARGUMENTS_REFERENCE = "$ARGUMENTS"
GENERATED = "<!-- Generated by the Daodan compiler for {host}. Edit the kernel, never this file. -->"


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _insert_after_frontmatter(text: str, block: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            head = text[: end + 5]
            return head + "\n" + block + text[end + 5 :].lstrip("\n")
    return block + text


def _host_text(
    text: str,
    adapter: HostAdapter,
    hint: str | None = None,
    extra_notes: Sequence[str] = (),
    operational_binding: str = "",
) -> str:
    """Adapt placeholders and bind execution without rewriting domain examples.

    `${CLAUDE_PLUGIN_ROOT}` and `$ARGUMENTS` are what a kernel writes, because
    they are what Claude expands. Neither is defined on the other hosts, so a
    role that says "run ${CLAUDE_PLUGIN_ROOT}/skills/x/scripts/y.py" ships an
    instruction Codex cannot follow. The adapter layout names the host's own
    reference for each, and a note explaining it is inserted once, after the
    frontmatter, in every file that uses it. Claude's layout maps each
    placeholder onto itself and needs no placeholder note. The execution binding
    is independent of placeholder rewriting and is added on every host.
    """
    layout = adapter.layout
    root_reference = layout.get("plugin_root_reference", DEFAULT_PLUGIN_ROOT_REFERENCE)
    arguments_reference = layout.get("arguments_reference", DEFAULT_ARGUMENTS_REFERENCE)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    rewritten = PLUGIN_ROOT_PLACEHOLDER.sub(lambda _: root_reference, normalized)
    rewritten = ARGUMENTS_PLACEHOLDER.sub(lambda _: arguments_reference, rewritten)

    notes: list[str] = []
    root_note = layout.get("plugin_root_note")
    mentions_root = root_reference in rewritten or any(
        root_reference in note for note in extra_notes
    )
    if root_note and mentions_root:
        notes.append(root_note)
    arguments_note = layout.get("arguments_note")
    if arguments_note and (hint or arguments_reference in rewritten):
        prefix = f"Arguments: `{hint}`. " if hint else ""
        notes.append(prefix + arguments_note)
    notes.extend(extra_notes)
    block = "\n".join(f"> {note}" for note in notes)
    if block:
        block += "\n\n"
    if operational_binding:
        block += operational_binding.rstrip() + "\n\n"
    return _insert_after_frontmatter(rewritten, block) if block else rewritten


def _write_markdown(
    destination: Path,
    text: str,
    adapter: HostAdapter,
    hint: str | None = None,
    extra_notes: Sequence[str] = (),
    operational_binding: str = "",
) -> None:
    rendered = _host_text(text, adapter, hint, extra_notes, operational_binding)
    _write_text(destination, rendered.rstrip() + "\n")


def _operational_binding(adapter: HostAdapter, adapters_root: Path | None) -> str:
    """One shared execution contract and the active host's actual binding."""
    root = Path(adapters_root) if adapters_root is not None else Path(__file__).resolve().parents[2] / "adapters"
    common = _read_text(root / "operational-binding.md.tmpl", root)
    specific = _template(root, adapter.host, "operational-binding.md.tmpl")
    if specific is None:
        raise RenderError(f"{adapter.host}: missing operational host binding")
    return render_template(common, {"host": adapter.host, "body": specific.strip()})


def _host_arguments(server_args: Sequence[str], adapter: HostAdapter) -> list[str]:
    root_reference = adapter.layout.get("plugin_root_reference", DEFAULT_PLUGIN_ROOT_REFERENCE)
    return [PLUGIN_ROOT_PLACEHOLDER.sub(lambda _: root_reference, arg) for arg in server_args]


def _mcp_manifest(plugin: PluginSpec, adapter: HostAdapter) -> str:
    """The package-root manifest a host that starts declared servers reads."""
    servers = {
        server.name: {"command": server.command, "args": _host_arguments(server.args, adapter)}
        for server in plugin.mcp_servers
    }
    return json.dumps({"mcpServers": servers}, indent=2) + "\n"


def _mcp_registration_notes(plugin: PluginSpec, adapter: HostAdapter) -> tuple[str, ...]:
    """One note per server for a host that does not start declared servers itself."""
    hint = adapter.layout.get("mcp_registration_hint")
    notes = []
    for server in plugin.mcp_servers:
        command = " ".join([server.command, *_host_arguments(server.args, adapter)])
        note = (
            f"This plugin declares an MCP server, `{server.name}`, started with `{command}`. "
            "This host does not start a plugin-declared MCP server on its own. "
            "Before calling this server's tools, register that command under that name "
            "in the host's MCP configuration and verify the connection."
        )
        if hint:
            note = f"{note} {hint}"
        notes.append(note)
    return tuple(notes)


def _mcp_rendering(
    plugin: PluginSpec, adapter: HostAdapter, staging_root: Path
) -> tuple[str, ...]:
    """Write the manifest where the host starts servers; return the notes where it does not."""
    if not plugin.mcp_servers:
        return ()
    binding = adapter.bindings.get(MCP_CAPABILITY)
    strategy = binding.strategy if binding is not None else "none"
    if strategy == MCP_MANIFEST_STRATEGY:
        _write_text(staging_root / MCP_MANIFEST, _mcp_manifest(plugin, adapter))
        return ()
    if strategy == MCP_REGISTRATION_STRATEGY:
        return _mcp_registration_notes(plugin, adapter)
    raise RenderError(f"{adapter.host}: no MCP server strategy for {plugin.name} ({strategy})")


def _workflow_name(workflow: str, adapter: HostAdapter, context: Mapping[str, str]) -> str:
    """The name a host registers a workflow under.

    Defaults to the kernel name. A host that renders workflows into the same
    namespace as skills (Codex does) sets `workflow_name` in its layout so the
    registered name carries the same suffix as the directory it lands in;
    otherwise a skill and a workflow that share a kernel name collide by name
    even though they no longer collide on disk.
    """
    template = adapter.layout.get("workflow_name", "${workflow}")
    return render_template(template, {**context, "workflow": workflow})


def _workflow_frontmatter(
    meta: Mapping[str, str], name: str, adapter: HostAdapter, hint: str | None
) -> str | None:
    """The fields this host actually reads for a workflow entry."""
    keys = adapter.layout.get("workflow_frontmatter")
    if not keys:
        return None
    lines = ["---"]
    for key in (item.strip() for item in keys.split(",") if item.strip()):
        if key == "name":
            lines.append(f"name: {name}")
        elif key == "description":
            lines.append(f"description: '{_one_line(meta.get('description', ''))}'")
        elif key == "argument-hint":
            if hint:
                lines.append(f"argument-hint: '{_one_line(hint)}'")
        else:
            raise RenderError(f"{adapter.host}: unknown workflow_frontmatter key {key!r}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def _flat_workflow(
    source: Path, name: str, adapter: HostAdapter, source_root: Path | None = None
) -> tuple[str, str | None]:
    """Render a workflow that does not fan out: the body as it is, under host frontmatter.

    Claude commands carry `description` and `argument-hint`; a Codex skill wants
    `name` and `description`, and a Copilot prompt wants all three. The layout's
    `workflow_frontmatter` lists what the host reads, in order. Without it the
    kernel file is copied verbatim, which is what Claude gets. `name` is the
    host-registered name from `_workflow_name`, not necessarily the kernel's.
    """
    text = _read_text(source, source_root)
    meta, body = _frontmatter(text)
    hint = _unquote(meta.get("argument-hint", "")).strip() or None
    frontmatter = _workflow_frontmatter(meta, name, adapter, hint)
    if frontmatter is None:
        return text, hint
    rendered = (
        frontmatter
        + GENERATED.format(host=adapter.host)
        + "\n\n"
        + body.strip()
        + "\n"
    )
    return rendered, hint


def _coordinator_tools(plugin: PluginSpec, adapter: HostAdapter) -> str:
    """The host tools a coordinator needs, derived from what the plugin requires.

    A coordinator that writes run state, runs a detection script and publishes
    a mirror needs more than a search tool. Every required capability whose
    binding names a host tool contributes it; reading and dispatching are
    always included because every coordinator does both.
    """
    names: set[str] = set()
    for capability in ("repository.read", "roles.dispatch", *plugin.capabilities.required):
        binding = adapter.bindings.get(capability)
        if binding is not None and binding.value:
            names.add(binding.value)
    if adapter.host == "copilot":
        # An explicit tools list also filters MCP. Keep the allowance scoped to
        # plugin-declared servers; GitHub's agent schema accepts server/*.
        names.update(f"{server.name}/*" for server in plugin.mcp_servers)
    return ", ".join(f"'{item}'" for item in sorted(names))


CONCURRENCY_WORDS = {
    "preferred": "in parallel where the host allows",
    "required": "in parallel",
    "forbidden": "one at a time",
}


def _names(items) -> str:
    quoted = [f"`{item}`" for item in items]
    if len(quoted) <= 1:
        return "".join(quoted)
    return ", ".join(quoted[:-1]) + " and " + quoted[-1]


def _dispatch_plan(workflow: WorkflowSpec, role_ids: Mapping[str, str] | None = None) -> str:
    """The phase graph as dispatch instructions, one numbered line per phase.

    The harness header used to say "dispatch the selected roles, once each",
    which is right for a wave of reviewers and wrong for a workflow that fans
    out one worker per partition across three waves. The plan says, per phase,
    how many workers, in what context, behind which barrier and after what.
    """
    lines = []
    role_ids = role_ids or {}
    for number, phase in enumerate(workflow.phases, 1):
        clauses = []
        isolated = phase.isolation == "required"
        if phase.fanout_from:
            unit = f"one `{role_ids.get(phase.role, phase.role)}`" if phase.role else "one worker"
            binding = (
                ""
                if phase.role
                else ", each bound to the role the selection names (any role this plugin declares)"
            )
            context = "each in its own isolated context" if isolated else "in the orchestrating context"
            clauses.append(
                f"{unit} per item of `{phase.fanout_from}`{binding}, {context}, "
                f"{CONCURRENCY_WORDS[phase.concurrency]}"
            )
        elif phase.fanout:
            references = (reference.partition(":")[2] or reference for reference in phase.fanout)
            roles = sorted(role_ids.get(reference, reference) for reference in references)
            context = "each in its own isolated context" if isolated else "in the orchestrating context"
            clauses.append(
                f"{_names(roles)}, once each, {context}, {CONCURRENCY_WORDS[phase.concurrency]}"
            )
        elif phase.role:
            context = "in an isolated context" if isolated else "in the orchestrating context"
            clauses.append(f"one `{role_ids.get(phase.role, phase.role)}` {context}")
        else:
            clauses.append("runs in the orchestrating context")
        if phase.fanout or phase.fanout_from:
            clauses.append(f"barrier `{phase.join or 'all-delivered'}`")
        if phase.needs:
            clauses.append("needs " + ", ".join(f"`{item}`" for item in phase.needs))
        if phase.consumes:
            clauses.append("consumes " + ", ".join(f"`{item}`" for item in phase.consumes))
        if phase.produces:
            clauses.append("produces " + ", ".join(f"`{item}`" for item in phase.produces))
        lines.append(f"{number}. `{phase.id}`: " + "; ".join(clauses) + ".")
    return "\n".join(lines)


def _template(adapters_root: Path | None, host: str, name: str | None) -> str | None:
    if adapters_root is None or not name:
        return None
    candidate = Path(adapters_root) / host / "templates" / name
    _source(candidate, Path(adapters_root) / host / "templates", allow_missing=True)
    return _read_text(candidate, Path(adapters_root) / host / "templates") if candidate.is_file() else None


def _manifest_template(adapter: HostAdapter, adapters_root: Path | None) -> str:
    if adapters_root is not None:
        candidate = Path(adapters_root) / adapter.host / "templates" / "plugin.json.tmpl"
        _source(candidate, Path(adapters_root) / adapter.host / "templates", allow_missing=True)
        if candidate.is_file():
            return _read_text(candidate, Path(adapters_root) / adapter.host / "templates")
    return DEFAULT_MANIFEST_TEMPLATE


def _package_context(plugin: PluginSpec, host: str) -> dict[str, str]:
    """One substitution context for rendered paths and their registrations."""
    return {
        "plugin": plugin.name,
        "version": plugin.version,
        "description": plugin.description,
        "license": plugin.license,
        "host": host,
        "adapter_version": ADAPTER_VERSION,
        "author": OWNER["name"],
    }


def render_plugin(
    plugin: PluginSpec,
    adapter: HostAdapter,
    destination: Path,
    overrides: Sequence[OverrideSpec] = (),
    adapters_root: Path | None = None,
    plugin_registry: Mapping[str, PluginSpec] | None = None,
) -> RenderResult:
    """Render one neutral plugin into one host's package layout.

    ``destination`` is a staging root: this function never touches live output.
    """
    support = resolve_support(plugin, adapter)
    if support.state == "unsupported":
        raise RenderError(
            f"{adapter.host}: {plugin.name} is unsupported "
            f"(missing: {', '.join(support.missing_capabilities) or 'no viable coordination strategy'})"
        )

    kernel_files = _kernel_files(plugin)

    staging_root = Path(destination)
    staging_root.mkdir(parents=True, exist_ok=True)

    context = _package_context(plugin, adapter.host)

    replacements = {spec.source: spec for spec in overrides}
    applied: list[str] = []

    # A host with no per-plugin manifest declares no `plugin_manifest` path.
    # Pi is the case: it installs a package and reads one manifest at its root,
    # so a per-plugin file would ship as something nothing reads.
    manifest_layout = adapter.layout.get("plugin_manifest")
    if manifest_layout:
        manifest = render_template(_manifest_template(adapter, adapters_root), context)
        _write_text(staging_root / render_path(manifest_layout, context), manifest)

    # A declared MCP server becomes a package-root manifest on a host that
    # starts it, and a note on every workflow of the plugin on a host that
    # needs the user to register it.
    mcp_notes = _mcp_rendering(plugin, adapter, staging_root)
    operational_binding = _operational_binding(adapter, adapters_root)

    def markdown(destination: Path, text: str, hint: str | None = None,
                 notes: Sequence[str] = ()) -> None:
        _write_markdown(destination, text, adapter, hint, notes, operational_binding)

    def resource(source: Path, destination: Path, source_root: Path) -> None:
        if source.suffix.lower() == ".md":
            markdown(destination, _read_text(source, source_root))
        else:
            _copy(source, destination, source_root)

    for exported in plugin.contract_exports:
        resource(plugin.root / exported, staging_root / exported, plugin.root)

    for skill in plugin.components.skills:
        source_directory = plugin.root / "skills" / skill
        target = staging_root / render_path(adapter.layout["skills"], {**context, "skill": skill})
        for path in _source_members(source_directory):
            relative = path.relative_to(source_directory)
            if _is_artifact(relative):
                continue
            destination = target if relative.as_posix() == "SKILL.md" else target.parent / relative
            if path.suffix == ".md":
                markdown(destination, _read_text(path, source_directory))
            else:
                _copy(path, destination, source_directory)

    if plugin.name == "skill-catalog":
        from .skill_catalog import declared_catalog
        registry = dict(plugin_registry or {})
        if not registry:
            from .load import load_plugin
            registry = {p.parent.name: load_plugin(p.parent)
                        for p in sorted(plugin.root.parent.glob("*/plugin.toml"))}
        reference = staging_root / "skills/skill-catalog/references"
        _write_text(reference / "catalog.json", json.dumps(
            declared_catalog(registry), sort_keys=True, indent=2, ensure_ascii=False) + "\n")
        inventory = _template(adapters_root, adapter.host, "skill-inventory.md.tmpl")
        if inventory is None:
            raise RenderError(f"{adapter.host}: missing skill inventory binding")
        markdown(reference / "host-inventory.md", inventory)

    for role in plugin.components.roles:
        target = staging_root / render_path(adapter.layout["roles"], {**context, "role": role})
        override = replacements.get(f"role:{role}")
        if override is not None:
            markdown(target, _read_text(override.root / override.replacement, override.root))
            applied.append(override.source)
        else:
            source = plugin.root / "roles" / f"{role}.md"
            role_template = _template(
                adapters_root, adapter.host, adapter.layout.get("role_template")
            )
            if role_template is None:
                markdown(target, _read_text(source, plugin.root))
            else:
                meta, body = _frontmatter(_read_text(source, plugin.root))
                copilot_tools = _copilot_tools(meta.get("tools")) if adapter.host == "copilot" else None
                markdown(
                    target,
                    render_template(
                        role_template,
                        {
                            **context,
                            "name": meta.get("name", role),
                            "description": _one_line(meta.get("description", "")),
                            "tools": "" if copilot_tools is None else f"tools: [{copilot_tools}]",
                            "permissions": _yaml_rules(
                                opencode_permissions(meta.get("tools", ""))
                            ),
                            "body": (_inline_role_scope(meta) if adapter.host in {"codex", "pi"} else "")
                                    + body.strip() + "\n",
                        },
                    ),
                )

    for policy in plugin.components.policies:
        _copy(
            plugin.root / "policies" / f"{policy}.toml",
            staging_root / "policies" / f"{policy}.toml",
            plugin.root,
        )
        # A policy is declared neutrally and enforced per host. Where this host
        # ships an implementation of it, that implementation travels with the
        # package: the policy TOML says what must hold, the adapter file is how
        # this host makes it hold.
        if adapters_root is not None:
            implementation = _policy_implementation(adapters_root, adapter.host, policy)
            if implementation is not None:
                for item in _source_members(implementation):
                    if not _is_artifact(item.relative_to(implementation)):
                        resource(
                            item,
                            staging_root / "policies" / policy / item.relative_to(implementation),
                            implementation,
                        )

    strategies: list[tuple[str, str]] = []
    for workflow in plugin.workflows:
        strategy = select_coordination(workflow, adapter)
        if strategy is None:
            raise RenderError(f"{adapter.host}: no coordination strategy for {workflow.name}")
        strategies.append((workflow.name, strategy.name))
        target = staging_root / render_path(
            adapter.layout["workflows"], {**context, "workflow": workflow.name}
        )
        override = replacements.get(f"workflow:{workflow.name}")
        dispatches = (bool(workflow.dispatch.roles) or workflow.dispatch.inline_workers
                      or any(phase.role or phase.fanout or phase.fanout_from for phase in workflow.phases))
        source = plugin.root / workflow.entrypoint
        if override is not None:
            markdown(target, _read_text(override.root / override.replacement, override.root), notes=mcp_notes)
            applied.append(override.source)
        elif dispatches:
            role_ids, body_bindings = _dispatch_bindings(
                plugin, workflow, strategy, adapter, staging_root, plugin_registry, operational_binding
            )
            harness = _harness_context(
                plugin, workflow, strategy, adapter, source, context, role_ids, body_bindings
            )
            hint = harness.pop("hint")
            team_template = _template(
                adapters_root, adapter.host, adapter.layout.get("team_workflow_template")
            )
            if team_template is not None:
                rendered = render_template(team_template, harness)
                if not rendered.startswith("---\n"):
                    meta, _ = _frontmatter(_read_text(source, plugin.root))
                    frontmatter = _workflow_frontmatter(meta, harness["workflow_name"], adapter, hint)
                    if frontmatter is None:
                        raise RenderError(f"{adapter.host}: workflow handoff has no host frontmatter")
                    rendered = frontmatter + rendered
                markdown(target, rendered, hint, mcp_notes)
            else:
                rendered, hint = _flat_workflow(source, harness["workflow_name"], adapter, plugin.root)
                markdown(target, rendered, hint, mcp_notes)
            coordinator_template = _template(
                adapters_root, adapter.host, adapter.layout.get("coordinator_template")
            )
            if coordinator_template is not None:
                coordinator = staging_root / render_path(
                    adapter.layout["coordinators"], {**context, "workflow": workflow.name}
                )
                markdown(coordinator, render_template(coordinator_template, harness), hint, mcp_notes)
        else:
            name = _workflow_name(workflow.name, adapter, context)
            rendered, hint = _flat_workflow(source, name, adapter, plugin.root)
            markdown(target, rendered, hint, mcp_notes)
        for schema in workflow.contract.schemas:
            resource(plugin.root / schema, staging_root / schema, plugin.root)
        # The sidecar travels with the package: a harness needs the declared
        # isolation, join and phase order at runtime, and a reader needs to be
        # able to check the contract without the kernel in hand.
        _copy(
            plugin.root / "workflows" / f"{workflow.name}.toml",
            staging_root / "contracts" / f"{workflow.name}.workflow.toml",
            plugin.root,
        )

    files = tuple(
        sorted(
            (path.relative_to(staging_root) for path in staging_root.rglob("*") if path.is_file()),
            key=lambda item: item.as_posix(),
        )
    )

    result = RenderResult(
        plugin=plugin.name,
        host=adapter.host,
        staging_root=staging_root,
        files=files,
        core_digest=_kernel_digest(plugin, kernel_files),
        harness_strategies=tuple(strategies),
        overrides=tuple(sorted(set(applied))),
    )
    write_provenance(result, plugin.version)
    return result


def _policy_implementation(adapters_root: Path, host: str, policy: str) -> Path | None:
    """Find this host's implementation of a neutral policy, if it ships one.

    The mapping lives on the adapter side (`policy.toml`, `implements = ...`) so
    that the kernel never has to name a host mechanism to get one.
    """
    root = Path(adapters_root) / host / "policies"
    _source(root, Path(adapters_root) / host, allow_missing=True)
    if not root.is_dir():
        return None
    _source_members(root)
    for candidate in sorted(root.iterdir(), key=lambda item: item.name):
        manifest = candidate / "policy.toml"
        _source(manifest, root, allow_missing=True)
        if not manifest.is_file():
            continue
        try:
            declared = tomllib.loads(_read_text(manifest, root))
        except tomllib.TOMLDecodeError as error:
            raise RenderError(f"invalid adapter policy TOML {manifest}: {error}") from error
        if declared.get("implements") == policy:
            return candidate
    return None


def _isolation_companion(adapter: HostAdapter) -> str:
    """The package a host needs installed before an isolated worker context exists.

    Empty on a host that ships isolation itself, which is every host but Pi. A
    template that never mentions it substitutes nothing.
    """
    binding = adapter.bindings.get("contexts.isolate")
    return binding.package or "" if binding is not None else ""


def _harness_context(
    plugin: PluginSpec,
    workflow: WorkflowSpec,
    strategy,
    adapter: HostAdapter,
    source: Path,
    context: dict,
    role_ids: Mapping[str, str] | None = None,
    body_bindings: str = "",
) -> dict:
    """Everything a host harness template may substitute, plus the argument hint.

    The hint is not a template key: the caller pops it and hands it to the
    host-text pass, which explains the arguments placeholder once per file.
    """
    roles = workflow.worker_references(plugin.components.roles) or plugin.components.roles
    role_ids = role_ids or {}
    ordered = sorted({role_ids.get(role, role) for role in roles})
    worker_phases = [phase for phase in workflow.phases if phase.role or phase.fanout or phase.fanout_from]
    isolated = (workflow.dispatch.isolated or workflow.dispatch.inline_workers
                or any(phase.isolation == "required" for phase in worker_phases))
    first_worker = worker_phases[0] if worker_phases else workflow.phases[0]
    meta, body = _frontmatter(_read_text(source, plugin.root))
    return {
        **context,
        "workflow": workflow.name,
        "workflow_name": _workflow_name(workflow.name, adapter, context),
        "description": _one_line(meta.get("description", plugin.description)),
        "strategy": strategy.name,
        "role_delivery": strategy.role_delivery,
        "isolation": "required" if isolated else "shared",
        "join": first_worker.join or "all-delivered",
        "roles": ", ".join(f"`{item}`" for item in ordered),
        "agents": ", ".join(f"'{item}'" for item in ordered),
        "tools": _coordinator_tools(plugin, adapter),
        "dispatch_plan": _dispatch_plan(workflow, role_ids),
        "role_bindings": body_bindings,
        "companion": _isolation_companion(adapter),
        "body": body.strip() + "\n",
        "hint": _unquote(meta.get("argument-hint", "")).strip() or None,
    }


def _dispatch_bindings(
    plugin: PluginSpec, workflow: WorkflowSpec, strategy, adapter: HostAdapter,
    staging: Path, registry: Mapping[str, PluginSpec] | None,
    operational_binding: str = "",
) -> tuple[dict[str, str], str]:
    """Bind declared external roles; inline bodies are generated resources, not components.

    A dependency owns the sole hand-authored role. Codex and Pi need that body
    verbatim in an isolated prompt, so the compiler ships only the referenced
    roles under contracts/dispatch. Those files carry owner and source digest
    and never register as skills or agents. Named-agent adapters copy no body.
    """
    references = workflow.worker_references(plugin.components.roles)
    providers = dict(registry or {})
    providers[plugin.name] = plugin
    ids: dict[str, str] = {}
    bindings: list[str] = []
    for reference in sorted(references):
        owner, separator, role = reference.partition("/")
        if not separator:
            owner, role = plugin.name, reference
        if owner != plugin.name and owner not in plugin.required_dependencies:
            raise RenderError(f"{plugin.name}: undeclared role provider {owner}")
        provider = providers.get(owner)
        if provider is None:
            # Compatibility for callers rendering a single real kernel. The
            # production build supplies the complete registry explicitly.
            from .load import load_plugin
            source_root = plugin.root.parent / owner
            _source(source_root, plugin.root.parent)
            if not (source_root / "plugin.toml").is_file():
                raise RenderError(f"{plugin.name}: unknown role provider {owner}")
            provider = load_plugin(source_root)
            providers[owner] = provider
        if role not in provider.components.roles:
            raise RenderError(f"{plugin.name}: unknown role {owner}/{role}")
        identity = f"{owner}:{role}" if owner != plugin.name else role
        ids[reference] = identity
        if strategy.role_delivery != "inline-prompt":
            bindings.append(f"- `{identity}`: dispatch the installed `{owner}:{role}` agent by its qualified identity.")
            continue
        if owner == plugin.name:
            relative = render_path(adapter.layout["roles"], {**_package_context(provider, adapter.host), "role": role})
            bindings.append(f"- `{identity}`: read `{relative.as_posix()}` inside this package and pass its complete body verbatim.")
            continue
        relative = Path("contracts/dispatch") / owner / f"{role}.md"
        source = provider.root / "roles" / f"{role}.md"
        text = _read_text(source, provider.root).replace("\r\n", "\n")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        owned_skills = ", ".join(f"`{owner}:{skill}`" for skill in provider.components.skills) or "none declared"
        skill_names = []
        if adapter.host == "pi":
            for skill in provider.components.skills:
                header, _ = _frontmatter(_read_text(provider.root / "skills" / skill / "SKILL.md", provider.root))
                registered = _unquote(header.get("name", skill))
                skill_names.append(f"`{owner}:{skill}` -> compiled registry name `{registered}` "
                                   f"at `skills/{skill}/SKILL.md` inside the owner's package")
        native_skills = ("Pi skill name bindings: " + "; ".join(skill_names) + ". Confirm those names and "
                         "provider paths in the active inventory before loading. " if skill_names else "")
        meta, body = _frontmatter(text)
        resource = (
            f"<!-- Generated dispatch body. Owner: {owner}:{role}; version: {provider.version}; "
            f"source-sha256: {digest}. Edit the owner's kernel, never this resource. -->\n\n"
            f"This body belongs to `{owner}`. Where it names its plugin root, resolve the root from "
            f"that installed plugin's available skill and verified provider path; it is not the coordinator's root. "
            f"`<{owner}-plugin-root>` names that owner root. Any unqualified skill load "
            f"in the body belongs to `{owner}`. The owning plugin's declared logical skill identities "
            f"are {owned_skills}; these are not invented native registry strings. Resolve each to the "
            f"exact installed identity advertised by this host and verify its provider before loading. "
            + native_skills
            + f"Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.\n\n"
            + _inline_role_scope(meta)
            + body.replace("${CLAUDE_PLUGIN_ROOT}", f"<{owner}-plugin-root>")
        )
        _write_markdown(staging / relative, resource, adapter, operational_binding=operational_binding)
        bindings.append(f"- `{identity}`: read `{relative.as_posix()}` inside this package and pass its complete role body verbatim.")
    if workflow.dispatch.inline_workers:
        bindings.append("- Method-owned inline workers use only `project-protocol:isolated-worker`. Give each the full task, "
                        "owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.")
    return ids, "\n".join(bindings)


def _rename_with_retry(
    source: Path, destination: Path, attempts: int = 10, *, replace_existing: bool = False
) -> None:
    """Rename a tree or replace a file, retrying a transient sharing violation.

    On Windows a directory rename fails with access denied while any process
    still holds a handle inside it, and an indexer or scanner routinely holds one
    for a moment after a package is written. That is transient by nature, so it
    must not abort a publication that is otherwise correct.
    """
    for attempt in range(attempts):
        try:
            if replace_existing:
                source.replace(destination)
            else:
                source.rename(destination)
            return
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.1 * (attempt + 1))


@contextmanager
def _publication_lock(lock: Path):
    """Hold OS ownership until close; process death releases it automatically.

    The sibling file stays in place so every contender locks the same inode.
    Its presence alone says nothing about whether a publisher is active.
    """
    handle = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(handle).st_size == 0:
                    os.write(handle, b"\0")
                os.lseek(handle, 0, os.SEEK_SET)
                msvcrt.locking(handle, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RenderError(f"another build holds {lock}: {error}") from error
        yield
    finally:
        os.close(handle)


def replace_tree(staging: Path, live: Path) -> None:
    """Swap a validated staging tree and restore live after a failed rename.

    OS ownership excludes concurrent publishers for this output. Keep the
    previous tree until the staging rename succeeds, including cancellation.
    """
    staging = Path(staging)
    live = Path(live)
    if not staging.is_dir():
        raise RenderError(f"staging tree does not exist: {staging}")

    live.parent.mkdir(parents=True, exist_ok=True)
    lock = live.parent / f".{live.name}.lock"
    previous = live.parent / f".{live.name}.previous"

    with _publication_lock(lock):
        if previous.exists():
            if not live.exists():
                _rename_with_retry(previous, live)
            else:
                shutil.rmtree(previous)
        had_live = live.exists()
        try:
            if had_live:
                _rename_with_retry(live, previous)
            _rename_with_retry(staging, live)
        except BaseException as error:
            if had_live and previous.exists() and not live.exists():
                _rename_with_retry(previous, live)
            if isinstance(error, OSError):
                raise RenderError(f"could not publish {live}: {error}") from error
            raise
        if had_live:
            shutil.rmtree(previous, ignore_errors=True)


def publish_plugin(
    plugin: PluginSpec,
    adapter: HostAdapter,
    live: Path,
    overrides: Sequence[OverrideSpec] = (),
    adapters_root: Path | None = None,
    plugin_registry: Mapping[str, PluginSpec] | None = None,
) -> RenderResult:
    """Render into a temporary sibling of ``live`` and publish it atomically."""
    live = Path(live)
    live.parent.mkdir(parents=True, exist_ok=True)
    staging = live.parent / f".{live.name}.{uuid.uuid4().hex}.staging"
    staging.mkdir()
    try:
        result = render_plugin(plugin, adapter, staging, overrides, adapters_root, plugin_registry)
        replace_tree(staging, live)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return RenderResult(
        plugin=result.plugin,
        host=result.host,
        staging_root=live,
        files=result.files,
        core_digest=result.core_digest,
        harness_strategies=result.harness_strategies,
        overrides=result.overrides,
    )


def read_provenance(root: Path) -> dict[str, object]:
    return json.loads(_read_text(Path(root) / ".daodan-provenance.json", Path(root)))
