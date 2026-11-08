"""Route table and a small HTTP server for local use: python -m server.routes from app/."""
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .audit import AuditLog
from .config import load_settings
from .handlers import Handlers, Request, Response
from .storage import NoteStore

NOTE = re.compile(r"/notes/([^/]+)")
MAX_BODY = 1 << 20


def dispatch(handlers: Handlers, request: Request) -> Response:
    if request.method == "GET" and request.path == "/notes":
        return handlers.list_page(request)
    match = NOTE.fullmatch(request.path)
    if match and request.method == "GET":
        return handlers.get_note(request, match.group(1))
    if match and request.method == "PUT":
        return handlers.put_note(request, match.group(1))
    return Response(404, '{"error": "not found"}')


def make_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    settings = load_settings()
    store = NoteStore(settings.data_dir, settings.max_note_bytes)
    handlers = Handlers(store, settings.token_secret, AuditLog(settings.data_dir / "audit.jsonl"))

    class Endpoint(BaseHTTPRequestHandler):
        def _serve(self) -> None:
            length = self.headers.get("Content-Length") or "0"
            if not length.isdigit() or int(length) > MAX_BODY:
                self.send_error(400 if not length.isdigit() else 413)
                return
            headers = {key.lower(): value for key, value in self.headers.items()}
            request = Request(self.command, self.path.split("?", 1)[0], headers, self.rfile.read(int(length)))
            response = dispatch(handlers, request)
            body = response.body.encode("utf-8")
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(body)))
            origin = headers.get("origin")
            if origin in settings.allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)

        do_GET = do_PUT = _serve

    return ThreadingHTTPServer((host, port), Endpoint)


if __name__ == "__main__":
    make_server().serve_forever()
