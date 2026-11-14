"""Connection points, the part that knows no language: keys, the join by key, islands and reach.

A side is `{site, role, kind, keys, holder, hole}`: `exposes` and `calls` meet on an `http` key, the method and
the path with every parameter as `{}`. A call key joins the route keys it matches: `exact` when every segment
is the same literal, a placeholder on a parameter, or a literal filling a parameter (the most literal route
wins, a tie is uncertain); `loose` when a hole on the call side has to equal a literal of the route. Keys with
one side only are reported with their reason; a route that only a catch-all answers counts as missing.
"""
from __future__ import annotations

import collections
import re

PAIRS = {"calls": "exposes"}  # the role a calling side meets; later writes/reads, emits/listens


def route_key(method: str, path: str) -> str:
    segments = []
    for segment in (s for s in path.split("/") if s):
        segments.append("{*}" if segment == "*" else "{}" if segment.startswith(":") else segment)
    return f"{method.upper()} /" + "/".join(segments)


def _grade(call: str, route: str) -> int | None:
    """2 the same, 1 a literal filling a parameter, 0 a call hole that must equal a literal, None no match."""
    if call == route:
        return 2
    if route == "{}":
        return 1
    if "{}" in call and "{" not in route:
        pattern = "".join("[^/]*" if part == "{}" else re.escape(part) for part in re.split(r"(\{\})", call))
        return 0 if re.fullmatch(pattern, route) else None
    return None


def _match(call: str, route: str) -> tuple | None:
    """(strict, total, catch-all) of a call key against a route key, None when they cannot meet."""
    call_method, call_path = call.split(" ", 1)
    route_method, route_path = route.split(" ", 1)
    if call_method not in ("*", route_method) and route_method != "ALL":
        return None
    calls, routes = call_path.strip("/").split("/"), route_path.strip("/").split("/")
    if routes and routes[-1] == "{*}":
        head = routes[:-1]
        if len(calls) < len(head) or any(_grade(c, r) is None for c, r in zip(calls, head)):
            return None
        return False, 0, True
    if len(calls) != len(routes):
        return None
    grades = [_grade(c, r) for c, r in zip(calls, routes)]
    if None in grades:
        return None
    return min(grades) >= 1 and call_method != "*", sum(grades), False


def join(sides: list[dict]) -> dict:
    exposed = [s for s in sides if s["role"] == "exposes"]
    out = {"links": [], "uncertain": [], "calls_only": [], "unmatched_candidates": [], "holes": [],
           "exposed_only": []}
    used = set()
    for side in (s for s in sides if s["role"] in PAIRS):
        if not side["keys"]:
            out["holes"].append({"site": side["site"], "reason": side.get("hole")})
            continue
        linked, missing = False, []
        for key in side["keys"]:
            found = [(m, r) for r in exposed if r["kind"] == side["kind"] for k in r["keys"]
                     if (m := _match(key, k)) is not None]
            real = [(m, r) for m, r in found if not m[2]]
            strict = [(m, r) for m, r in real if m[0]]
            pool = strict or real
            if pool:
                best = max(m[1] for m, _ in pool)
                chosen = [r for m, r in pool if m[1] == best] if strict else [r for _, r in pool]
                if len(chosen) == 1:
                    route = chosen[0]
                    out["links"].append({"call": side["site"], "route": route["site"], "key": key,
                                         "route_key": route["keys"][0], "match": "exact" if strict else "loose",
                                         "holder": side.get("holder"), "handler": route.get("holder")})
                    used.add(id(route))
                else:
                    out["uncertain"].append({"call": side["site"], "key": key,
                                             "candidates": [r["site"] for r in chosen],
                                             "candidate_keys": [r["keys"][0] for r in chosen]})
                    used.update(id(r) for r in chosen)
                linked = True
            else:
                missing.append((key, "only the catch-all route" if found else "no route"))
        if not linked:
            out["calls_only"] += [{"site": side["site"], "key": k, "reason": why} for k, why in missing]
        else:
            out["unmatched_candidates"] += [{"site": side["site"], "key": k} for k, _ in missing]
    out["exposed_only"] = [{"site": r["site"], "key": r["keys"][0]} for r in exposed if id(r) not in used]
    return out


def islands(nodes: set, edges: list) -> dict:
    """Weakly connected components: their count, the five largest, singletons, the largest one's share."""
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    sizes = sorted(collections.Counter(find(n) for n in nodes).values(), reverse=True)
    return {"nodes": len(nodes), "components": len(sizes), "largest": sizes[:5],
            "singletons": sum(1 for s in sizes if s == 1),
            "largest_share": round(sizes[0] / len(nodes), 3) if sizes else 0}


def holder(file: str, start: int, end: int, edges: list, lines: dict, module: str) -> str:
    """The graph node a span of code belongs to: among the holders of the edges inside it, the innermost one
    defined at or before its start (a nested definition is not the span's holder); the file's module node
    when no edge falls inside."""
    inside = {source for source, _target, site in edges
              if site.rpartition(":")[0] == file and start <= int(site.rpartition(":")[2]) <= end}
    before = [n for n in inside if lines.get(n, 10 ** 9) <= start]
    return max(before, key=lambda n: lines[n]) if before else module


def reach(starts: set, edges: list, goals: set) -> set:
    """The starts from which some goal is reachable along the edges."""
    forward = collections.defaultdict(set)
    for a, b in edges:
        forward[a].add(b)
    backward = collections.defaultdict(set)
    for a, b in edges:
        backward[b].add(a)
    seen, stack = set(goals), list(goals)
    while stack:
        node = stack.pop()
        for previous in backward[node]:
            if previous not in seen:
                seen.add(previous)
                stack.append(previous)
    return {s for s in starts if s in seen}
