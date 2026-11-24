"""The links' binder, spec 8.13 point 2: the one place a row of an entries' source is tied to a function of the snapshot.

Two forms. An export in a file (`exports`, or `methods` when each export is a method of the route): the snapshot's own
export records name the function (`exported_target`). A name at a position (`handler` with `site` `file:line`): the one
function of that name whose lines hold the line; failing that, for Noir's row (a scanner of text: its place and its name are
citations), the one function that starts at the line (the outermost, when a closure holds others on it) if the name agrees with it
(`_agrees`). The place alone cannot tell a handler from the function that registers it, nor the name alone a function among those of its
name: each is an equality of two data. A row with no name is no such row (`noir.rows` reads the name only where Noir cites the handler's
place; without it the place is the registration's). The sources that name the function itself (Flask, Django, FastAPI) bind by the
name only. A row of another form passes unchanged.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from languages.semantic import NAMELESS


def bind(rows: list[dict], facts, resolver) -> list[dict]:
    placed = {id(row): _placed(row, facts) for row in rows if "handler" in row and "handler_source" not in row}
    _name_handlers(rows, placed, facts)
    out = []
    for row in rows:
        if "handler" not in row and ("exports" in row or "methods" in row):
            out += _exports(row, facts, resolver)
        elif id(row) in placed:
            out.append(_position(row, facts, *placed[id(row)]))
        else:
            out.append(row)
    return out


def _exports(row: dict, facts, resolver) -> list[dict]:
    methods = "methods" in row
    names = row["methods"] if methods else row["exports"]
    base = {k: v for k, v in row.items() if k not in ("exports", "methods", "exports_optional")}
    file, found, unread = row["site"], [], []
    for name in names:
        identity, reason = resolver.exported_target(file, name)
        symbol = facts.node(identity) if identity else None
        if symbol:
            found.append({**base, "symbol": symbol, "site": f"{file}:{facts.declarations[identity]['line']}",
                          "handler_source": row["reader"], "handler": name, **({"method": name} if methods else {})})
        elif reason != "export-missing":  # an export the file does not make is no gap: a route module has the exports it needs
            unread.append(f"{name}: {reason}")
    if found and not unread:
        return found
    if not found and not unread and row.get("exports_optional"):
        return []  # a layout with no data function is normal
    looked = "; ".join(unread) or ", ".join(names)
    return [*found, {**base, "gap": f"no function found for the exports the framework starts {row['path']} from: {looked}"}]


NO_NODE = "the function there has no node: an anonymous function no named function holds"


def _placed(row: dict, facts) -> tuple[list[dict], list[dict] | None]:
    """Where a row's handler is: the functions of its file whose lines hold the line and that have the name the tool gives (the rule of
    a name at a position), and, for a row with a name that this does not bind, the functions that start at the line and no other of them
    holds (`starts`); None where the row is not one to bind by the place."""
    import entries  # where the readers' names are
    file, _, line = row["site"].rpartition(":")
    functions, named = facts.functions.get(file, ()), row["handler"]
    at = int(line) if line.isdecimal() else 0
    matches = [d for d in functions if named and named in (d["name"], d.get("qualified_name")) and d["line"] <= at <= (d["end"] or d["line"])]
    if row.get("reader") != entries.NOIR or not named or len(matches) == 1:
        return matches, None
    starts = [d for d in functions if d["line"] == at] if at else []
    # the spans say which holds the others: a callback in a closure, a lambda in a lambda
    return matches, [d for d in starts if not any(o is not d and o["span"][:2] <= d["span"][:2] and d["span"][2:] <= o["span"][2:] for o in starts)]


def _position(row: dict, facts, matches: list[dict], starts: list[dict] | None) -> dict:
    symbol, cause = None, None
    if len(matches) == 1:
        symbol, cause = facts.node(matches[0]["id"]), NO_NODE
    elif starts is not None:
        symbol, cause = _started(row["handler"], starts, facts)
    if symbol:  # a row with no symbol would fail the links' sort of their entries
        return {**row, "symbol": symbol, "handler_source": row["reader"]}
    return {**row, "gap": f"{row['reader']} reports this entry without a unique snapshot handler at its site" + (f": {cause}" if cause else "")}


def _started(name: str, starts: list[dict], facts) -> tuple[str | None, str | None]:
    """The node of the function that starts at the line Noir cites for its handler when the name Noir gives agrees with it, or why it is none."""
    if not starts:
        return None, "no function starts at the line Noir cites for the handler"
    if len(starts) > 1:
        return None, "several functions start at the line and none holds the others"
    [function] = starts
    how = _agrees(name, function, facts)
    if how is None:
        return None, f"Noir names {name}, the function at the line is {function.get('qualified_name') or function['name']}"
    held = facts.node(function["id"])
    if held is None:
        return None, NO_NODE
    if function["name"] in NAMELESS and function["id"] not in facts.route_named and facts.property_label(function) is None:
        # a route names it (`_name_handlers`), so that its node does not depend on its siblings; it stays as it is where none could
        return None, (f"the function there is folded into {held}" if facts.folds(function)
                      else "the function there is anonymous and its route is the route of another function of the file")
    node = facts.own_node(function["id"])
    if node is None:
        return None, f"the function there shares its node {held} with other functions of the same name"
    # shortcut: Noir cites the function that builds a handler (`f()`), not the handler: it binds to the builder's node only where the function it returns is folded into it (a closure of JavaScript), so that the node holds the calls of the handler; upgrade when the returned function of the other readers (a func literal, a lambda, a named function) is folded too
    if how == "factory" and not _builds_folded(function, facts):
        return None, f"Noir names {name}, a function that builds the handler: the one it returns is not folded into {function['name']}"
    return node, None


def _agrees(name: str, function: dict, facts) -> str | None:
    """How the name Noir gives agrees with the function at the line, or None. A function written with no name takes any. Else: its name or
    qualified name; the same after a receiver or a variable in front (`api.GetPage` for Go's `SysApi.GetPage`: the part after the last
    dot of each); the class that owns it (a class view named by its class); the call that returns it (`recycles.f()`: a factory)."""
    if function["name"] in NAMELESS:
        return "anonymous"
    if name in (function["name"], function.get("qualified_name")):
        return "name"
    after, own = name.rpartition(".")[2], function["name"].rpartition(".")[2]
    if after == own:
        return "receiver"
    if after == own + "()":
        return "factory"
    owner = facts.owner(function)
    return "class" if owner is not None and owner["kind"] == "class" and name == owner.get("qualified_name") else None


def _builds_folded(function: dict, facts) -> bool:
    """Whether the functions written directly in a function all fold into it, and there is one: its node holds what they call."""
    inside = [d for d in facts.functions.get(function["file"], ()) if (owner := facts.owner(d)) is not None and owner["id"] == function["id"]]
    return bool(inside) and all(facts.folds(d) for d in inside)


def _name_handlers(rows: list[dict], placed: dict, facts) -> None:
    """A function written with no name that is the only one to start where Noir cites a route's handler is named by that route, as the links
    name a function written as a handler (`Facts.route_named`): its node is its own and holds the calls inside its lines, and does not
    depend on its siblings. Not one that already has a real name (the value of a property is that property's node), nor one a rule
    named. A function with several routes is named by the first of them by name, whatever the order of the rows; two functions of a file
    that one route would name are named none of them."""
    routes = defaultdict(set)
    for row in rows:
        starts = placed.get(id(row), (None, None))[1] or ()
        if (len(starts) == 1 and row.get("kind") == "rotta" and starts[0]["name"] in NAMELESS and starts[0]["id"] not in facts.route_named
                and facts.property_label(starts[0]) is None):
            routes[starts[0]["id"]].add(f"{(row.get('method') or 'ANY').upper()} {row['path']}")
    if not routes:
        return
    names = {ident: min(found) for ident, found in routes.items()}
    taken = Counter((ident.split("::", 1)[0], name) for ident, name in {**names, **facts.route_named}.items())
    named = {ident: name for ident, name in names.items() if taken[ident.split("::", 1)[0], name] == 1}
    if named:
        facts.name_routes(named)
