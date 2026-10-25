"""Read-only MCP stdio interface backed by the shared bounded views."""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from . import __version__
from .engine import Engine
from .errors import ProcessError
from .views import Views

MODERN_VERSION = "2026-07-28"
LEGACY_VERSION = "2025-11-25"
MAX_MESSAGE_BYTES = 1024 * 1024
_RATE_LIMIT = 120
_RATE_WINDOW_SECONDS = 60.0
_RATE_LIMIT_ERROR = -31900

_PROTOCOL_META = "io.modelcontextprotocol/protocolVersion"
_CLIENT_INFO_META = "io.modelcontextprotocol/clientInfo"
_CLIENT_CAPABILITIES_META = "io.modelcontextprotocol/clientCapabilities"
_SERVER_INFO_META = "io.modelcontextprotocol/serverInfo"
_MODERN_META_KEYS = {_PROTOCOL_META, _CLIENT_INFO_META, _CLIENT_CAPABILITIES_META}
_SERVER_INFO = {"name": "work-controller", "version": __version__}
_INSTRUCTIONS = (
    "Read-only Work Controller inspection. Use the bounded run, event, map and "
    "supervision tools; artifact bodies, logs and process definitions are not exposed."
)


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


class _RPCError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def _invalid_params(message: str) -> _RPCError:
    return _RPCError(-32602, "Invalid params", {"detail": message})


def _schema(
    properties: dict[str, Any] | None = None,
    required: tuple[str, ...] = (),
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "object",
        "properties": properties or {},
        "additionalProperties": False,
    }
    if required:
        result["required"] = list(required)
    return result


def _identifier(description: str) -> dict[str, Any]:
    return {"type": "string", "minLength": 1, "maxLength": 256, "description": description}


_LIMIT = {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}
_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
_TOOLS = (
    {
        "name": "process_runs",
        "description": "List recent runs without the map overview.",
        "inputSchema": _schema({"limit": _LIMIT}),
        "annotations": _READ_ONLY,
    },
    {
        "name": "process_run_status",
        "description": "Return the bounded status and job counts for one run.",
        "inputSchema": _schema({"run_id": _identifier("Run identifier")}, ("run_id",)),
        "annotations": _READ_ONLY,
    },
    {
        "name": "process_run_detail",
        "description": "Return the shared bounded detail projection for one run.",
        "inputSchema": _schema({"run_id": _identifier("Run identifier")}, ("run_id",)),
        "annotations": _READ_ONLY,
    },
    {
        "name": "process_frontier",
        "description": "Return currently runnable jobs for one run.",
        "inputSchema": _schema({"run_id": _identifier("Run identifier")}, ("run_id",)),
        "annotations": _READ_ONLY,
    },
    {
        "name": "process_events",
        "description": "Return a bounded page of run events after a sequence number.",
        "inputSchema": _schema(
            {
                "run_id": _identifier("Run identifier"),
                "after": {"type": "integer", "minimum": 0, "maximum": 9223372036854775807, "default": 0},
                "limit": _LIMIT,
            },
            ("run_id",),
        ),
        "annotations": _READ_ONLY,
    },
    {
        "name": "process_map_status",
        "description": "Return map status and its bounded ticket projection.",
        "inputSchema": _schema({"map_id": _identifier("Map identifier")}, ("map_id",)),
        "annotations": _READ_ONLY,
    },
    {
        "name": "process_supervise",
        "description": "Return deterministic, non-authoritative supervision advice for an attempt.",
        "inputSchema": _schema(
            {"attempt_id": _identifier("Attempt identifier")}, ("attempt_id",)
        ),
        "annotations": _READ_ONLY,
    },
)
_TOOL_BY_NAME = {tool["name"]: tool for tool in _TOOLS}


def _response_meta() -> dict[str, Any]:
    return {_SERVER_INFO_META: dict(_SERVER_INFO)}


