"""The logic of the SQL grammar benchmark, with no tree-sitter, sqlglot or Daodan import: what an object is, how the
tree of the `sql` grammar is read into objects, how the objects of two readers are compared, and how a growth is judged.

An object is (kind, name, first line, last line, inner). The three readers hand over what they have: the regex readers
of Daodan (`languages/sql.py`, `plsql.py`: a first line, no last line), a walk of the tree-sitter tree, and sqlglot's
expressions (`sql_readers.py`). The tree walk reads node types, never text: the grammar decides what a statement is.
"""
from __future__ import annotations

from typing import NamedTuple

CREATES = {"create_table": "table", "create_view": "view", "create_materialized_view": "view",
           "create_index": "index", "create_sequence": "sequence", "create_type": "type",
           "create_schema": "schema", "create_trigger": "trigger", "create_function": "function",
           "create_procedure": "procedure"}  # the regex readers call a materialized view a view too
PACKAGE_KINDS = ("package", "package-body", "type-body")  # no node of the `sql` grammar: only the regex readers name them
TALLY = ("found", "missing", "extra", "start_diff", "end_diff", "end_unknown")


class Obj(NamedTuple):
    kind: str
    name: str
    line: int
    end: int | None = None
    inner: bool = False


def norm_name(parts) -> str:
    """The parts of a name (`schema`, `name`) as one lowercase dotted name, the quotes off each."""
    return ".".join(part.strip().strip('"`[]') for part in parts if part and part.strip()).lower()


def _reference_name(node) -> str:
    if node.type == "object_reference":
        parts = [node.child_by_field_name(field) for field in ("database", "schema", "name")]
        parts = [part.text.decode("utf-8", "replace") for part in parts if part is not None]
        if parts:
            return norm_name(parts)
    return norm_name([node.text.decode("utf-8", "replace")])


def _tree_name(node) -> str | None:
    """The grammar's own shape: a `name` field where it has one; else, in `create_index`, the identifier that is a direct
    child (the grammar labels it `column`) comes before the table's object_reference; else the object_reference."""
    target = node.child_by_field_name("name")
    for kind in ("identifier", "object_reference"):
        if target is None:
            target = next((child for child in node.children if child.type == kind), None)
    return _reference_name(target) if target is not None else None


def _end_line(node) -> int:
    row, column = node.end_point  # the end is exclusive: a node that stops at a line's start ends on the line before
    return row if column == 0 and row > node.start_point[0] else row + 1


def tree_objects(root) -> list[Obj]:
    """The objects of a `sql` tree: every create statement the grammar names, wherever it sits in the tree."""
    found, stack = [], [root]
    while stack:
        node = stack.pop()
        kind = CREATES.get(node.type)
        if kind is not None:
            name = _tree_name(node)
            if name:
                found.append(Obj(kind, name, node.start_point[0] + 1, _end_line(node)))
        stack.extend(node.children)
    return sorted(found, key=lambda o: (o.line, o.kind, o.name))


def tree_errors(root) -> dict:
    """ERROR and MISSING nodes of a tree, and the bytes the outermost ERROR nodes cover."""
    errors = missing = covered = 0
    stack = [(root, False)]
    while stack:
        node, inside = stack.pop()
        is_error = node.type == "ERROR"
        if is_error:
            errors += 1
            if not inside:
                covered += node.end_byte - node.start_byte
        if node.is_missing:
            missing += 1
        stack.extend((child, inside or is_error) for child in node.children)
    return {"error": errors, "missing": missing, "error_bytes": covered}


def from_regex(classes, functions) -> list[Obj]:
    """The objects of a regex reader's result: `classes` are (name, kind, line), `functions` (name, visibility, line).
    A procedure is a function whose visibility is `procedure` (as `sql.py` marks it)."""
    found = [Obj(kind, norm_name([name]), line) for name, kind, line in classes]
    found += [Obj("procedure" if visibility == "procedure" else "function", norm_name([name]), line)
              for name, visibility, line in functions]
    return sorted(found, key=lambda o: (o.line, o.kind, o.name))


def _group(objects) -> dict:
    groups: dict = {}
    for obj in sorted(objects, key=lambda o: (o.line, o.end or 0)):
        groups.setdefault((obj.kind, obj.name), []).append(obj)
    return groups


