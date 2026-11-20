"""Do small local embedders group the certified flows that are the same chain, and find a flow by its name?

    uv run --no-project --with model2vec --with numpy [--with sentence-transformers] python embed_probe.py \
        chains CARDS.json VERIFIED.json MODEL [MODEL ...]
    ... python embed_probe.py find LABELS.json MODEL [MODEL ...]
    ... python embed_probe.py rank QUERIES.json MODEL [MODEL ...]

`chains`: CARDS.json and VERIFIED.json are those of `traces.py`; two flows are the same chain when their last three
edges are the same edges of the links, and a similarity is judged by how well it says so. `find`: LABELS.json is
`{"names": [...], "wanted": [{"query": "...", "right": [names]}]}`, written by a person: for each query the names
that answer it, none when nothing does. A model answers a query with its nearest name, or with nothing under a
threshold; the score is the share of queries answered rightly at the best threshold. A model whose name starts with
`st:` is a sentence-transformers model, the others are model2vec. `words` is the baseline with no model: the share
of words two texts have in common. `rank`: QUERIES.json is what `embed_queries.py` writes, many requests in words
with their right flow or part; per kind and voice, how often the right one is the nearest and among the nearest
three, against the names alone and against the longer records. Results in the README, «Embedder piccoli».
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np


def encoder(name: str):
    """Texts to unit vectors, by a model2vec model or, with `st:`, a sentence-transformers one."""
    if name == "words":
        return None
    if name.startswith("st:"):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(name[3:])  # no trust_remote_code: a model that needs its own code is not run here
        prefix = "query: " if "e5" in name else ""
        return lambda texts: model.encode([prefix + t for t in texts], normalize_embeddings=True)
    from model2vec import StaticModel
    model = StaticModel.from_pretrained(name)

    def encode(texts):
        v = model.encode(texts)
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
    return encode


def likeness(name: str, first: list[str], second: list[str]) -> np.ndarray:
    """The matrix of how alike each text of `first` is to each of `second`."""
    encode = encoder(name)
    if encode is None:
        bags = [[set(t.casefold().split()) for t in texts] for texts in (first, second)]
        return np.array([[len(a & b) / max(1, len(a | b)) for b in bags[1]] for a in bags[0]])
    return encode(first) @ encode(second).T


def chains(cards_file: str, verified_file: str, models: list[str]) -> None:
    cards = {c["entry"]: c for c in json.loads(Path(cards_file).read_text(encoding="utf-8"))}
    flows = []
    for item in json.loads(Path(verified_file).read_text(encoding="utf-8")):
        by = {s["n"]: s for s in cards[item["entry"]]["steps"]}
        flows += [{"name": f["nome"], "tail": tuple(by[n]["edge"] for n in f["passi"][-3:])} for f in item["accepted"]]
    names = [f["name"] for f in flows]
    pairs = list(combinations(range(len(flows)), 2))
    same = np.array([flows[a]["tail"] == flows[b]["tail"] for a, b in pairs])
    print(f"flows {len(flows)}, names {len(set(names))}, same-chain pairs {int(same.sum())} of {len(pairs)}")
    for model in models:
        alike = likeness(model, names, names)
        score, out = np.array([alike[a, b] for a, b in pairs]), (0.0, 0.0, 0.0, 0.0)
        for t in np.unique(np.round(score, 2)):
            said = score >= t
            hit = int((said & same).sum())
            if hit:
                p, r = hit / said.sum(), hit / same.sum()
                out = max(out, (2 * p * r / (p + r), p, r, float(t)))
        print(f"{model.split('/')[-1]:34s} F1 {out[0]:.2f}  precision {out[1]:.2f}  recall {out[2]:.2f}  at {out[3]:.2f}")


def find(labels_file: str, models: list[str]) -> None:
    labels = json.loads(Path(labels_file).read_text(encoding="utf-8"))
    names, wanted = labels["names"], labels["wanted"]
    answerable = [w for w in wanted if w["right"]]
    print(f"queries {len(wanted)}, with an answer {len(answerable)}, names {len(names)}")
    for model in models:
        alike = likeness(model, [w["query"] for w in wanted], names)
        top, score = alike.argmax(axis=1), alike.max(axis=1)
        first = sum(names[top[i]] in w["right"] for i, w in enumerate(wanted) if w["right"])
        best = (0, 0.0)
        for t in np.unique(np.round(score, 2)):
            right = sum((score[i] >= t and names[top[i]] in w["right"]) or (score[i] < t and not w["right"])
                        for i, w in enumerate(wanted))
            best = max(best, (right, float(t)))
        print(f"{model.split('/')[-1]:34s} nearest is right {first} of {len(answerable)}  |  "
              f"right with «none» allowed {best[0]} of {len(wanted)} at {best[1]:.2f}")


def rank(queries_file: str, models: list[str]) -> None:
    sets = json.loads(Path(queries_file).read_text(encoding="utf-8"))["sets"]
    groups = sorted({(s["kind"], w["voice"]) for s in sets for w in s["wanted"]})
    print("requests:", {f"{k}/{v}": sum(w["voice"] == v for s in sets if s["kind"] == k for w in s["wanted"]) for k, v in groups},
          "| names per set:", sorted(len(s["names"]) for s in sets))
    for model in models:
        for index in ("names", "records"):
            hits = {group: [0, 0, 0] for group in groups}
            for one in sets:
                if not one["wanted"]:
                    continue
                alike = likeness(model, [w["query"] for w in one["wanted"]], one[index])
                order = np.argsort(-alike, axis=1)[:, :3]
                for i, wanted in enumerate(one["wanted"]):
                    count = hits[(one["kind"], wanted["voice"])]
                    top = [one["names"][j] for j in order[i]]
                    count[0] += top[0] in wanted["right"]
                    count[1] += any(name in wanted["right"] for name in top)
                    count[2] += 1
            print(f"{model.split('/')[-1]:28s} on {index:7s} " + "  ".join(
                f"{k}/{v}: 1st {a / n:.0%} top3 {b / n:.0%}" for (k, v), (a, b, n) in hits.items() if n))


def main(argv: list[str]) -> int:
    if len(argv) >= 4 and argv[1] == "rank":
        rank(argv[2], argv[3:])
        return 0
    if len(argv) >= 5 and argv[1] == "chains":
        chains(argv[2], argv[3], argv[4:])
        return 0
    if len(argv) >= 4 and argv[1] == "find":
        find(argv[2], argv[3:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
