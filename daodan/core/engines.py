"""The engines the app gives a task of reasoning to: one small contract and three adapters.

    engine.run(task, say, cancelled) -> {"state": "done" | "failed" | "cancelled", "text", "session", "cause"}

`task` is `{"prompt", "system"?, "tools"?, "mcp"?, "cwd"?}`. `tools` are functions of this process, each `{"name",
"description", "parameters" (a JSON Schema), "call"}`, for an engine that is asked over an API and has none of
its own. `mcp` is how to start Daodan's MCP server for the project, `{"command", "args"}`, for an engine that is a
command line and reaches Daodan as any MCP client does. An adapter uses the one it can and never pretends the
other. `say(kind, **data)` is told what happens while it happens: `text` (a piece of the answer), `tool` (a tool
asked for, its arguments and what it answered), `log`. `cancelled()` is asked between steps; a run it stops is
`cancelled` and its process is ended before the call returns.

- `OpenAICompatible`: an endpoint that speaks Chat Completions (`<base_url>/chat/completions`), streamed, with
  tool calls; this adapter holds the loop of model, tools and answers. The key travels only in the request header.
- `ClaudeCode`, `Codex`: the command lines with their own login. Each runs without its tools that execute commands
  or write files: what the analysed project holds is read through Daodan's tools, and its code runs nowhere here.

`configured` builds the engine of a setting; `probe` asks it for a word and, where it has tools, for a tool call.
`kept` writes a setting for the next start and `recalled` reads it: engine, address and model in the work folder, the
key only in the system's deposit of secrets (`keyring`: the credential manager on Windows, Secret Service or KWallet
on Linux), which encrypts it with the person's account. A folder or a deposit that fails is a cause the setting
carries (`unread`, `unkept`), never a failure of the start.
"""
from __future__ import annotations

import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import threading
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path

ENGINES = ("openai", "claude", "codex")
TURNS = 24  # the model's turns in one task: a loop of tool calls ends there
SECONDS = 900  # one task
ANSWER = 20_000  # the characters of a tool's answer given back to the model
SERVER = "daodan"  # the name Daodan's MCP server has for a command-line engine
KEPT = ("engine", "base_url", "model")  # what of a setting the work folder keeps: never the key
STORE, DEPOSIT, ENTRY = "settings.sqlite", "daodan", "openai-api-key"  # the folder's file; the key's place in the deposit


def _outcome(state: str, text: str = "", session: str | None = None, cause: str | None = None) -> dict:
    return {"state": state, "text": text, "session": session, "cause": cause}


