"""A position graded against the snapshot's own declarations (`grade`, `symbol_table`), the callee's column of a
call (`callee_column`) and the sources a reader may trust (`verify_sources`)."""
from __future__ import annotations

import hashlib
import io
import tokenize
import unicodedata
from pathlib import Path

from source_reader import _binding, _source_path
from snapshot_store import _unpack
from source_positions import char_to_byte


def callee_column(source_line: str, span: list[int], last_part: str) -> int | None:
    """The UTF-8 byte column of the callee's name, the snapshot's unit.

    For a multiline expression, the supplied line is the span's final line. A
    callee ends at its span's end; a matching substring elsewhere in its receiver
    is insufficient evidence of its position.
    """
    start, end = (span[1] if span[0] == span[2] else 0), span[3]
    encoded = source_line.encode("utf-8")
    if not last_part or not 0 <= start < end <= len(encoded):
        return None
    try:
        window = encoded[start:end].decode("utf-8")
    except UnicodeError:
        return None
    if not window.endswith(last_part):
        return None
    return end - len(last_part.encode("utf-8"))


def _python_name_positions(source: str) -> dict:
    """`(kind, line, byte column of def/async/class)` to `(name, line, byte column of the name)`."""
    names = {}
    previous = None
    declaration = None
    lines = source.split("\n")
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if declaration is not None and token.type == tokenize.NAME:
                row, column = token.start
                names[declaration] = (unicodedata.normalize("NFKC", token.string), row,
                                      char_to_byte(lines[row - 1], column))
                declaration = None
            if token.type == tokenize.NAME and token.string in ("def", "class"):
                line, column = token.start
                if token.string == "def" and previous is not None \
                        and previous.type == tokenize.NAME and previous.string == "async":
                    line, column = previous.start
                declaration = ("function" if token.string == "def" else "class", line,
                               char_to_byte(lines[line - 1], column))
            previous = token
    except (tokenize.TokenError, IndentationError):
        # Declarations recorded before a damaged suffix stay usable only where the
        # snapshot independently holds their exact spans.
        pass
    return names


def symbol_table(connection, rel: str, source: str) -> tuple[dict, set]:
    """Where each function, method and class of a file is named: `(line, byte column)` to `(id, kind)`.

    An engine answers with the position of a declaration's name, and only that
    position binds it to this snapshot: a matching bare name elsewhere proves no
    edge. Tree-sitter adapters record the name as `name_span`, and the names of a
    body's overload signatures as `signature_spans`; Python's AST gives
    only the statement start, so its names come from tokenizing the verified
    source. Two declarations named at one position are ambiguous, never a first match.
    """
    python = rel.lower().endswith((".py", ".pyi"))
    python_names = _python_name_positions(source) if python else {}
    table: dict = {}
    ambiguous: set = set()
    # A value binding is where a callable is held, not what is called: it never
    # becomes a target, and a callable named at the same position wins.
    bindings = {(line, column): (identity, "binding") for identity, line, column in connection.execute(
        "SELECT id, l0, c0 FROM sem_declarations WHERE file=? AND kind IN ('binding','parameter','property')",
        (rel,))}
    for identity, name, kind, line, column, blob in connection.execute(
            "SELECT id, name, kind, l0, c0, payload FROM sem_declarations "
            "WHERE file=? AND kind IN ('function','method','class') ORDER BY l0,c0", (rel,)):
        kind = "function" if kind == "method" else kind
        if python:
            found = python_names.get((kind, line, column))
            if found is None or found[0] != name:
                continue
            keys = [found[1:]]
        else:
            payload = _unpack(blob) or {}
            if not payload.get("name_span"):
                continue
            if payload.get("constructs"):
                identity, kind = f"{rel}::{payload['constructs']}", "class"
            # Overload signatures name the same body as the implementation's own name.
            keys = [(span[0], span[1]) for span in (payload["name_span"], *payload.get("signature_spans", ()))]
        for key in keys:
            if key in table and table[key][0] != identity:
                ambiguous.add(key)
            table.setdefault(key, (identity, kind))
    for key, value in bindings.items():
        table.setdefault(key, value)
    return table, ambiguous


def inventory_files(connection) -> set[str]:
    return {row[0] for row in connection.execute(
        "SELECT file FROM sem_coverage WHERE status IN ('ast', 'partial')")}


def grade(definition, inventory: set[str], tables: dict, root: Path,
          table_for) -> tuple[str, dict | None]:
    """One engine answer, graded by what this snapshot declares at that position.

    Returns `(verdict, target)` where verdict is `edge-call`, `edge-instantiation`,
    `external-definition`, `project-not-a-symbol`, `ambiguous-target`, `unresolved`
    or `binding` (a value binding, never kept as a call's target),
    and target carries the declaration identity an edge arrives at. The kind comes
    from the snapshot's declaration, never from the engine.
    """
    if definition is None:
        return "unresolved", None
    module_path = getattr(definition, "module_path", None)
    if not module_path:
        return "external-definition", None
    try:
        relative = Path(module_path).resolve().relative_to(root).as_posix()
    except ValueError:
        return "external-definition", None
    if relative not in inventory:
        # Inside the project directory but not in the snapshot: a virtual
        # environment, a build output, a file the perimeter leaves out. Counting
        # exactly these as project code was the measured harness defect that made
        # the published gap three times its real size.
        return "external-definition", None
    if relative not in tables:
        tables[relative] = table_for(relative)
    table, ambiguous = tables[relative]
    line = getattr(definition, "line", None)
    column = getattr(definition, "column", None)
    if type(line) is not int or type(column) is not int:
        return "project-not-a-symbol", None
    if (line, column) in ambiguous:
        return "ambiguous-target", None
    found = table.get((line, column))
    if found is None:
        return "project-not-a-symbol", None
    identity, kind = found
    if kind == "binding":  # the declaration the engine names, for a caller that reads a value's identity; no edge
        return "binding", {"id": identity, "file": relative, "kind": kind}
    verdict = "edge-instantiation" if kind == "class" else "edge-call"
    return verdict, {"id": identity, "file": relative, "kind": kind}


def verify_sources(store, languages=None) -> tuple[Path, dict[str, Path], int]:
    """Check the sources an engine can read, including dependencies inferred indirectly.

    Every inventoried file keeps its confined path, so no output can replace one.
    The bytes are hashed for the files of the engine's languages, or for every
    file when `languages` is None: a changed document cannot alter an inference,
    a changed source of the engine's language can, wherever it sits. Returns the
    root, the paths and how many files were hashed.
    """
    root, target, perimeter = _binding(store)
    paths = {}
    verified = 0
    for rel, entry in store.iter_file_headers_only():
        checked = languages is None or entry.get("language") in languages
        try:
            path = _source_path(rel, root, target, perimeter)
        except ValueError:
            if checked:
                raise
            continue
        paths[rel] = path
        if not checked:
            continue
        expected = entry.get("raw_hash")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if not isinstance(expected, str) or digest.hexdigest() != expected:
            raise ValueError(f"source differs from snapshot: {rel}; refresh the snapshot")
        verified += 1
    return root, paths, verified
