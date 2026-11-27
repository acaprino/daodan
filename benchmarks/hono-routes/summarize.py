"""The counts of `modal_probe.py`, pure: from the routes `inspectRoutes` printed, the rows of Noir as Daodan's binder left them and the names of the
snapshot's functions, to the comparison the README's decision rule reads. It runs in the container (`modal_probe.read`), where Daodan's
`flows.path_schema` is; `test_hono_routes.py` proves it on rows written by hand.
"""
from collections import Counter

NAMELESS = ("", "[handler]", "[middleware]")  # what `inspectRoutes` writes for a function with no name (hono/dev `handlerName`)


def routes(inspected: list[dict]) -> list[dict]:
    """The routes of `inspectRoutes` (`path`, `method`, `name`, `isMiddleware`): the handlers that are not middleware, once per method, path and name."""
    seen, out = set(), []
    for row in inspected:
        key = (row["method"], row["path"], row["name"])
        if not row.get("isMiddleware") and key not in seen:
            seen.add(key)
            out.append({"method": row["method"], "path": row["path"], "name": row["name"]})
    return out


def names(functions: list[dict]) -> Counter:
    """How many functions of the snapshot each name is: the name and the last part of the qualified name, once per function."""
    counted = Counter()
    for function in functions:
        for key in {function["name"], (function.get("qualified_name") or function["name"]).rpartition(".")[2]}:
            counted[key] += 1
    return counted


def handler(name: str, counted: Counter) -> str:
    """`nameless`, `unique`, `ambiguous` or `absent`: whether a route's handler name ties it to one function of the snapshot."""
    if name in NAMELESS:
        return "nameless"
    return {0: "absent", 1: "unique"}.get(counted[name], "ambiguous")


def compare(inspected: list[dict], noir: list[dict], counted: Counter, symbols: dict, schema) -> dict:
    """`inspected`: the routes of `routes`; `noir`: Noir's `http` rows (`method`, `path`, `symbol` when the binder tied one); `symbols`: name -> the
    node of its one function; `schema`: `flows.path_schema`. A route is its method and its path schema."""
    def key(row):
        return row["method"].upper(), schema(row["path"])
    ours = {key(r): r for r in inspected}
    theirs = {key(r): r for r in noir}
    common = sorted(set(ours) & set(theirs), key=str)
    bindable = Counter(handler(r["name"], counted) for r in inspected)
    agree = sum(1 for k in common if theirs[k].get("symbol") and symbols.get(ours[k]["name"]) == theirs[k]["symbol"])
    return {"inspect_routes": len(ours), "noir_routes": len(theirs), "common": len(common),
            "only_inspect": sorted(map(list, set(ours) - set(theirs)), key=str), "only_noir": sorted(map(list, set(theirs) - set(ours)), key=str),
            "inspect_handlers": dict(sorted(bindable.items())), "noir_bound": sum(1 for r in theirs.values() if r.get("symbol")),
            "common_bound_by_both": sum(1 for k in common if theirs[k].get("symbol") and handler(ours[k]["name"], counted) == "unique"),
            "common_same_function": agree}