class OpenAICompatible:
    NAME = "openai"

    def __init__(self, base_url: str, model: str, api_key: str | None = None, seconds: int = SECONDS):
        if not base_url.startswith(("https://", "http://")) or not model:
            raise ValueError("the endpoint needs an http(s) address and a model")
        self.base_url, self.model, self.api_key, self.seconds = base_url.rstrip("/"), model, api_key or None, seconds

    def _stream(self, messages: list[dict], tools: list[dict], say, cancelled) -> dict:
        """One turn: the assistant's message, its text said as it comes."""
        body = {"model": self.model, "messages": messages, "stream": True}
        if tools:
            body["tools"] = [{"type": "function", "function": {key: tool[key] for key in
                                                               ("name", "description", "parameters")}}
                             for tool in tools]
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(f"{self.base_url}/chat/completions", json.dumps(body).encode("utf-8"),
                                         headers, method="POST")
        text, calls, chunks = [], {}, 0
        with urllib.request.urlopen(request, timeout=self.seconds) as answer:
            for raw in answer:
                if cancelled():
                    raise InterruptedError
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                    continue
                choices = json.loads(line[5:]).get("choices") or [{}]
                delta = choices[0].get("delta") or {}
                chunks += 1
                if delta.get("content"):
                    text.append(delta["content"])
                    say("text", text=delta["content"])
                for piece in delta.get("tool_calls") or ():
                    call = calls.setdefault(piece.get("index", 0), {"id": "", "name": "", "arguments": ""})
                    call["id"] = piece.get("id") or call["id"]
                    function = piece.get("function") or {}
                    call["name"] += function.get("name") or ""
                    call["arguments"] += function.get("arguments") or ""
        message = {"role": "assistant", "content": "".join(text) or None}
        if calls:
            message["tool_calls"] = [{"id": call["id"], "type": "function",
                                      "function": {"name": call["name"], "arguments": call["arguments"]}}
                                     for _, call in sorted(calls.items())]
        return {"message": message, "chunks": chunks}

    def run(self, task: dict, say=lambda kind, **data: None, cancelled=lambda: False) -> dict:
        tools = {tool["name"]: tool for tool in task.get("tools") or ()}
        messages = [*([{"role": "system", "content": task["system"]}] if task.get("system") else []),
                    {"role": "user", "content": task["prompt"]}]
        try:
            for _turn in range(TURNS):
                message = self._stream(messages, list(tools.values()), say, cancelled)["message"]
                messages.append(message)
                if not message.get("tool_calls"):
                    return _outcome("done", message["content"] or "")
                for call in message["tool_calls"]:
                    name = call["function"]["name"]
                    try:
                        arguments = json.loads(call["function"]["arguments"] or "{}")
                        answer = tools[name]["call"](arguments)
                    except KeyError:
                        answer = {"error": f"no tool {name!r}"}
                    except (ValueError, TypeError, OSError) as error:  # the model reads what its call got wrong
                        answer = {"error": str(error)}
                    said = json.dumps(answer, ensure_ascii=False, default=str)[:ANSWER]
                    say("tool", name=name, arguments=call["function"]["arguments"], answer=said[:400])
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": said})
            return _outcome("failed", cause=f"the model asked for tools {TURNS} turns in a row and gave no answer")
        except InterruptedError:
            return _outcome("cancelled")
        except urllib.error.HTTPError as error:
            detail = error.read(600).decode("utf-8", errors="replace")
            return _outcome("failed", cause=f"the endpoint answered {error.code}: {detail}")
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            return _outcome("failed", cause=f"the endpoint was not reached: {type(error).__name__}: {error}")


class _CommandLine:
    """An engine that is a command line: the prompt on its input, one JSON event per line on its output."""
    NAME = COMMAND = ""

    def __init__(self, command: str | None = None, seconds: int = SECONDS):
        self.command, self.seconds = command or self.COMMAND, seconds

    def arguments(self, task: dict, folder: Path) -> list[str]:
        raise NotImplementedError

    def read(self, event: dict, state: dict, say) -> None:
        raise NotImplementedError

    def run(self, task: dict, say=lambda kind, **data: None, cancelled=lambda: False) -> dict:
        program = shutil.which(self.command)
        if program is None:
            return _outcome("failed", cause=f"{self.command} is not on PATH")
        folder = Path(task.get("cwd") or ".").resolve()
        state = {"text": [], "session": None, "error": None}
        process = subprocess.Popen([program, *self.arguments(task, folder)], cwd=folder, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                   errors="replace")
        late = threading.Timer(self.seconds, process.kill)
        late.start()
        errors: list[str] = []
        drain = threading.Thread(target=lambda: errors.extend(process.stderr), daemon=True)
        drain.start()
        try:
            process.stdin.write((f"{task['system']}\n\n" if task.get("system") else "") + task["prompt"])
            process.stdin.close()
            for line in process.stdout:
                if cancelled():
                    process.kill()
                    process.wait()
                    return _outcome("cancelled", "".join(state["text"]), state["session"])
                try:
                    event = json.loads(line)
                except ValueError:
                    continue  # a line that is not an event: the command's own words
                if isinstance(event, dict):
                    self.read(event, state, say)
            code = process.wait()
            drain.join(2)
        finally:
            late.cancel()
            if process.poll() is None:
                process.kill()
                process.wait()
        text = "".join(state["text"])
        if code or state["error"]:
            cause = state["error"] or f"{self.command} ended with code {code}: {''.join(errors)[-600:].strip()}"
            return _outcome("failed", text, state["session"], cause)
        return _outcome("done", text, state["session"])