def _validate_implementation(value: Any, field: str) -> None:
    if not isinstance(value, dict):
        raise _invalid_params(f"{field} must be an object")
    for key in ("name", "version"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise _invalid_params(f"{field}.{key} must be a nonempty string")


def _reject_unknown_params(params: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(params) - allowed - {"_meta"})
    if unknown:
        raise _invalid_params("unknown params field(s): " + ", ".join(unknown))


class _MCPService:
    def __init__(self, home: Path, workspace: Path):
        self.engine = Engine(home, workspace)
        self.views = Views(self.engine)
        self.legacy_phase = "new"
        self.rate_limit = _RATE_LIMIT
        self.rate_started = time.monotonic()
        self.rate_count = 0

    def _debug(self, method: str) -> None:
        if os.environ.get("WORK_CONTROLLER_MCP_DEBUG", os.environ.get("PROCESS_CONTROLLER_MCP_DEBUG")) == "1":
            print(f"work-controller MCP method={method!r}", file=sys.stderr)

    def _check_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self.rate_started
        if elapsed >= _RATE_WINDOW_SECONDS:
            self.rate_started = now
            self.rate_count = 0
            elapsed = 0.0
        if self.rate_count >= self.rate_limit:
            retry_ms = max(1, int((_RATE_WINDOW_SECONDS - elapsed) * 1000))
            raise _RPCError(
                _RATE_LIMIT_ERROR,
                "Rate limit exceeded",
                {"limit": self.rate_limit, "retryAfterMs": retry_ms},
            )
        self.rate_count += 1

    def _require_modern_meta(self, params: dict[str, Any]) -> None:
        meta = params.get("_meta")
        if not isinstance(meta, dict):
            raise _invalid_params("params._meta must contain the MCP 2026-07-28 protocol fields")
        version = meta.get(_PROTOCOL_META)
        if not isinstance(version, str) or not version:
            raise _invalid_params(f"params._meta[{_PROTOCOL_META!r}] is required")
        if version != MODERN_VERSION:
            raise _RPCError(
                -32022,
                "Unsupported protocol version",
                {"supported": [MODERN_VERSION, LEGACY_VERSION], "requested": version},
            )
        if _CLIENT_INFO_META not in meta:
            raise _invalid_params(f"params._meta[{_CLIENT_INFO_META!r}] is required")
        _validate_implementation(meta[_CLIENT_INFO_META], f"params._meta[{_CLIENT_INFO_META!r}]")
        if not isinstance(meta.get(_CLIENT_CAPABILITIES_META), dict):
            raise _invalid_params(
                f"params._meta[{_CLIENT_CAPABILITIES_META!r}] must be an object"
            )

    def _is_modern(self, method: str, params: dict[str, Any]) -> bool:
        meta = params.get("_meta")
        if meta is not None and not isinstance(meta, dict):
            return True
        if isinstance(meta, dict) and _MODERN_META_KEYS.intersection(meta):
            return True
        return method in {"tools/list", "tools/call"} and self.legacy_phase == "new"

    def _initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        if self.legacy_phase != "new":
            raise _RPCError(-32600, "Invalid Request", {"detail": "initialize was already accepted"})
        _reject_unknown_params(params, {"protocolVersion", "capabilities", "clientInfo"})
        if not isinstance(params.get("protocolVersion"), str) or not params["protocolVersion"]:
            raise _invalid_params("protocolVersion must be a nonempty string")
        if not isinstance(params.get("capabilities"), dict):
            raise _invalid_params("capabilities must be an object")
        _validate_implementation(params.get("clientInfo"), "clientInfo")
        self.legacy_phase = "initializing"
        return {
            "protocolVersion": LEGACY_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": dict(_SERVER_INFO),
            "instructions": _INSTRUCTIONS,
        }

    def _list_tools(self, params: dict[str, Any], *, modern: bool) -> dict[str, Any]:
        _reject_unknown_params(params, set())
        if modern:
            return {
                "resultType": "complete",
                "tools": list(_TOOLS),
                "ttlMs": 300000,
                "cacheScope": "private",
                "_meta": _response_meta(),
            }
        return {"tools": list(_TOOLS)}

    @staticmethod
    def _validate_arguments(name: str, arguments: dict[str, Any]) -> None:
        schema = _TOOL_BY_NAME[name]["inputSchema"]
        properties = schema["properties"]
        unknown = sorted(set(arguments) - set(properties))
        if unknown:
            raise _invalid_params(
                f"unknown argument(s) for {name}: " + ", ".join(unknown)
            )
        for key in schema.get("required", []):
            if key not in arguments:
                raise _invalid_params(f"{name}.{key} is required")
        for key, value in arguments.items():
            spec = properties[key]
            if spec["type"] == "string":
                if (
                    not isinstance(value, str)
                    or not value.strip()
                    or len(value) > spec.get("maxLength", 256)
                ):
                    raise _invalid_params(f"{name}.{key} must be a nonempty string")
            elif type(value) is not int:
                raise _invalid_params(f"{name}.{key} must be an integer")
            if "minimum" in spec and value < spec["minimum"]:
                raise _invalid_params(f"{name}.{key} must be at least {spec['minimum']}")
            if "maximum" in spec and value > spec["maximum"]:
                raise _invalid_params(f"{name}.{key} must be at most {spec['maximum']}")

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "process_runs":
            return {"runs": self.views.overview(limit=arguments.get("limit", 20))["runs"]}
        if name == "process_run_status":
            return self.views.status(arguments["run_id"])
        if name == "process_run_detail":
            return self.views.run(arguments["run_id"])
        if name == "process_frontier":
            return {"frontier": self.engine.frontier(arguments["run_id"])}
        if name == "process_events":
            return self.views.events(
                arguments["run_id"],
                after=arguments.get("after", 0),
                limit=arguments.get("limit", 20),
            )
        if name == "process_map_status":
            return self.views.map(arguments["map_id"])
        return self.engine.supervise(arguments["attempt_id"])

    def _tool_result(
        self, payload: dict[str, Any], *, modern: bool, is_error: bool = False
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "content": [{"type": "text", "text": _compact_json(payload)}],
            "structuredContent": payload,
            "isError": is_error,
        }
        if modern:
            return {"resultType": "complete", **result, "_meta": _response_meta()}
        return result

    def _call_tool(self, params: dict[str, Any], *, modern: bool) -> dict[str, Any]:
        _reject_unknown_params(params, {"name", "arguments"})
        name = params.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 128:
            raise _invalid_params("tools/call.name must be a nonempty string of at most 128 characters")
        if name not in _TOOL_BY_NAME:
            raise _RPCError(-32602, f"Unknown tool: {name}")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            raise _invalid_params("tools/call.arguments must be an object")
        self._validate_arguments(name, arguments)
        try:
            payload = self._execute_tool(name, arguments)
        except ProcessError as exc:
            message = f"{exc}; check the identifier and selected home/workspace, then retry"
            return self._tool_result({"error": message}, modern=modern, is_error=True)
        except (OSError, sqlite3.Error):
            message = "local state is unavailable; check home/workspace permissions and available storage, then retry"
            return self._tool_result({"error": message}, modern=modern, is_error=True)
        return self._tool_result(payload, modern=modern)

    def _discover(self, params: dict[str, Any]) -> dict[str, Any]:
        self._require_modern_meta(params)
        _reject_unknown_params(params, set())
        return {
            "resultType": "complete",
            "supportedVersions": [MODERN_VERSION, LEGACY_VERSION],
            "capabilities": {"tools": {}},
            "_meta": _response_meta(),
            "instructions": _INSTRUCTIONS,
            "ttlMs": 3600000,
            "cacheScope": "private",
        }

    def _dispatch_modern(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._require_modern_meta(params)
        if method == "tools/list":
            return self._list_tools(params, modern=True)
        if method == "tools/call":
            return self._call_tool(params, modern=True)
        if method == "ping":
            _reject_unknown_params(params, set())
            return {"resultType": "complete", "_meta": _response_meta()}
        raise _RPCError(-32601, "Method not found")

    def _dispatch_legacy(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "ping":
            _reject_unknown_params(params, set())
            return {}
        if method not in {"tools/list", "tools/call"}:
            raise _RPCError(-32601, "Method not found")
        if self.legacy_phase != "ready":
            raise _invalid_params(
                "legacy server is not initialized; send initialize, then notifications/initialized"
            )
        if method == "tools/list":
            return self._list_tools(params, modern=False)
        return self._call_tool(params, modern=False)

    def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            return self._initialize(params)
        if method == "server/discover":
            return self._discover(params)
        if self._is_modern(method, params):
            return self._dispatch_modern(method, params)
        return self._dispatch_legacy(method, params)

    def handle(self, message: Any) -> dict[str, Any] | None:
        request_id = message.get("id") if isinstance(message, dict) else None
        if isinstance(request_id, bool) or not isinstance(request_id, (str, int, type(None))):
            request_id = None
        try:
            if not isinstance(message, dict):
                raise _RPCError(-32600, "Invalid Request")
            if message.get("jsonrpc") != "2.0":
                raise _RPCError(-32600, "Invalid Request")
            method = message.get("method")
            if not isinstance(method, str) or not method:
                raise _RPCError(-32600, "Invalid Request")
            has_id = "id" in message
            if has_id and (
                isinstance(message["id"], bool)
                or not isinstance(message["id"], (str, int))
            ):
                raise _RPCError(-32600, "Invalid Request")
            self._debug(method)
            if not has_id:
                params = message.get("params", {})
                if (
                    method == "notifications/initialized"
                    and self.legacy_phase == "initializing"
                    and isinstance(params, dict)
                ):
                    self.legacy_phase = "ready"
                return None
            params = message.get("params", {})
            if not isinstance(params, dict):
                raise _invalid_params("params must be an object")
            if "_meta" in params and not isinstance(params["_meta"], dict):
                raise _invalid_params("params._meta must be an object")
            self._check_rate_limit()
            result = self._dispatch(method, params)
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except _RPCError as exc:
            error: dict[str, Any] = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            return {"jsonrpc": "2.0", "id": request_id, "error": error}
        except Exception:  # noqa: BLE001 - JSON-RPC must not leak implementation failures.
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": "Internal error"},
            }


def _oversized(raw: bytes | str, payload: bytes | str) -> bool:
    size = len(payload if isinstance(payload, bytes) else payload.encode("utf-8"))
    return size > MAX_MESSAGE_BYTES


def _drain_line(stdin: Any) -> None:
    while True:
        raw = stdin.readline(MAX_MESSAGE_BYTES + 2)
        if raw in (b"", "") or raw.endswith(b"\n" if isinstance(raw, bytes) else "\n"):
            return


def _parse_line(stdin: Any, raw: bytes | str) -> Any:
    newline = b"\n" if isinstance(raw, bytes) else "\n"
    carriage_return = b"\r" if isinstance(raw, bytes) else "\r"
    has_newline = raw.endswith(newline)
    payload = raw[:-1] if has_newline else raw
    if payload.endswith(carriage_return):
        payload = payload[:-1]
    try:
        if _oversized(raw, payload):
            if not has_newline:
                _drain_line(stdin)
            raise _RPCError(
                -32600,
                "Invalid Request",
                {"detail": f"message exceeds the {MAX_MESSAGE_BYTES}-byte limit"},
            )
    except UnicodeEncodeError as exc:
        raise _RPCError(-32700, "Parse error", {"detail": "message is not valid UTF-8"}) from exc
    try:
        text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    except UnicodeDecodeError as exc:
        raise _RPCError(-32700, "Parse error", {"detail": "message is not valid UTF-8"}) from exc

    def reject_constant(value: str) -> None:
        raise ValueError(f"invalid JSON constant: {value}")

    try:
        return json.loads(text, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise _RPCError(-32700, "Parse error") from exc


def _write_response(stdout: Any, response: dict[str, Any]) -> None:
    line = _compact_json(response) + "\n"
    if isinstance(stdout, io.TextIOBase):
        stdout.write(line)
    else:
        try:
            stdout.write(line.encode("utf-8"))
        except TypeError:
            stdout.write(line)
    stdout.flush()


def run_stdio(home: Path, workspace: Path, stdin=None, stdout=None) -> None:
    """Serve newline-delimited JSON-RPC until EOF; never mutate graph state."""
    if stdin is None:
        stdin = getattr(sys.stdin, "buffer", sys.stdin)
    if stdout is None:
        stdout = getattr(sys.stdout, "buffer", sys.stdout)
    service = _MCPService(home, workspace)
    while True:
        raw = stdin.readline(MAX_MESSAGE_BYTES + 2)
        if raw in (b"", ""):
            return
        try:
            message = _parse_line(stdin, raw)
            response = service.handle(message)
        except _RPCError as exc:
            error: dict[str, Any] = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            response = {"jsonrpc": "2.0", "id": None, "error": error}
        if response is not None:
            try:
                _write_response(stdout, response)
            except BrokenPipeError:
                return
