"""Project-level store for Meta-Code cards.

A card is a model's reading of one symbol (purpose, contracts, side effects). It is
the one thing in the Codebase Map that must outlive a run. A run's snapshot is
immutable evidence, bound by digest to the artifacts that inherit from it, so cards
cannot live in it. They live beside the runs, in one SQLite file of the analysis
root, and carry the digests of the symbol they were written against. Whether a card
is still fresh is decided when it is read, by comparing those digests with the
snapshot being queried (semantic_store). This module only stores and validates.

Standard library only.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from snapshot_store import _pack, _plain, _unpack

__all__ = [
    "CARD_STORE_NAME", "CARD_LIST_KEYS", "CARD_TEXT_KEYS", "default_cards_path",
    "digests", "read_cards", "validate_card", "write_cards",
]

CARD_STORE_NAME = "cards.sqlite"
APPLICATION_ID = 0x44434152  # "DCAR"
STORAGE_VERSION = 1
MAX_CARD_BYTES = 8 * 1024
MAX_FIELD_ITEMS = 40
MAX_TEXT = 2_000
BUSY_TIMEOUT_MS = 10_000

CARD_TEXT_KEYS = ("purpose", "notes", "confidence")
CARD_LIST_KEYS = ("preconditions", "postconditions", "invariants", "side_effects", "failure_modes")
_IDENTITY_KEYS = ("symbol_id", "file", "symbol")

_SCHEMA = f"""
    PRAGMA application_id={APPLICATION_ID};
    PRAGMA user_version={STORAGE_VERSION};
    CREATE TABLE cards(
        root TEXT NOT NULL, symbol_id TEXT NOT NULL, file TEXT NOT NULL,
        symbol TEXT NOT NULL, kind TEXT NOT NULL,
        body_hash TEXT NOT NULL, interface_hash TEXT NOT NULL, effects_hash TEXT NOT NULL,
        callee_digest TEXT NOT NULL, updated_at TEXT NOT NULL, payload BLOB NOT NULL,
        PRIMARY KEY(root, symbol_id)
    );
    CREATE INDEX cards_file ON cards(root, file);
"""


def default_cards_path(manifest: Path | str) -> Path:
    """The card store of the analysis a snapshot belongs to.

    A run snapshot is `<root>/runs/<id>/snapshot/manifest.<format>` and its store is
    `<root>/cards.sqlite`. A snapshot anywhere else keeps its store beside itself.
    """
    manifest = Path(manifest).resolve()
    run = manifest.parent.parent
    if manifest.parent.name == "snapshot" and run.parent.name == "runs" and (run / "state.json").is_file():
        return run.parent.parent / CARD_STORE_NAME
    return manifest.parent / CARD_STORE_NAME


def validate_card(card: object) -> dict:
    """The stored fields of a card, or ValueError.

    Unknown keys are refused instead of dropped: a misspelled `side_effect` that
    vanished silently would leave a card that looks complete and is not.
    """
    if not isinstance(card, dict):
        raise ValueError("a card must be an object")
    allowed = {*_IDENTITY_KEYS, *CARD_TEXT_KEYS, *CARD_LIST_KEYS}
    unknown = sorted(set(card) - allowed)
    if unknown:
        raise ValueError(f"unknown card field(s): {', '.join(map(str, unknown))}")
    payload: dict = {}
    for key in CARD_TEXT_KEYS:
        if key in card:
            value = card[key]
            if not isinstance(value, str) or len(value) > MAX_TEXT:
                raise ValueError(f"{key} must be text of at most {MAX_TEXT} characters")
            payload[key] = value
    for key in CARD_LIST_KEYS:
        if key in card:
            value = card[key]
            if (not isinstance(value, list) or len(value) > MAX_FIELD_ITEMS
                    or any(not isinstance(item, str) or len(item) > MAX_TEXT for item in value)):
                raise ValueError(f"{key} must be a list of at most {MAX_FIELD_ITEMS} texts")
            payload[key] = value
    if not payload:
        raise ValueError("a card needs at least one of: " + ", ".join((*CARD_TEXT_KEYS, *CARD_LIST_KEYS)))
    if len(_pack(payload)) > MAX_CARD_BYTES:
        raise ValueError(f"a card must pack to at most {MAX_CARD_BYTES} bytes")
    return payload


@contextmanager
def _connection(path: Path, *, create: bool = False, write: bool = False):
    path = Path(path)
    _plain(path)
    if not path.exists():
        if not create:
            raise FileNotFoundError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as fresh:
            fresh.executescript(_SCHEMA)
    uri = path.resolve().as_uri() + ("" if write else "?mode=ro")
    try:
        db = sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_MS / 1000, isolation_level=None)
    except sqlite3.Error as error:
        raise ValueError(f"cannot open card store {path}: {error}") from error
    with closing(db):
        try:
            identity = db.execute("PRAGMA application_id").fetchone()[0]
            version = db.execute("PRAGMA user_version").fetchone()[0]
        except sqlite3.Error as error:
            raise ValueError(f"not a card store: {path}") from error
        if identity != APPLICATION_ID:
            raise ValueError(f"not a card store: {path}")
        if version != STORAGE_VERSION:
            raise ValueError(f"unsupported card store version: {path}")
        yield db


def write_cards(path: Path | str, root: str, rows: list[dict]) -> None:
    """Insert or replace cards, all or none. Each row holds the identity, kind, the
    three digests and the callee digest the card was written against, and its payload."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _connection(Path(path), create=True, write=True) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            db.executemany(
                "INSERT OR REPLACE INTO cards VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                [(root, row["symbol_id"], row["file"], row["symbol"], row["kind"], row["body_hash"],
                  row["interface_hash"], row["effects_hash"], row["callee_digest"], now,
                  _pack(row["payload"])) for row in rows],
            )
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise


def digests(path: Path | str, root: str) -> list[tuple]:
    """(symbol_id, file, symbol, body, interface, effects, callee, updated_at) of
    every card of a root, without payloads. A missing store holds no cards."""
    try:
        with _connection(Path(path)) as db:
            return db.execute(
                "SELECT symbol_id,file,symbol,body_hash,interface_hash,effects_hash,callee_digest,updated_at "
                "FROM cards WHERE root=? ORDER BY file,symbol_id", (root,)).fetchall()
    except FileNotFoundError:
        return []


def read_cards(path: Path | str, root: str, symbol_ids: list[str]) -> dict[str, dict]:
    """The stored fields of the named cards, by symbol id."""
    found: dict[str, dict] = {}
    if not symbol_ids:
        return found
    try:
        with _connection(Path(path)) as db:
            for start in range(0, len(symbol_ids), 500):
                chunk = symbol_ids[start:start + 500]
                marks = ",".join("?" for _ in chunk)
                for symbol_id, updated_at, payload in db.execute(
                        f"SELECT symbol_id,updated_at,payload FROM cards WHERE root=? AND symbol_id IN ({marks})",
                        (root, *chunk)):
                    found[symbol_id] = {"updated_at": updated_at, **_unpack(payload)}
    except FileNotFoundError:
        pass
    return found