class ClaudeCode(_CommandLine):
    NAME = COMMAND = "claude"

    def arguments(self, task: dict, folder: Path) -> list[str]:
        out = ["-p", "--output-format", "stream-json", "--verbose", "--tools", "", "--strict-mcp-config"]
        if task.get("mcp"):
            config = folder / f"mcp-{secrets.token_hex(4)}.json"
            config.write_text(json.dumps({"mcpServers": {SERVER: task["mcp"]}}), encoding="utf-8")
            out += ["--mcp-config", str(config), "--allowedTools", f"mcp__{SERVER}"]
        return out

    def read(self, event: dict, state: dict, say) -> None:
        state["session"] = event.get("session_id") or state["session"]
        if event.get("type") == "system" and event.get("subtype") == "init":
            unconnected = [f"{server.get('name')} is {server.get('status')}" for server in event.get("mcp_servers") or ()
                           if server.get("name") == SERVER and server.get("status") != "connected"]
            if unconnected:  # an answer given without Daodan's tools would be a guess
                state["error"] = f"Daodan's MCP server did not connect ({unconnected[0]}): the task has no tools"
        elif event.get("type") == "assistant":
            for block in (event.get("message") or {}).get("content") or ():
                if block.get("type") == "text":
                    say("text", text=block["text"])
                elif block.get("type") == "tool_use":
                    say("tool", name=block.get("name"), arguments=json.dumps(block.get("input"))[:400], answer=None)
        elif event.get("type") == "result":
            state["text"] = [event.get("result") or ""]
            if event.get("is_error"):
                state["error"] = f"claude ended in error: {event.get('result') or event.get('subtype')}"


class Codex(_CommandLine):
    NAME = COMMAND = "codex"

    def arguments(self, task: dict, folder: Path) -> list[str]:
        out = ["exec", "--json", "--skip-git-repo-check", "--ephemeral", "--sandbox", "read-only",
               "--disable", "shell_tool", "--disable", "unified_exec", "--cd", str(folder)]
        if task.get("mcp"):  # the values are TOML: JSON strings and arrays are TOML's too
            out += ["-c", f"mcp_servers.{SERVER}.command={json.dumps(task['mcp']['command'])}",
                    "-c", f"mcp_servers.{SERVER}.args={json.dumps(task['mcp']['args'])}"]
        return [*out, "-"]

    def read(self, event: dict, state: dict, say) -> None:
        if event.get("type") == "thread.started":
            state["session"] = event.get("thread_id")
        elif event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message":
                state["text"].append(item.get("text") or "")
                say("text", text=item.get("text") or "")
            elif item.get("type") == "mcp_tool_call":
                say("tool", name=item.get("tool"), arguments=json.dumps(item.get("arguments"))[:400], answer=None)
        elif event.get("type") in ("error", "turn.failed"):
            state["error"] = f"codex: {event.get('message') or (event.get('error') or {}).get('message')}"


def _asked(environment) -> dict:
    """What Daodan's variables of the environment name, without what they leave out."""
    asked = {"engine": environment.get("DAODAN_ENGINE"), "base_url": environment.get("DAODAN_OPENAI_BASE_URL"),
             "model": environment.get("DAODAN_OPENAI_MODEL"), "api_key": environment.get("DAODAN_OPENAI_API_KEY")}
    return {name: value for name, value in asked.items() if value}


def setting(environment=os.environ, saved: dict | None = None) -> dict:
    """The engine to use, `{engine, base_url, model, api_key}`, each part from the first that has it: Daodan's
    variables of the environment, `saved`, the general `OPENAI_API_KEY`, the defaults. None of it is written here."""
    return {"engine": None, "base_url": "https://api.openai.com/v1", "model": "",
            "api_key": environment.get("OPENAI_API_KEY") or "", **(saved or {}), **_asked(environment)}


def recalled(folder: Path, environment=os.environ) -> dict:
    """The setting of a start: `setting` over what `kept` wrote in `folder` and the key the system's deposit holds.
    `unread` is why the folder's file was not read, `unkept` why the deposit was not, each None when it was."""
    import keyring  # here, not above: running an engine needs no deposit
    saved, unread, unkept = {}, None, None
    if (folder / STORE).is_file():
        try:
            with closing(sqlite3.connect(folder / STORE)) as db:
                saved = {name: value for name, value in db.execute("SELECT name, value FROM setting") if name in KEPT}
        except sqlite3.Error as error:
            unread = f"the saved engine is not read ({error}): saving one replaces it"
    try:
        key = keyring.get_password(DEPOSIT, ENTRY)
    except Exception as error:  # noqa: BLE001 a deposit raises its system's own errors, not only keyring's
        key, unkept = None, f"the system's deposit of secrets is not read ({type(error).__name__})"
    return {**setting(environment, {**saved, **({"api_key": key} if key else {})}), "unread": unread, "unkept": unkept}


