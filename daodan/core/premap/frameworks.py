"""The helpers the framework sources of `FRAMEWORK_SOURCES` and `TEMPLATE_SOURCES` share; no framework in it."""
from __future__ import annotations

import json
from pathlib import PurePosixPath


def folders(context, names) -> list[str]:
    """The folders whose `package.json` declares any of `names` in `dependencies` or `devDependencies`, in the inventory's order;
    one that is not valid JSON, or not an object, is skipped: `npm-files` reports it."""
    found = []
    for rel in context.inventory.files:
        if PurePosixPath(rel).name != "package.json":
            continue
        try:
            manifest = json.loads(context.inventory.text(rel))
        except ValueError:
            continue
        if isinstance(manifest, dict) and any(isinstance(manifest.get(section), dict) and name in manifest[section]
                                              for section in ("dependencies", "devDependencies") for name in names):
            found.append(PurePosixPath(rel).parent.as_posix())
    return found


def nearest_first(folders: list[str]) -> list[str]:
    """The deepest first, the root last."""
    return sorted(folders, key=lambda folder: (folder == ".", -len(folder), folder))


def folder_of(folders: list[str], file: str) -> str | None:
    """The first of `folders` that holds `file` (the nearest, when they are `nearest_first`)."""
    return next((folder for folder in folders if folder == "." or file.startswith(folder + "/")), None)


def excerpt(result: dict) -> str:
    """What the tool said: both ends when it is long, the cause is first in React Router's and the stack after it, and Remix
    writes its warnings first."""
    text = (result["stderr"] or result["stdout"]).strip()
    return text if len(text) <= 600 else f"{text[:300]} [...] {text[-300:]}"


def starts(db, resolver, file: str, names: list[str]) -> tuple[list[tuple[str, str, int]], list[str]]:
    """The exports of a file that name a function of the snapshot, `(export, qualified name, line)`, and why the others do
    not: an export that the file does not make (`export-missing`) is no reason (a route module has the exports it needs), one the
    file makes in several records (`export-ambiguous`: an overload, a value and a type of one name) or the snapshot's own records
    cannot follow (a re-export, a name that is no function) is. Nothing here picks one of several records: it is a gap."""
    from snapshot_store import _unpack
    found, unread = [], []
    for name in names:
        identity, reason = resolver.exported_target(file, name)
        if identity:
            declared = db.execute("SELECT name,l0,payload FROM sem_declarations WHERE id=?", (identity,)).fetchone()
            found.append((name, _unpack(declared[2]).get("qualified_name") or declared[0], declared[1]))
        elif reason != "export-missing":
            unread.append(f"{name}: {reason}")
    return found, unread


def column_bytes(line: str, units: int) -> int:
    """The column in bytes, as the snapshot writes it, of a column the compiler gives in UTF-16 code units."""
    seen = 0
    for index, char in enumerate(line):
        if seen >= units:
            return len(line[:index].encode("utf-8"))
        seen += 2 if ord(char) > 0xFFFF else 1
    return len(line.encode("utf-8"))
