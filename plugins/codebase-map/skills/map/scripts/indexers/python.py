"""scip-python for Python: what its index leaves to the reader.

`hops` reads, from `code_graph.Index`, what scip-python leaves implicit; each hop carries its own tag:
- `import-binding`: an imported name (`from m import a`, `a as b`) is a `local` the index defines nowhere, with
  no tie to `m`; it leads to the module occurrence of the same one-line statement;
- `builtin`: a builtin function (`isinstance`, `len`) is such a `local` too, while a builtin class has its
  `builtins/` symbol; an unbound bare name the interpreter's `builtins` holds, neither an attribute nor a
  keyword argument's name, leads to that module's symbol, in the package the index gives `builtins`;
- `classmethod-cls`: the first parameter of a method decorated `classmethod` (the decorator lies in the
  method's enclosing range) leads to the method's class;
- `type-of-self`: a local assigned `type(<first parameter of a method>)` leads to the method's class.
"""
from __future__ import annotations

import collections
import re

ASSIGNED_TYPE = re.compile(r"^\s*(\w+)\s*=\s*type\(\s*(\w+)\s*\)\s*(#.*)?$")
FROM_IMPORT = re.compile(r"^\s*from\s+\S+\s+import\s+[^()]+$")
METHOD = re.compile(r"#[^#/().]+\(\)\.$")


def _text(index, rel: str, occurrence) -> tuple[str, str]:
    """(the line an occurrence starts on, the source text of its range on that line)."""
    line = index.line(rel, occurrence.line) or ""
    begin = index.to_bytes(rel, occurrence.line, occurrence.start)
    stop = index.to_bytes(rel, occurrence.line, occurrence.end) if occurrence.end_line == occurrence.line else None
    data = line.encode("utf-8")
    return line, data[begin:stop].decode("utf-8", errors="replace") if begin is not None else ""


def static(index) -> set:
    """`(rel, line, byte column)` of member references Python binds without dispatch: `C.m` on a class symbol
    the index names right before the dot, and `super().m`. An override in a subclass never runs there."""
    out = set()
    for rel, occurrences in index.documents.items():
        ends = {(o.line, o.end): o.key for o in occurrences if not o.definition and o.end_line == o.line}
        for o in occurrences:
            if o.definition or o.start < 2:
                continue
            line = index.line(rel, o.line) or ""
            begin = index.to_bytes(rel, o.line, o.start)
            head = line.encode("utf-8")[:begin].decode("utf-8", errors="ignore") if begin is not None else ""
            if not head.endswith("."):
                continue
            receiver = ends.get((o.line, o.start - 1), "")
            if head[:-1].rstrip().endswith("super()") or (receiver.endswith("#") and "#local " not in receiver):
                out.add((rel, o.line, begin))
    return out


def hops(index) -> dict:
    """Hops `{key: [(target key, tag)]}` for what scip-python leaves implicit; see the module's docstring."""
    import builtins
    out = collections.defaultdict(list)
    stdlib = next((key.split(" builtins/")[0] for occurrences in index.documents.values() for o in occurrences
                   for key in (o.key,) if " builtins/" in key), None)
    for rel, occurrences in index.documents.items():
        ordered = sorted(occurrences, key=lambda o: (o.line, o.start))
        methods = {}  # method key -> [its class, decorated classmethod, first parameter]
        for o in ordered:
            if o.definition and o.enclosing and METHOD.search(o.key):
                start, head = (o.line, o.start), (o.enclosing[0], o.enclosing[1])
                decorated = any(d.key.endswith(" builtins/classmethod#") and not d.definition
                                and head <= (d.line, d.start) < start for d in ordered)
                methods[o.key] = [o.key[:o.key.rindex("#") + 1], decorated, None]
        for o in ordered:
            owner = o.key.rsplit("(", 1)[0] if o.key.endswith(")") else None
            if o.definition and owner in methods and methods[owner][2] is None:
                methods[owner][2] = o.key
        first = {parameter: (cls, decorated) for cls, decorated, parameter in methods.values() if parameter}
        for parameter, (cls, decorated) in first.items():
            if decorated:
                out[parameter].append((cls, "classmethod-cls"))
        seen = set()
        for position, o in enumerate(ordered):
            if "#local " not in o.key:
                continue
            line, name = _text(index, rel, o)
            if o.definition:
                found, following = ASSIGNED_TYPE.match(line), ordered[position + 1:position + 3]
                if found and found.group(1) == name and len(following) == 2 \
                        and following[0].key.endswith(" builtins/type#") and following[1].key in first:
                    out[o.key].append((first[following[1].key][0], "type-of-self"))
                continue
            if o.key in index.defs or o.key in seen:
                continue
            seen.add(o.key)  # the first occurrence of an undefined local decides
            if FROM_IMPORT.match(line):
                module = [m.key for m in ordered[:position] if m.line == o.line and m.key.endswith("/__init__:")
                          and not m.definition]
                if module:
                    out[o.key].append((module[-1], "import-binding"))
                continue
            begin = index.to_bytes(rel, o.line, o.start) or 0
            before = line.encode("utf-8")[:begin].decode("utf-8", errors="ignore").rstrip()[-1:]
            after = line.encode("utf-8")[begin + len(name.encode("utf-8")):].decode("utf-8", errors="ignore").lstrip()[:2]
            keyword = after[:1] == "=" and after != "=="  # `f(help=...)` names a parameter, not a value
            if stdlib and name.isidentifier() and not name.startswith("_") and before != "." and not keyword \
                    and hasattr(builtins, name):
                suffix = "#" if isinstance(getattr(builtins, name), type) else "()."
                out[o.key].append((f"{stdlib} builtins/{name}{suffix}", "builtin"))
    return {key: list(dict.fromkeys(items)) for key, items in out.items()}
