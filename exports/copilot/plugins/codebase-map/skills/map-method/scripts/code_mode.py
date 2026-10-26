"""Bounded local JavaScript composition over explicitly supplied capabilities.

Original implementation inspired by Cloudflare Code Mode. The Python broker owns
capability admission and receipts; Deno's permission boundary owns generated code.
This is not an OS sandbox or a process-wide memory/disk quota.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
import time
from typing import Awaitable, Callable


@dataclass(frozen=True)
class Limits:
    max_code_bytes: int = 32768
    timeout_seconds: float = 30
    max_calls: int = 32
    heap_mb: int = 128
    max_output_bytes: int = 65536
    max_argument_bytes: int = 65536
    max_intermediate_bytes: int = 8 * 1024 * 1024
    max_total_intermediate_bytes: int = 32 * 1024 * 1024
    max_stderr_bytes: int = 16384


class CodeModeError(ValueError):
    def __init__(self, message: str, calls: list[dict] | None = None):
        super().__init__(message)
        self.calls = calls if calls is not None else []

    def __str__(self) -> str:
        # JS strings can contain isolated UTF-16 surrogates. Diagnostics still
        # have to survive the MCP transport's UTF-8 serializer.
        message = super().__str__().encode("utf-8", errors="backslashreplace").decode("utf-8")
        if self.calls:
            message += "; admitted calls: " + json.dumps(self.calls, ensure_ascii=True)
        return message


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _environment(directory: str) -> dict[str, str]:
    # DENO_PERMISSION_BROKER_PATH overrides CLI permissions. Inherit no Deno,
    # loader, proxy, credential, PATH or project configuration variables.
    environment = {"DENO_DIR": str(Path(directory) / "cache"),
                   "DENO_NO_UPDATE_CHECK": "1", "NO_COLOR": "1",
                   "TMPDIR": directory, "TEMP": directory, "TMP": directory}
    if os.name == "nt":
        for name in ("SystemRoot", "WINDIR"):
            if name in os.environ:
                environment[name] = os.environ[name]
    return environment


def _resolve_deno(value: str | Path | None, project_root: Path | None) -> Path:
    candidates = []
    if value is not None:
        candidate = Path(value)
        if not candidate.is_absolute():
            raise CodeModeError("Deno executable must be an absolute path")
        candidates.append(candidate)
    else:
        for entry in os.get_exec_path():
            if Path(entry).is_absolute():
                found = shutil.which("deno", path=entry)
                if found:
                    candidates.append(Path(found))
    for candidate in candidates:
        resolved = candidate.resolve()
        if project_root is not None and resolved.is_relative_to(project_root.resolve()):
            continue
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return resolved
    raise CodeModeError("Deno 2.4+ is required for --code-mode; install a maintained "
                        "release outside the project or supply an absolute --deno path")


class DenoExecutor:
    def __init__(self, deno: str | Path | None = None, *, limits: Limits | None = None,
                 project_root: Path | None = None):
        self.limits = limits or Limits()
        self.deno = _resolve_deno(deno, project_root)
        try:
            with tempfile.TemporaryDirectory(prefix="daodan-deno-check-") as directory:
                checked = subprocess.run([str(self.deno), "--version"], cwd=directory,
                                         env=_environment(directory), capture_output=True,
                                         text=True, timeout=5, check=True)
        except (OSError, subprocess.SubprocessError) as error:
            raise CodeModeError(f"Cannot start Deno: {error}") from error
        version = re.search(r"^deno (\d+)\.(\d+)\.(\d+)", checked.stdout)
        if not version or tuple(map(int, version.groups())) < (2, 4, 0):
            raise CodeModeError("Deno 2.4 or later is required for --deny-import")
        self.version = version.group(0)

    async def run(self, code: str, *, catalog: list[dict],
                  call_tool: Callable[[str, dict], Awaitable[object]] | None,
                  allowed_tools: set[str]) -> dict:
        limits = self.limits
        if not isinstance(code, str) or not code.strip():
            raise CodeModeError("code must be a non-empty async JavaScript function")
        try:
            code_bytes = code.encode("utf-8")
        except UnicodeError as error:
            raise CodeModeError("code must contain valid UTF-8 text") from error
        if len(code_bytes) > limits.max_code_bytes:
            raise CodeModeError("code exceeds the execution input limit")
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
               or name in {"__proto__", "constructor", "prototype"} for name in allowed_tools):
            raise CodeModeError("invalid capability name")

        calls: list[dict] = []
        intermediate_bytes = 0
        started = time.monotonic()
        token = secrets.token_hex(32)
        bootstrap = _json_bytes({"token": token, "code": code, "catalog": catalog,
                                 "tools": sorted(allowed_tools),
                                 "maxOutputBytes": limits.max_output_bytes})
        if len(bootstrap) > limits.max_intermediate_bytes:
            raise CodeModeError("catalog exceeds the execution input limit")
        runner = Path(__file__).with_name("code_mode_runner.js")
        arguments = [str(self.deno), "run", "--no-config", "--no-lock", "--no-npm",
                     "--no-remote", "--cached-only", "--no-prompt", "--deny-read",
                     "--deny-write", "--deny-net", "--deny-env", "--deny-run",
                     "--deny-ffi", "--deny-sys", "--deny-import",
                     f"--v8-flags=--max-old-space-size={limits.heap_mb}", str(runner)]
        frame_limit = max(limits.max_output_bytes, limits.max_argument_bytes) + 8192

        with tempfile.TemporaryDirectory(prefix="daodan-code-mode-") as directory:
            try:
                process = await asyncio.create_subprocess_exec(
                    *arguments, cwd=directory, env=_environment(directory),
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE, limit=frame_limit)
            except OSError as error:
                raise CodeModeError(f"Cannot start Deno: {error}") from error
            violation = None
            diagnostics = bytearray()
            active_call = None

            def stop(reason: str) -> None:
                nonlocal violation
                violation = violation or reason
                if process.returncode is None:
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass

            async def deadline():
                await asyncio.sleep(limits.timeout_seconds)
                stop("JavaScript deadline exceeded")

            async def drain_stderr():
                while chunk := await process.stderr.read(4096):
                    remaining = limits.max_stderr_bytes - len(diagnostics)
                    diagnostics.extend(chunk[:max(remaining, 0)])
                    if len(chunk) > remaining:
                        stop("stderr output limit exceeded")
                        # Keep draining after the kill: a paused pipe prevents
                        # asyncio's subprocess transport from finishing.

            async def drain_stdout():
                while await process.stdout.read(65536):
                    pass

            timer = asyncio.create_task(deadline())
            stderr_task = asyncio.create_task(drain_stderr())

            async def send(message: dict) -> None:
                process.stdin.write(_json_bytes(message) + b"\n")
                await process.stdin.drain()

            try:
                process.stdin.write(bootstrap + b"\n")
                await process.stdin.drain()
                seen_ids = set()
                while True:
                    try:
                        line = await process.stdout.readline()
                    except (ValueError, asyncio.LimitOverrunError) as error:
                        raise CodeModeError("protocol output frame exceeds limit", calls) from error
                    if not line:
                        await process.wait()
                        await stderr_task
                        detail = diagnostics.decode("utf-8", errors="replace")[-2000:]
                        raise CodeModeError(violation or f"Deno exited without a result: {detail}", calls)
                    if violation:
                        raise CodeModeError(violation, calls)
                    try:
                        message = json.loads(line)
                    except (ValueError, UnicodeError) as error:
                        raise CodeModeError("invalid Code Mode protocol JSON", calls) from error
                    if not isinstance(message, dict) or message.get("token") != token:
                        raise CodeModeError("unauthenticated Code Mode protocol output", calls)
                    kind = message.get("type")
                    if kind == "error":
                        raise CodeModeError(str(message.get("error", "JavaScript execution failed"))[:4000], calls)
                    if kind == "result":
                        value = message.get("value")
                        output_bytes = len(_json_bytes(value))
                        if output_bytes > limits.max_output_bytes:
                            raise CodeModeError("final output exceeds limit; return a smaller selection", calls)
                        # A Worker can race its final message with raw stdout.
                        # Never wait for exit while unread output can pause the
                        # subprocess pipe, even if the process has already exited.
                        if await process.stdout.read(1):
                            raise CodeModeError("unexpected output after final result", calls)
                        await process.wait()
                        await stderr_task
                        if violation or process.returncode:
                            raise CodeModeError(violation or "Deno failed after producing output", calls)
                        return {"value": value, "calls": calls,
                                "stats": {"tool_calls": len(calls),
                                          "intermediate_bytes": intermediate_bytes,
                                          "selected_value_bytes": output_bytes,
                                          "receipt_bytes": len(_json_bytes(calls)),
                                          "elapsed_ms": round((time.monotonic() - started) * 1000)}}
                    if kind != "call":
                        raise CodeModeError("unknown Code Mode protocol message", calls)
                    identity, name = message.get("id"), message.get("name")
                    if (type(identity) is not int or identity < 1 or identity in seen_ids):
                        raise CodeModeError("invalid or duplicate protocol request id", calls)
                    seen_ids.add(identity)
                    if len(seen_ids) > limits.max_calls:
                        raise CodeModeError("internal call limit exceeded", calls)
                    if not isinstance(name, str) or name not in allowed_tools or call_tool is None:
                        raise CodeModeError("operation is not permitted in this execution", calls)
                    parameters = message.get("arguments")
                    if not isinstance(parameters, dict):
                        raise CodeModeError("tool arguments must be a JSON object", calls)
                    if len(_json_bytes(parameters)) > limits.max_argument_bytes:
                        raise CodeModeError("tool arguments exceed input limit", calls)

                    receipt = {"tool": name, "ok": False}
                    calls.append(receipt)
                    active_call = asyncio.create_task(call_tool(name, parameters))
                    try:
                        value = await asyncio.shield(active_call)
                        encoded = _json_bytes(value)
                        receipt.update(ok=True, output_bytes=len(encoded))
                        intermediate_bytes += len(encoded)
                        if (len(encoded) > limits.max_intermediate_bytes
                                or intermediate_bytes > limits.max_total_intermediate_bytes):
                            raise CodeModeError("intermediate output limit exceeded", calls)
                        response = {"id": identity, "value": value}
                    except CodeModeError:
                        raise
                    except Exception as error:
                        detail = f"{type(error).__name__}: {error}"[:2000]
                        receipt["error"] = detail
                        response = {"id": identity, "error": detail}
                    active_call = None
                    if violation:
                        raise CodeModeError(violation, calls)
                    await send(response)
            except CodeModeError:
                raise
            except (UnicodeError, ValueError, TypeError, RecursionError) as error:
                raise CodeModeError(f"Execution contains an invalid JSON value: {error}", calls) from error
            except (BrokenPipeError, ConnectionResetError) as error:
                raise CodeModeError(violation or "Deno protocol connection closed", calls) from error
            finally:
                stop("execution ended")

                async def cleanup():
                    timer.cancel()
                    process.stdin.close()
                    discarded_stdout = asyncio.create_task(drain_stdout())
                    # Do not abandon an admitted atomic operation on cancellation.
                    if active_call is not None:
                        try:
                            await active_call
                            calls[-1]["ok"] = True
                        except BaseException as error:
                            calls[-1]["error"] = f"{type(error).__name__}: {error}"[:2000]
                    await asyncio.gather(timer, return_exceptions=True)
                    await asyncio.gather(discarded_stdout, stderr_task, process.wait())
                    await asyncio.gather(process.stdin.wait_closed(), return_exceptions=True)

                cleanup_task = asyncio.create_task(cleanup())
                cancelled = False
                while not cleanup_task.done():
                    try:
                        await asyncio.shield(cleanup_task)
                    except asyncio.CancelledError:
                        cancelled = True
                cleanup_task.result()
                if cancelled:
                    raise asyncio.CancelledError
