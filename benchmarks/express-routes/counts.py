"""The counts of `modal_compare.py`, pure: from the rows of Express's module and Noir's, as Daodan's binder left them, to the comparison the
README's decision rule reads (`T1.C.9`). It runs in the container (`modal_compare.read`), where Daodan's `flows.path_schema` is;
`test_express_compare.py` proves it on rows written by hand. The sample (`sample`) is read by a person: `modal_compare.py --mode sample`.
"""
import random
from collections import Counter

SAMPLE = 20
SEED = 24


def _key(row: dict, schema) -> tuple:
    return (row.get("method") or None, schema(row["path"]) or row["path"]) if row.get("path") is not None else (row.get("method") or None, None)


def bound(rows: list[dict], schema) -> set[tuple]:
    """The routes a binding ties: (method, schema or path, function), once each; the function is the declaration the row's symbol is
    (`function`, given by `modal_compare._identify`: a function written with no name takes its route's name, which differs between two
    readers), else the symbol."""
    return {(*_key(row, schema), row.get("function") or row["symbol"]) for row in rows if not row.get("gap") and row.get("symbol")}


def cause(gap: str) -> str:
    """The cause of a gap of the module, without the route and the sites it names (`express route GET /x: cause at a.js:3`)."""
    said = gap.partition(": ")[2] or gap
    said = said.partition(" at ")[0]
    return said.partition(": ")[0] if said.startswith("the handler is no function") else said


def compare(express: list[dict], noir: list[dict], schema) -> dict:
    """`express`: the module's rows as the binder left them; `noir`: Noir's `http` rows as the step binds them. A discordance is a route
    the module binds to a function Noir does not bind with that method (`ours`), or one Noir binds to a function the module does not
    bind with that method (`theirs`)."""
    ours, theirs = bound(express, schema), bound(noir, schema)
    by_function = lambda found: {(method, symbol) for method, _, symbol in found}  # noqa: E731
    our_functions, their_functions = by_function(ours), by_function(theirs)
    keys = lambda found: {(method, path) for method, path, _ in found}  # noqa: E731
    return {"express_rows": len(express), "express_bound": len(ours), "noir_rows": len(noir), "noir_bound": len(theirs),
            "common_routes": len(keys(ours) & keys(theirs)), "same_route_and_function": len(ours & theirs),
            "same_function_other_path": len({(m, s) for m, p, s in ours if (m, s) in their_functions and (m, p, s) not in theirs}),
            "express_gaps": dict(Counter(cause(row["gap"]) for row in express if row.get("gap")).most_common()),
            "noir_gaps": sum(1 for row in noir if row.get("gap")),
            "only_express": sorted(map(list, {r for r in ours if (r[0], r[2]) not in their_functions}), key=str),
            "only_noir": sorted(map(list, {r for r in theirs if (r[0], r[2]) not in our_functions}), key=str)}


def sample(compared: dict[str, dict], count: int = SAMPLE, seed: int = SEED) -> list[dict]:
    """`count` of the routes only the module binds (`only_express`), over every application, in a fixed order then shuffled by `seed`."""
    every = [{"application": name, "method": m, "path": p, "symbol": s} for name in sorted(compared)
             for m, p, s in compared[name]["only_express"]]
    random.Random(seed).shuffle(every)
    return every[:count]


def show(results: dict[str, dict], lines) -> None:
    """Print the sample over `results` (application -> answer of `measure.run`) with the source's lines at the registration and at the
    start of the handler, `lines(application, [[file, first, last], ...])` reading them in the container: for a person, never written."""
    chosen = sample({name: answer["compare"] for name, answer in results.items() if "compare" in answer})
    for item in chosen:
        row = next(r for r in results[item["application"]]["express_rows"] if r.get("function", r.get("symbol")) == item["symbol"]
                   and (r.get("method") or None) == item["method"] and (r.get("schema") or r["path"]) == item["path"])
        sites = (row["registered"], row["site"])
        wanted = [[site.rpartition(":")[0], int(site.rpartition(":")[2]) - 1, int(site.rpartition(":")[2]) + 2] for site in sites]
        print(f"\n{item['application']} {item['method'] or 'ANY'} {row['path']} -> {item['symbol']}")
        for site, found in zip(sites, lines(item["application"], wanted)):
            print(f"  {site}")
            print("\n".join(f"     {line}" for line in found))
