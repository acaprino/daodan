"""scip-java for Java: what its index leaves to the reader.

`hops` is empty: `new X()` already names the constructor, an implicit constructor is defined at its class's
name, Java has no aliases, and implementations come from `is_implementation`. `static` names the calls through
`super`, bound statically, which take no implementation; `same_range` keeps an enum constant from aliasing the
constructor it runs.
"""
from __future__ import annotations


def hops(index) -> dict:
    """None: see the module's docstring."""
    return {}


def static(index) -> set[tuple[str, int, int]]:
    """`(rel, line, byte column)` of each method name called through `super` (`super.m()`), bound statically."""
    out = set()
    for rel, occurrences in index.documents.items():
        ordered = sorted(occurrences, key=lambda o: (o.line, o.start))
        for before, after in zip(ordered, ordered[1:]):
            text = index.line(rel, before.line) or ""
            # `super(...)` names a constructor; `super.m` is `super`, a dot, then the method's name.
            if text[before.start:before.end] == "super" and not before.key.endswith(").")                     and (after.line, after.start) == (before.end_line, before.end + 1) and not after.definition:
                out.add((rel, after.line, index.to_bytes(rel, after.line, after.start)))
    return out


def same_range(index) -> dict[tuple[str, str], bool]:
    """Never an alias: at each enum constant's name scip-java writes its definition and a reference to the enum
    constructor it runs; a read of the constant is not a call of the constructor."""
    out = {}
    for rel, occurrences in index.documents.items():
        for occurrence in occurrences:
            if occurrence.definition:
                for other in index.at.get((rel, occurrence.line, occurrence.start), ()):
                    if not other.definition and "`<init>`" in other.key and other.key != occurrence.key                             and (other.end_line, other.end) == (occurrence.end_line, occurrence.end):
                        out[(occurrence.key, other.key)] = False
    return out
