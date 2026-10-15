"""Static import diagnostics over caller-supplied, already confined file graphs.

Edges point from an importer to its dependencies. Centrality is a reading aid,
and reverse reachability is not a claim that a change propagates at runtime.
This module reads no source files and changes no incremental-update decision.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
import math


__all__ = ["dependency_graph_metrics", "transitive_importers"]


def _normalise_graph(graph: dict[str, list[str]]) -> dict[str, list[str]]:
    """Copy, validate and order edges; targets without rows are dangling nodes."""
    if not isinstance(graph, dict):
        raise ValueError("graph must be a dictionary of string nodes and adjacency lists")
    adjacency: dict[str, list[str]] = {}
    targets: set[str] = set()
    for node, neighbors in graph.items():
        if not isinstance(node, str):
            raise ValueError("graph nodes must be strings")
        if not isinstance(neighbors, (list, tuple, set, frozenset)):
            raise ValueError("graph adjacency must be a collection of string nodes")
        if any(not isinstance(target, str) for target in neighbors):
            raise ValueError("graph targets must be strings")
        adjacency[node] = sorted(set(neighbors))
        targets.update(adjacency[node])
    for target in targets:
        adjacency.setdefault(target, [])
    return {node: adjacency[node] for node in sorted(adjacency)}


def _import_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Find strongly connected components with two iterative depth-first walks."""
    reverse: dict[str, list[str]] = {node: [] for node in graph}
    for node, targets in graph.items():
        for target in targets:
            reverse[target].append(node)

    finished: list[str] = []
    visited: set[str] = set()
    for root in graph:
        if root in visited:
            continue
        stack = [(root, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                finished.append(node)
            elif node not in visited:
                visited.add(node)
                stack.append((node, True))
                stack.extend((target, False) for target in reversed(graph[node]) if target not in visited)

    cycles: list[list[str]] = []
    visited.clear()
    for root in reversed(finished):
        if root in visited:
            continue
        component: list[str] = []
        pending = [root]
        while pending:
            node = pending.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            pending.extend(reverse[node])
        if len(component) > 1 or root in graph[root]:
            cycles.append(sorted(component))
    return sorted(cycles)


def dependency_graph_metrics(
    graph: dict[str, list[str]],
    *,
    damping: float = 0.85,
    tolerance: float = 1e-10,
    max_iterations: int = 100,
) -> dict:
    """Return cycles and PageRank on importer-to-dependency edges.

    Rank includes uniform teleportation and redistributes dangling-node mass.
    ``tolerance`` bounds the L1 change of the complete probability vector.
    The final iterate is returned even when the iteration limit is reached,
    with explicit convergence metadata. No rank threshold classifies a file.
    """
    if (isinstance(damping, bool) or not isinstance(damping, (int, float))
            or not math.isfinite(damping) or not 0 < damping < 1):
        raise ValueError("damping must be finite and strictly between zero and one")
    if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
            or not math.isfinite(tolerance) or tolerance <= 0):
        raise ValueError("tolerance must be finite and positive")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError("max_iterations must be a positive integer")

    adjacency = _normalise_graph(graph)
    nodes = list(adjacency)
    ranks = {node: 1 / len(nodes) for node in nodes}
    converged = not nodes
    iterations = 0
    if nodes:
        for iterations in range(1, max_iterations + 1):
            dangling = math.fsum(ranks[node] for node in nodes if not adjacency[node])
            base = (1 - damping + damping * dangling) / len(nodes)
            updated = {node: base for node in nodes}
            for node, targets in adjacency.items():
                if targets:
                    contribution = damping * ranks[node] / len(targets)
                    for target in targets:
                        updated[target] += contribution
            difference = math.fsum(abs(updated[node] - ranks[node]) for node in nodes)
            ranks = updated
            if difference <= tolerance:
                converged = True
                break
    return {
        "nodes": nodes,
        "edges": [[node, target] for node, targets in adjacency.items() for target in targets],
        "import_cycles": _import_cycles(adjacency),
        "pagerank": ranks,
        "pagerank_converged": converged,
        "pagerank_iterations": iterations,
        "pagerank_damping": damping,
        "pagerank_tolerance": tolerance,
        "pagerank_max_iterations": max_iterations,
    }


def transitive_importers(index: dict[str, list[str]], seeds: Iterable[str]) -> list[dict]:
    """Return reachable importers by shortest depth, then file name.

    ``index`` points from a dependency to its direct importers. Every result
    gives the selected ``seed`` and immediate predecessor ``via``, so a witness
    can be reconstructed without storing every path prefix on deep chains.
    Sorted seeds and neighbors choose a deterministic shortest witness; every
    seed is excluded from the output even when reachable from another seed.
    Unknown targets have no fabricated edges. The caller owns removed-file and
    perimeter semantics.
    """
    adjacency = _normalise_graph(index)
    if isinstance(seeds, (str, bytes)):
        raise ValueError("seeds must be an iterable of string nodes")
    try:
        roots = list(seeds)
    except TypeError as exc:
        raise ValueError("seeds must be an iterable of string nodes") from exc
    if any(not isinstance(node, str) for node in roots):
        raise ValueError("seeds must contain string nodes")
    roots = sorted(set(roots))
    parent: dict[str, str | None] = {node: None for node in roots}
    origin = {node: node for node in roots}
    depth = {node: 0 for node in roots}
    pending = deque(roots)
    while pending:
        node = pending.popleft()
        for importer in adjacency.get(node, []):
            if importer not in parent:
                parent[importer] = node
                origin[importer] = origin[node]
                depth[importer] = depth[node] + 1
                pending.append(importer)

    return [
        {"file": node, "depth": depth[node], "via": parent[node], "seed": origin[node]}
        for node in sorted((node for node in parent if depth[node]), key=lambda item: (depth[item], item))
    ]
