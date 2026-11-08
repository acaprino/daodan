"""Request handlers for reading, writing and listing notes."""
import json
from dataclasses import dataclass, field

from .audit import AuditLog
from .auth import AuthError, require_user
from .render import note_list_page
from .storage import NoteStore, StorageError


@dataclass
class Request:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""


@dataclass
class Response:
    status: int
    body: str
    content_type: str = "application/json"


def _error(status: int, message: str) -> Response:
    return Response(status, json.dumps({"error": message}))


class Handlers:
    def __init__(self, store: NoteStore, secret: bytes, audit: AuditLog):
        self.store = store
        self.secret = secret
        self.audit = audit

    def _user(self, request: Request) -> str:
        return require_user(self.secret, request.headers)

    def get_note(self, request: Request, name: str) -> Response:
        try:
            user = self._user(request)
            return Response(200, json.dumps({"name": name, "text": self.store.read(user, name)}))
        except AuthError:
            return _error(401, "unauthorized")
        except StorageError as error:
            return _error(404, str(error))

    def put_note(self, request: Request, name: str) -> Response:
        try:
            user = self._user(request)
            payload = json.loads(request.body.decode("utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
                return _error(400, "text must be a string")
            self.store.write(user, name, payload["text"])
            self.audit.record(user, "write", name)
            return Response(204, "")
        except AuthError:
            return _error(401, "unauthorized")
        except (ValueError, StorageError) as error:
            return _error(400, str(error))

    def list_page(self, request: Request) -> Response:
        try:
            user = self._user(request)
        except AuthError:
            return _error(401, "unauthorized")
        return Response(200, note_list_page(user, self.store.names(user)), "text/html; charset=utf-8")