def compare(reference, reader, detail: int = 40) -> dict:
    """The objects of `reader` against `reference`, per kind and in all, matched by kind and name (the i-th of a key
    with the i-th). found: both have it; missing: only the reference; extra: only the reader. For a found pair,
    start_diff: the first lines differ; end_diff: both know a last line and they differ; end_unknown: the reader has
    none. `by_level` counts the reference's inner subprograms apart from its top-level objects."""
    tally: dict = {}
    levels = {"top": {"found": 0, "missing": 0}, "inner": {"found": 0, "missing": 0}}
    notes: list = []

    def count(kind: str, key: str, n: int = 1) -> None:
        tally.setdefault(kind, dict.fromkeys(TALLY, 0))[key] += n

    ref_groups, read_groups = _group(reference), _group(reader)
    for key in sorted(set(ref_groups) | set(read_groups)):
        kind, name = key
        refs, reads = ref_groups.get(key, []), read_groups.get(key, [])
        for ref, read in zip(refs, reads):
            count(kind, "found")
            levels["inner" if ref.inner else "top"]["found"] += 1
            if ref.line != read.line:
                count(kind, "start_diff")
                notes.append(f"line {kind} {name}: {ref.line} vs {read.line}")
            if read.end is None:
                count(kind, "end_unknown")
            elif ref.end is not None and ref.end != read.end:
                count(kind, "end_diff")
                notes.append(f"end {kind} {name}: {ref.end} vs {read.end}")
        for ref in refs[len(reads):]:
            count(kind, "missing")
            levels["inner" if ref.inner else "top"]["missing"] += 1
            notes.append(f"missing {kind} {name} line {ref.line}")
        for read in reads[len(refs):]:
            count(kind, "extra")
            notes.append(f"extra {kind} {name} line {read.line}")
    total = {key: sum(row[key] for row in tally.values()) for key in TALLY}
    return {"total": total, "kinds": tally, "by_level": levels, "notes": notes[:detail]}


def merge(results) -> dict:
    """The tallies of several comparisons, added up per kind."""
    tally: dict = {}
    for result in results:
        for kind, row in result["kinds"].items():
            into = tally.setdefault(kind, dict.fromkeys(TALLY, 0))
            for key in TALLY:
                into[key] += row[key]
    return {"total": {key: sum(row[key] for row in tally.values()) for key in TALLY}, "kinds": tally}


def summarise(records, key) -> dict:
    """Per group (`key(record)`): files, bytes, the tree's error counts, time and objects of each reader, and the
    tree, sqlglot and sqlglot-with-dialect against the regex reader (reference: the regex reader's objects, so
    `missing` is what only the regex reader has and `extra` what only the other has). A record is a measured file."""
    groups: dict = {}
    for record in records:
        if "ts_ms" in record:
            groups.setdefault(key(record), []).append(record)
    out = {}
    for name, rows in sorted(groups.items()):
        size = sum(r["size"] for r in rows)
        entry = {"files": len(rows), "bytes": size,
                 "files_with_error": sum(1 for r in rows if r["err"]["error"] or r["err"]["missing"]),
                 "error_nodes": sum(r["err"]["error"] for r in rows), "missing_nodes": sum(r["err"]["missing"] for r in rows),
                 "error_byte_share": round(sum(r["err"]["error_bytes"] for r in rows) / size, 4) if size else 0.0,
                 "ms": {reader: round(sum(r.get(f"{reader}_ms", 0.0) for r in rows), 1)
                        for reader in ("rx", "ts", "g", "gd")},
                 "objects": {reader: sum(r.get(f"n_{reader}", 0) for r in rows) for reader in ("rx", "ts", "g", "gd")},
                 "glot_skipped": sum(1 for r in rows if r.get("cmp_g") is None),
                 "glot_failed": sum(1 for r in rows if r.get("g_failure")),
                 "glot_commands": sum(r.get("g_commands", 0) for r in rows)}
        for compared in ("cmp_ts", "cmp_g", "cmp_gd"):
            entry[compared] = merge([r[compared] for r in rows if r.get(compared)])
        out[name] = entry
    return out


def growth_ratio(small: float, large: float, factor: int) -> float:
    """How far a run on `factor` times the text is from linear: its time over `factor` times the small run's
    (1 is linear; 4 times the text taking 16 times as long is 4)."""
    return large / (small * factor) if small > 0 else float("inf")


def judge(ratio: float, floor_ok: bool, limit: float = 2.0) -> str:
    """`linear` under the limit, `superlinear` over it; a run too fast to tell (`floor_ok` False) is `noise`."""
    if not floor_ok:
        return "noise"
    return "linear" if ratio <= limit else "superlinear"
