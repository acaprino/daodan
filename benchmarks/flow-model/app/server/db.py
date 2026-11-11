"""Document store of the shop service: collections of JSON documents by key."""
_COLLECTIONS: dict[str, dict[str, dict]] = {}


def put(collection: str, key: str, document: dict) -> None:
    _COLLECTIONS.setdefault(collection, {})[key] = dict(document)


def get(collection: str, key: str) -> dict | None:
    return _COLLECTIONS.get(collection, {}).get(key)


def find(collection: str, **fields) -> list[dict]:
    return [doc for doc in _COLLECTIONS.get(collection, {}).values()
            if all(doc.get(name) == value for name, value in fields.items())]
