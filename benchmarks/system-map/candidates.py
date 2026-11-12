"""Zero-cost trial: candidate nodes made by code from the links, and arrows as edges between nodes.

Candidates: the dominator partition of the file graph from the entry points. A file belongs to the
entry it is reached only through; a file reached through several entries heads its own candidate.
Store keys are grouped by collection. Then the hand-made nodes are expressed as unions of candidates,
and arrows between hand-made nodes are the links between their files, with nothing to verify.

    python -I candidates.py LINKS.json EXPECTED.json FILES.txt
"""
import collections
import json
import sys
from pathlib import Path

links = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
all_files = {f for f in Path(sys.argv[3]).read_text(encoding="utf-8").split() if not f.endswith("/")}


def place(end):
    if end.startswith("store:"):
        return "store:" + "/".join(end[6:].split("/")[:2])  # one candidate per collection or state key
    return end.split("::")[0]


graph = collections.defaultdict(set)
for e in links["edges"]:
    a, b = place(e["from"]), place(e["to"])
    if a != b and e["type"] in ("chiama", "attiva"):
        graph[a].add(b)
entries = sorted({place(e["symbol"]) for e in links["entries"]})
ROOT = "<root>"
graph[ROOT] = set(entries)

# Dominators (Cooper, Harvey, Kennedy) over the files reachable from the entry points.
order, seen, stack = [], {ROOT}, [(ROOT, iter(sorted(graph[ROOT])))]
while stack:
    node, children = stack[-1]
    child = next(children, None)
    if child is None:
        order.append(node)
        stack.pop()
    elif child not in seen:
        seen.add(child)
        stack.append((child, iter(sorted(graph.get(child, ())))))
rpo = order[::-1]
index = {n: i for i, n in enumerate(rpo)}
preds = collections.defaultdict(set)
for a in rpo:
    for b in graph.get(a, ()):
        if b in index:
            preds[b].add(a)
idom = {ROOT: ROOT}
changed = True
while changed:
    changed = False
    for node in rpo[1:]:
        done = [p for p in preds[node] if p in idom]
        new = done[0]
        for p in done[1:]:
            x, y = p, new
            while x != y:
                while index[x] > index[y]:
                    x = idom[x]
                while index[y] > index[x]:
                    y = idom[y]
            new = x
        if idom.get(node) != new:
            idom[node] = new
            changed = True


def head(node):
    while idom[node] != ROOT:
        node = idom[node]
    return node


candidate = {n: head(n) for n in idom if n != ROOT}
groups = collections.defaultdict(set)
for n, h in candidate.items():
    groups[h].add(n)
for e in links["edges"]:  # stores: one candidate per collection or state key
    for end in (e["from"], e["to"]):
        if end.startswith("store:"):
            groups[place(end)].add(place(end))
            candidate[place(end)] = place(end)
code = {f for f in all_files if f.split(".")[-1] in ("py", "ts", "tsx", "js", "jsx", "rs", "kt", "html")}
unreached = sorted(code - set(candidate))
sizes = collections.Counter(min(len(g), 10) for g in groups.values())
print(f"candidates {len(groups)} (stores {sum(1 for g in groups if g.startswith('store:'))}); "
      f"files in a candidate {sum(1 for n in candidate if not n.startswith('store:'))}; code files reached by no entry {len(unreached)}")
print("sizes (10 = 10 or more):", dict(sorted(sizes.items())))

print("== hand-made nodes as unions of candidates")
owner = {}
for node in expected["nodes"]:
    members = set(node.get("files") or []) | {place(m[6:] and m) for m in node.get("members") or []}
    if not members:
        continue
    for m in members:
        owner.setdefault(m, node["name"])
    used = {candidate[m] for m in members if m in candidate}
    union = set().union(*(groups[c] for c in used)) if used else set()
    inside = union & members
    loose = sorted(m.split("/")[-1] for m in members if m not in candidate)
    print(f"{node['name']}: {len(members)} members, {len(used)} candidates; members covered {len(inside)}; "
          f"extra files the candidates bring {len(union - members)}; reached by no entry {loose}")
    for c in sorted(used):
        extra = sorted(x.split("/")[-1] for x in groups[c] - members)
        print(f"    {c.split('/')[-1]} ({len(groups[c])} files){': also ' + ', '.join(extra[:6]) + (' ...' if len(extra) > 6 else '') if extra else ''}")

print("== arrows: links between the files of two hand-made nodes (no chain, nothing to verify)")
pairs = collections.Counter()
for e in links["edges"]:
    a, b = owner.get(place(e["from"])), owner.get(place(e["to"]))
    if e["type"] == "legge":
        a, b = owner.get(place(e["from"])), owner.get(place(e["to"]))
    if a and b and a != b:
        pairs[(a, b, e["type"])] += 1
for (a, b, kind), n in sorted(pairs.items()):
    print(f"  {a} -> {b}: {kind} x{n}")

mixed = [c for c, files in groups.items() if len({owner[f] for f in files if f in owner}) > 1]
print("== candidates that hold files of two hand-made nodes:", mixed)
