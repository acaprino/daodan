"""Authenticated, local-only and read-only web console."""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlencode, urlsplit

from .engine import Engine
from .errors import DefinitionError, ProcessError, StateError
from .views import Views

_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost"})
_MAX_SSE_CLIENTS = 4
_ASSETS = {
    "/": ("console.html", "text/html; charset=utf-8"),
    "/console.css": ("console.css", "text/css; charset=utf-8"),
    "/console.js": ("console.js", "text/javascript; charset=utf-8"),
}
_RUN = re.compile(r"^/api/run/([^/]+)$")
_RUN_EVENTS = re.compile(r"^/api/run/([^/]+)/events$")
_RUN_FRONTIER = re.compile(r"^/api/run/([^/]+)/frontier$")
_MAP = re.compile(r"^/api/map/([^/]+)$")
_ATTEMPT_LOG = re.compile(r"^/api/attempt/([^/]+)/log$")
_INTEGER = re.compile(r"^[0-9]+$")


class _ConsoleServer(ThreadingHTTPServer):
    """Threaded server with bounded SSE clients and cooperative shutdown."""

    daemon_threads = True

    def __init__(self, home: Path, workspace: Path, host: str, port: int):
        self.engine = Engine(home, workspace)
        self.views = Views(self.engine)
        self.token = secrets.token_urlsafe(32)
        self.shutdown_event = threading.Event()
        self.sse_heartbeat = 10.0
        self.sse_poll = 0.5
        self._sse_lock = threading.Lock()
        self._sse_clients = 0
        super().__init__((host, port), _RequestHandler)

    def acquire_sse(self) -> bool:
        with self._sse_lock:
            if self._sse_clients >= _MAX_SSE_CLIENTS:
                return False
            self._sse_clients += 1
            return True

    def release_sse(self) -> None:
        with self._sse_lock:
            self._sse_clients -= 1

    def shutdown(self) -> None:
        self.shutdown_event.set()
        super().shutdown()

    def server_close(self) -> None:
        self.shutdown_event.set()
        super().server_close()


