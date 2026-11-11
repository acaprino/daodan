"""Route table of the back-office service, mounted at /api/admin."""
from typing import Callable

ROUTES: dict[tuple[str, str], Callable] = {}


def route(method: str, path: str):
    def register(handler: Callable) -> Callable:
        ROUTES[(method, path)] = handler
        return handler
    return register
