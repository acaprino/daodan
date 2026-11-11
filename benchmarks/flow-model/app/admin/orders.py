from .http import route

ARCHIVE: dict[str, dict] = {}


@route("GET", "/orders")
def list_all_orders(body: dict) -> list[dict]:
    return [dict(row, id=key) for key, row in sorted(ARCHIVE.items())]