def kept(chosen: dict, folder: Path, key: str | None = None) -> str | None:
    """Keep `chosen` for the next start: engine, address and model in `folder`, written whole beside the file kept
    and put in its place, so a file that cannot be read is replaced. `key` is the key the person gave, empty to
    forget the one kept, None to leave it: the system's deposit takes it, and the answer is why it did not, else
    None. A folder that cannot be written is an OSError, and nothing is kept."""
    import keyring
    import keyring.errors
    fresh = folder / f"{STORE}.new"
    try:
        fresh.unlink(missing_ok=True)
        with closing(sqlite3.connect(fresh)) as db, db:
            db.execute("CREATE TABLE setting (name TEXT PRIMARY KEY, value TEXT)")
            db.executemany("INSERT INTO setting VALUES (?, ?)", [(name, chosen.get(name)) for name in KEPT])
        os.replace(fresh, folder / STORE)
    except sqlite3.Error as error:
        raise OSError(f"the engine is not kept in {folder}: {error}") from error
    if key is None:
        return None
    try:
        try:  # first, so a key replaced leaves no copy: the Windows deposit keeps the old one under a second name
            keyring.delete_password(DEPOSIT, ENTRY)
        except keyring.errors.PasswordDeleteError:
            pass  # none was kept
        if key:
            keyring.set_password(DEPOSIT, ENTRY, key)
    except Exception as error:  # noqa: BLE001 as in `recalled`
        return f"the system's deposit of secrets did not {'take' if key else 'forget'} the key ({type(error).__name__})"
    return None


def described(chosen: dict) -> dict:
    """A setting as it may be shown: the key is said `set` or `missing`, never itself; `unkept` is why what the
    person saved is not all kept (a file not read, a key that is in this process only), None when it is."""
    return {"engine": chosen.get("engine"), "base_url": chosen.get("base_url"), "model": chosen.get("model"),
            "api_key": "set" if chosen.get("api_key") else "missing",
            "unkept": "; ".join(filter(None, (chosen.get("unread"), chosen.get("unkept")))) or None,
            "engines": list(ENGINES)}


def configured(chosen: dict):
    """The engine of a setting; a setting that names none, or lacks what its engine needs, is refused."""
    if chosen.get("engine") == "openai":
        return OpenAICompatible(chosen.get("base_url") or "", chosen.get("model") or "", chosen.get("api_key"))
    if chosen.get("engine") == "claude":
        return ClaudeCode()
    if chosen.get("engine") == "codex":
        return Codex()
    raise ValueError(f"no engine is chosen: one of {', '.join(ENGINES)}")


def probe(engine, folder: Path, seconds: int = 120) -> dict:
    """Whether `engine` answers, and whether it calls a tool where it takes tools of this process: `{engine,
    reachable, tools, detail}`. `tools` is None for an engine whose tools are an MCP server's."""
    word, called = secrets.token_hex(4), []
    echo = {"name": "daodan_echo", "description": "Returns the value it is given.",
            "parameters": {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]},
            "call": lambda arguments: called.append(arguments.get("value")) or {"value": arguments.get("value")}}
    own = isinstance(engine, OpenAICompatible)
    engine.seconds = seconds
    prompt = (f"Call the tool daodan_echo with the value {word}, then answer with the value it returned and "
              "nothing else." if own else f"Answer with this word and nothing else: {word}")
    outcome = engine.run({"prompt": prompt, "tools": [echo] if own else [], "cwd": str(folder)})
    reachable = outcome["state"] == "done" and word in outcome["text"]
    return {"engine": engine.NAME, "reachable": reachable, "tools": (word in called) if own else None,
            "detail": outcome["cause"] or ("" if reachable else f"the answer was not the word: {outcome['text'][:200]}")}