class _RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ProcessControllerConsole/1.0"
    sys_version = ""

    @property
    def console(self) -> _ConsoleServer:
        return self.server  # type: ignore[return-value]

    def log_message(self, format: str, *args: Any) -> None:
        """Do not write URLs, which may contain a bootstrap token, to logs."""

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; font-src 'self'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        )

    def _send_bytes(
        self,
        body: bytes,
        *,
        status: int = 200,
        content_type: str = "application/json; charset=utf-8",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD" and body:
            self.wfile.write(body)

    def _send_json(
        self,
        payload: Any,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_bytes(body, status=status, headers=headers)

    def _error(self, status: int, message: str, *, headers: dict[str, str] | None = None) -> None:
        self._send_json({"error": message}, status=status, headers=headers)

    def _valid_host(self) -> bool:
        values = self.headers.get_all("Host", [])
        if len(values) != 1:
            return False
        value = values[0]
        if not value or value != value.strip() or value.count(":") > 1:
            return False
        hostname, separator, port = value.partition(":")
        if hostname.lower() not in _ALLOWED_HOSTS:
            return False
        if separator:
            if not port.isascii() or not port.isdigit():
                return False
            if int(port) != self.server.server_address[1]:
                return False
        return True

    def _matches_token(self, candidate: str) -> bool:
        return secrets.compare_digest(
            candidate.encode("utf-8"), self.console.token.encode("utf-8")
        )

    def _authorized(self, path: str, query: dict[str, list[str]]) -> bool:
        candidates = self.headers.get_all("X-Process-Controller-Token", [])
        if path == "/api/events/stream" and len(query.get("token", [])) == 1:
            candidates.append(query["token"][0])
        return any(self._matches_token(candidate) for candidate in candidates)

    def _parse_target(self) -> tuple[Any, dict[str, list[str]]]:
        target = urlsplit(self.path)
        if target.scheme or target.netloc or target.fragment or not target.path.startswith("/"):
            raise DefinitionError("request target must be an origin-relative path")
        try:
            query = parse_qs(target.query, keep_blank_values=True, max_num_fields=16)
        except ValueError as exc:
            raise DefinitionError("too many query fields") from exc
        return target, query

    @staticmethod
    def _identifier(value: str) -> str:
        try:
            decoded = unquote(value, encoding="utf-8", errors="strict")
        except (UnicodeError, ValueError) as exc:
            raise DefinitionError("resource identifier is not valid UTF-8") from exc
        if not decoded or any(character in decoded for character in ("/", "\\", "\x00")):
            raise DefinitionError("invalid resource identifier")
        return decoded

    @staticmethod
    def _query_one(query: dict[str, list[str]], name: str) -> str:
        values = query.get(name, [])
        if len(values) != 1 or not values[0]:
            raise DefinitionError(f"{name} is required exactly once")
        return values[0]

    @staticmethod
    def _query_integer(
        query: dict[str, list[str]], name: str, default: int, *, minimum: int = 0
    ) -> int:
        if name not in query:
            return default
        value = _RequestHandler._query_one(query, name)
        if not _INTEGER.fullmatch(value):
            raise DefinitionError(f"{name} must be a nonnegative integer")
        try:
            number = int(value)
        except ValueError as exc:
            raise DefinitionError(f"{name} is too large") from exc
        if number < minimum:
            raise DefinitionError(f"{name} must be at least {minimum}")
        return number

    def _serve_asset(self, path: str) -> None:
        filename, content_type = _ASSETS[path]
        body = (Path(__file__).with_name("assets") / filename).read_bytes()
        self._send_bytes(body, content_type=content_type)

    def _serve_api(self, path: str, query: dict[str, list[str]]) -> None:
        views = self.console.views
        if path == "/api/overview":
            self._send_json(views.overview())
            return
        if path == "/api/events/stream":
            run_id = self._query_one(query, "run_id")
            after = self._query_integer(query, "after", 0)
            self._serve_event_stream(run_id, after)
            return
        match = _RUN_EVENTS.fullmatch(path)
        if match:
            self._send_json(views.events(
                self._identifier(match[1]),
                after=self._query_integer(query, "after", 0),
                limit=self._query_integer(query, "limit", 20, minimum=1),
            ))
            return
        match = _RUN_FRONTIER.fullmatch(path)
        if match:
            run_id = self._identifier(match[1])
            self._send_json({"frontier": self.console.engine.frontier(run_id)})
            return
        match = _RUN.fullmatch(path)
        if match:
            self._send_json(views.run(self._identifier(match[1])))
            return
        match = _MAP.fullmatch(path)
        if match:
            self._send_json(views.map(self._identifier(match[1])))
            return
        match = _ATTEMPT_LOG.fullmatch(path)
        if match:
            self._send_json(views.attempt_log(
                self._identifier(match[1]),
                self._query_one(query, "stream"),
                max_bytes=self._query_integer(query, "max_bytes", 32768, minimum=1),
            ))
            return
        self._error(404, "resource not found")

    def _write_sse(self, event: str, payload: Any, *, event_id: int | None = None) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        prefix = f"id: {event_id}\n" if event_id is not None else ""
        self.wfile.write(f"{prefix}event: {event}\ndata: {data}\n\n".encode())
        self.wfile.flush()

    def _serve_event_stream(self, run_id: str, after: int) -> None:
        last_event_id = self.headers.get("Last-Event-ID")
        if last_event_id and last_event_id.isascii() and last_event_id.isdigit():
            after = max(after, int(last_event_id))
        self.console.views.events(run_id, after=after, limit=1)
        if self.command == "HEAD":
            self._send_bytes(b"", content_type="text/event-stream; charset=utf-8")
            return
        if not self.console.acquire_sse():
            self._error(429, "too many event stream clients", headers={"Retry-After": "2"})
            return
        try:
            self.send_response(200)
            self._security_headers()
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self._write_sse("ready", {"run_id": run_id, "after": after})
            cursor = after
            next_heartbeat = time.monotonic() + self.console.sse_heartbeat
            while not self.console.shutdown_event.is_set():
                events = self.console.views.events(run_id, after=cursor, limit=100)["events"]
                for item in events:
                    cursor = item["seq"]
                    self._write_sse("update", item, event_id=cursor)
                now = time.monotonic()
                if now >= next_heartbeat:
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
                    next_heartbeat = now + self.console.sse_heartbeat
                delay = min(self.console.sse_poll, max(0.01, next_heartbeat - now))
                if self.console.shutdown_event.wait(delay):
                    break
        except (BrokenPipeError, ConnectionResetError):
            pass
        except (ProcessError, OSError, sqlite3.Error):
            try:
                self._write_sse("stream-error", {"error": "event stream interrupted"})
            except OSError:
                pass
        finally:
            self.close_connection = True
            self.console.release_sse()

    def _dispatch(self) -> None:
        if not self._valid_host():
            self._error(403, "invalid Host header")
            return
        try:
            target, query = self._parse_target()
            if target.path in _ASSETS:
                self._serve_asset(target.path)
            elif not self._authorized(target.path, query):
                self._error(401, "valid token required")
            elif target.path.startswith("/api/"):
                self._serve_api(target.path, query)
            else:
                self._error(404, "resource not found")
        except DefinitionError as exc:
            self._error(400, str(exc))
        except StateError as exc:
            status = 404 if str(exc).startswith("unknown ") else 409
            self._error(status, str(exc))
        except ProcessError as exc:
            self._error(400, str(exc))
        except (OSError, sqlite3.Error):
            self._error(503, "local state is temporarily unavailable")

    def _reject_method(self) -> None:
        if not self._valid_host():
            self._error(403, "invalid Host header")
            return
        self._error(405, "method not allowed", headers={"Allow": "GET, HEAD"})

    def do_GET(self) -> None:
        self._dispatch()

    def do_HEAD(self) -> None:
        self._dispatch()

    def do_POST(self) -> None:
        self._reject_method()

    def do_PUT(self) -> None:
        self._reject_method()

    def do_DELETE(self) -> None:
        self._reject_method()

    def do_PATCH(self) -> None:
        self._reject_method()

    def do_OPTIONS(self) -> None:
        self._reject_method()

    def do_TRACE(self) -> None:
        self._reject_method()


def create_server(
    home: Path,
    workspace: Path,
    host: str = "127.0.0.1",
    port: int = 0,
) -> ThreadingHTTPServer:
    """Create a bound loopback-only server; no request thread is started."""

    if not isinstance(host, str) or host.lower() not in _ALLOWED_HOSTS:
        raise ValueError("web console host must be 127.0.0.1 or localhost")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("web console port must be in 0..65535")
    return _ConsoleServer(home, workspace, host, port)


def serve(
    home: Path,
    workspace: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """Print the bootstrap URL and serve until interrupted with Ctrl+C."""

    server = create_server(home, workspace, host=host, port=port)
    bound_port = server.server_address[1]
    query = urlencode({"token": server.token})
    print(f"Work Controller console: http://{host}:{bound_port}/#{query}", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown_event.set()
        server.server_close()
