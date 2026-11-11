"""Route table of the shop service, mounted at /api/shop."""
from typing import Callable

ROUTES: dict[tuple[str, str], Callable] = {}


def route(method: str, path: str):
    def register(handler: Callable) -> Callable:
        ROUTES[(method, path)] = handler
        return handler
    return register


def dispatch(method: str, path: str, body: dict | None = None):
    handler = ROUTES.get((method, path))
    if handler is None:
        return 404, {"error": "not found"}
    return 200, handler(body or {})
