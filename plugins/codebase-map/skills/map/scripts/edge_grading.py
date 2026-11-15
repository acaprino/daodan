"""An engine's answer graded against the snapshot's own declarations (`grade`), and the calls it is asked about
(`classify_reference`)."""
from __future__ import annotations

import hashlib
import io
import os
import sys
import tokenize
import unicodedata
from pathlib import Path, PurePosixPath

from source_reader import _binding, _no_links, _source_path
from snapshot_store import _unpack
from source_positions import char_to_byte


# The population an engine is asked about: the snapshot's own unresolved call
# references, minus the builtins the lexical resolver declines to model and minus
# the callees no project declaration is named after (`classify_reference`).
EXCLUDED_REASONS = frozenset({"unbound-name"})


CANDIDATE_REASONS = {
    "project-not-a-symbol": "engine-project-not-a-symbol",
    "ambiguous-target": "engine-ambiguous-target",
}


# The end class a per-position verdict is stored as; a candidate verdict is stored `uncertain`.
POSITION_ENDS = {"external-definition": "external", "project-not-a-symbol": "project-value",
                 "ambiguous-target": "project-callable"}


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
        "SELECT file FROM sem_coverage WHERE status='ast'")}


def grade(definition, inventory: set[str], tables: dict, root: Path,
          table_for) -> tuple[str, dict | None]:
    """One engine answer, graded by what this snapshot declares at that position.

    Returns `(verdict, target)` where verdict is `edge-call`, `edge-instantiation`,
    `external-definition`, `project-not-a-symbol`, `ambiguous-target`, `unresolved`
    or `binding` (a value binding, which `grade_all` never keeps as a target),
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
    if kind == "binding":
        return "binding", None
    verdict = "edge-instantiation" if kind == "class" else "edge-call"
    return verdict, {"id": identity, "file": relative, "kind": kind}


def grade_all(definitions, inventory: set[str], tables: dict, root: Path,
              table_for, *, follow=None) -> tuple[str, dict | None]:
    """Follow exact holders with engine evidence, bounded to 64 distinct queries.

    A holder beside a confirmed callable names its container (requirement 14).
    An external location alone does not identify a project holder's contents.
    Cycles, missing answers and exhausted budgets keep uncertainty explicit.
    """
    memo, active = {}, set()
    queries = 0

    def walk(items):
        nonlocal queries
        if not items:
            return "unresolved", None
        unique = {(str(item.module_path), item.line, item.column): item for item in items}
        graded = [(key, item, grade(item, inventory, tables, root, table_for))
                  for key, item in unique.items()]
        callable_found = any(answer[0].startswith("edge-") for _, _, answer in graded)
        answers = []
        for key, item, answer in graded:
            if answer[0] == "binding":
                if callable_found:
                    continue
                if follow is None or key in active or len(active) >= 32:
                    answer = ("project-not-a-symbol", None)
                elif key in memo:
                    answer = memo[key]
                elif queries >= 64:
                    answer = ("project-not-a-symbol", None)
                else:
                    queries += 1
                    active.add(key)
                    children = follow(item)
                    answer = walk(children) if children else ("project-not-a-symbol", None)
                    active.remove(key)
                    memo[key] = answer
            answers.append(answer)
        if all(answer == answers[0] for answer in answers):
            return answers[0]
        return "ambiguous-target", None

    return walk(definitions)


def runtime_imports(connection) -> dict[str, dict]:
    """Imports the snapshot could not place that reach a project module through `sys.path`.

    A bare `import snapshot` the snapshot could not place is how a test or a
    script reaches a tool after inserting the tool's directory into sys.path.
    When exactly one directory holds an inventoried Python module of that name,
    that directory is such a root. Standard-library names never make one. Returns,
    per module name, the directory relative to the snapshot root, the module's
    files and the files that import it.
    """
    placed = {(row[0], row[1]) for row in connection.execute("SELECT file, module FROM sem_modules")}
    importers: dict[str, set[str]] = {}
    for file, blob in connection.execute("SELECT file, payload FROM sem_bindings WHERE kind='import'"):
        module = (_unpack(blob) or {}).get("module") or ""
        head = module.split(".")[0]
        if head and not module.startswith(".") and (file, module) not in placed \
                and head not in sys.stdlib_module_names:
            importers.setdefault(head, set()).add(file)
    found: dict[str, dict[str, set[str]]] = {}
    for (rel,) in connection.execute("SELECT file FROM sem_coverage WHERE language='python'"):
        path = PurePosixPath(rel)
        package = path.name == "__init__.py"
        name = path.parent.name if package else path.stem
        if name in importers:
            directory = (path.parent.parent if package else path.parent).as_posix()
            found.setdefault(name, {}).setdefault(directory, set()).add(rel)
    return {name: {"directory": directory, "files": sorted(files), "importers": sorted(importers[name])}
            for name, places in sorted(found.items()) if len(places) == 1
            for directory, files in places.items()}


def project_callee_names(connection) -> set[str]:
    """Names used to prioritize queries, never to prove a call external."""
    names = {unicodedata.normalize("NFKC", row[0]) for row in connection.execute(
        "SELECT DISTINCT name FROM sem_declarations WHERE kind IN ('function','method','class')")}
    # A Go method is declared as `Type.Method`; a call names it by the last segment.
    names |= {name.rsplit(".", 1)[-1] for name in names if "." in name}
    names |= {unicodedata.normalize("NFKC", row[0]) for row in connection.execute(
        "SELECT DISTINCT name FROM sem_bindings WHERE kind='import'")}
    return names


def classify_reference(payload: dict, names: set[str]) -> str:
    """An unresolved call is builtin, dynamic or askable, regardless of its name."""
    parts = payload.get("parts") or []
    if payload.get("reason") in EXCLUDED_REASONS:
        return "builtin"
    if not parts:
        return "dynamic"
    return "askable"


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


def edge_destination(out: Path, manifest: Path, sources: dict[str, Path]) -> Path:
    """Refuse evidence collisions and linked destinations before any write."""
    out = Path(os.path.abspath(out))
    existing = out
    while not existing.exists() and not existing.is_symlink():
        existing = existing.parent
    _no_links(existing)
    protected = [Path(manifest).resolve(), *sources.values()]
    for path in protected:
        if out == path or (out.exists() and path.exists() and out.samefile(path)):
            raise ValueError(f"engine edge output would overwrite snapshot evidence: {out}")
    return out
