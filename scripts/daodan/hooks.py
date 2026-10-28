"""Render neutral Python callbacks and routing delivery as optional host lifecycle registrations."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from .adapter import HostAdapter
from .model import HookSpec, PluginSpec
from .templates import render_path

HOOK_MANIFEST = Path("hooks/hooks.json")
#: The routing text a plugin package carries on a host that delivers it.
ROUTING_TEXT = Path("hooks/entry-routing.md")
ROUTING_TIMEOUT = 5


def _environments(adapter: HostAdapter) -> list[str]:
    environments = adapter.layout.get("hook_root_environment", "").split(",")
    if not environments or any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", name) for name in environments):
        raise ValueError(f"{adapter.host}: missing or invalid hook root environment binding")
    return environments


def _launcher(source: str, flags: str = "") -> str:
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    # This command contains only fixed syntax and base64, never shell substitutions.
    return f'''python {flags}-c "import base64;exec(base64.b64decode('{encoded}'))"'''


def _command(hook: HookSpec, plugin: PluginSpec, adapter: HostAdapter) -> str:
    """Keep all paths and literal arguments out of shell parsing on both platforms."""
    environments = _environments(adapter)
    skill = hook.script.parts[1]
    entry = render_path(adapter.layout["skills"], {"plugin": plugin.name, "skill": skill})
    script = entry.parent.joinpath(*hook.script.parts[2:]).as_posix()
    payload = json.dumps({"environments": environments, "script": script, "args": hook.args})
    source = (
        "import json, os, pathlib, subprocess, sys\n"
        f"data = json.loads({payload!r})\n"
        "root = next((os.environ[key] for key in data['environments'] if os.environ.get(key)), None)\n"
        "if not root:\n"
        "    raise SystemExit('Plugin hook root environment is missing')\n"
        "root = pathlib.Path(root)\n"
        "if not root.is_absolute():\n"
        "    raise SystemExit('Plugin hook root must be absolute')\n"
        "root = root.resolve(strict=True)\n"
        "script = (root / data['script']).resolve(strict=True)\n"
        "if not script.is_relative_to(root) or not script.is_file():\n"
        "    raise SystemExit('Plugin hook script escapes its root or is missing')\n"
        "result = subprocess.run([sys.executable, str(script), *data['args']], "
        "stdin=sys.stdin.buffer, stdout=sys.stdout.buffer, stderr=sys.stderr.buffer)\n"
        "raise SystemExit(result.returncode)\n"
    )
    return _launcher(source)


def _routing_command(adapter: HostAdapter) -> str:
    """Print the routing text as session context; once started, any error ends silently with 0.

    `-I` keeps the project directory, where the host starts the hook, off the import path.
    """
    payload = json.dumps({"environments": _environments(adapter), "text": ROUTING_TEXT.as_posix()})
    source = (
        "import os\n"
        "try:\n"
        "    import json, pathlib, sys\n"
        f"    data = json.loads({payload!r})\n"
        "    root = next((os.environ[key] for key in data['environments'] if os.environ.get(key)), None)\n"
        "    if not root or not pathlib.Path(root).is_absolute():\n"
        "        os._exit(0)\n"
        "    root = pathlib.Path(root).resolve(strict=True)\n"
        "    path = (root / data['text']).resolve(strict=True)\n"
        "    if not path.is_relative_to(root) or not path.is_file():\n"
        "        os._exit(0)\n"
        "    context = path.read_text(encoding='utf-8')\n"
        "    output = json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', "
        "'additionalContext': context}}, ensure_ascii=False) + '\\n'\n"
        "    sys.stdout.buffer.write(output.encode('utf-8'))\n"
        "    sys.stdout.buffer.flush()\n"
        "except BaseException:\n"
        "    os._exit(0)\n"
    )
    return _launcher(source, "-I ")


def render_hooks(
    plugin: PluginSpec, adapter: HostAdapter, routing: bool = False
) -> tuple[str | None, tuple[str, ...]]:
    """Return a manifest and entry notes; unsupported optional hooks stay explicit.

    ``routing`` adds the session-start entry that delivers `ROUTING_TEXT` and never a note.
    """
    if not plugin.hooks and not routing:
        return None, ()
    binding = adapter.bindings.get("hooks.lifecycle")
    if binding is None or binding.state == "unsupported":
        return None, (
            "This package retains its lifecycle callback scripts, but this host has no "
            "declared native hook registration. Use the method's explicit workflow checkpoints; "
            "automatic interception outside those workflows is unavailable.",
        ) if plugin.hooks else ()
    if binding.strategy == "loader-hooks":
        return None, (
            "This package registers lifecycle callbacks through the OpenCode plugin loader "
            "when the plugin is enabled. Execution requires Python 3 on PATH as `python`. "
            "Prompt hooks feed the primary model context; session-start falls back to the "
            "first prompt when creation was not observed. Hook failures do not crash the host.",
        ) if plugin.hooks else ()
    if binding.strategy != "hooks-manifest":
        raise ValueError(f"{adapter.host}: unsupported lifecycle hook strategy {binding.strategy!r}")
    entries = adapter.layout.get("hook_events", "").split(",")
    events = dict(entry.split(":", 1) for entry in entries if ":" in entry)
    hooks: dict[str, list[dict[str, object]]] = {}
    for hook in plugin.hooks:
        event = events.get(hook.event)
        if event not in {"SessionStart", "UserPromptSubmit"}:
            raise ValueError(f"{adapter.host}: missing native event binding for {hook.event!r}")
        handler = {"type": "command", "command": _command(hook, plugin, adapter), "timeout": hook.timeout}
        hooks.setdefault(event, []).append({"hooks": [handler]})
    if routing:
        if events.get("session-start") != "SessionStart":
            raise ValueError(f"{adapter.host}: missing native event binding for 'session-start'")
        handler = {"type": "command", "command": _routing_command(adapter), "timeout": ROUTING_TIMEOUT}
        hooks.setdefault("SessionStart", []).append({"hooks": [handler]})
    notes = (
        "This package registers lifecycle callbacks through `hooks/hooks.json` when the plugin "
        "is enabled. Execution requires the host's hook trust approval and Python 3 on PATH "
        "as `python`. The compiler does not approve hooks or modify host settings. "
        "Generated registration and subprocess checks do not prove installed-host execution.",
    ) if plugin.hooks else ()
    return json.dumps({"hooks": hooks}, indent=2) + "\n", notes
