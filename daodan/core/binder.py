"""The links' binder, spec 8.13 point 2: the one place a row of an entries' source is tied to a function of the snapshot.

Two forms. An export in a file (`exports`, or `methods` when each export is a method of the route): the snapshot's own
export records name the function (`exported_target`). A name at a position (`handler` with `site` `file:line`): the one
function of that name whose lines hold the line. A row of another form passes unchanged.
"""
from __future__ import annotations


def bind(rows: list[dict], facts, resolver) -> list[dict]:
    out = []
    for row in rows:
        if "handler" not in row and ("exports" in row or "methods" in row):
            out += _exports(row, facts, resolver)
        elif "handler" in row and "handler_source" not in row:
            out.append(_position(row, facts))
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


def _position(row: dict, facts) -> dict:
    file, _, line = row["site"].rpartition(":")
    at = int(line) if line.isdecimal() else 0
    matches = [d for d in facts.functions.get(file, ()) if row["handler"] == d["name"] and d["line"] <= at <= (d["end"] or d["line"])]
    if len(matches) == 1:
        return {**row, "symbol": facts.node(matches[0]["id"]), "handler_source": row["reader"]}
    return {**row, "gap": f"{row['reader']} reports this entry without a unique snapshot handler at its site"}
