#!/usr/bin/env python3
"""Generate a deterministic stratified gold set from one benchmark corpus.

The queries are derived from symbol names and signatures, which biases them
toward identifier vocabulary. They therefore stress scale, duplication and
language mix on large projects; they do not replace hand-written or
history-derived queries. The bias is declared in RESULTS.md of each run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def words(text: str) -> list[str]:
    out: list[str] = []
    for raw in TOKEN_RE.findall(text or ""):
        for piece in re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", raw).split():
            token = piece.lower()
            if len(token) >= 3 and token not in out:
                out.append(token)
    return out


def key(seed: str, symbol: str) -> str:
    return hashlib.sha256(f"{seed}:{symbol}".encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--adjacency", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-kind", type=int, default=40)
    parser.add_argument("--seed", default="daodan-retrieval-v2")
    args = parser.parse_args()

    docs = [json.loads(line) for line in args.corpus.read_text(encoding="utf-8").splitlines() if line]
    adjacency = json.loads(args.adjacency.read_text(encoding="utf-8"))
    pool = [doc for doc in docs
            if doc["kind"] in {"function", "method", "class"}
            and len(doc["short"]) >= 4
            and "test" not in doc["file"].lower()
            and doc["signature"]]

    def sample(items, count, offset):
        ordered = sorted(items, key=lambda doc: key(args.seed + str(offset), doc["id"]))
        return ordered[:count]

    queries: list[dict] = []

    def add(kind: str, doc: dict, query: str) -> None:
        item = {"id": f"{kind}-{len(queries) + 1:03d}", "kind": kind, "query": query,
                "expected": [doc["id"]]}
        neighbours = adjacency.get(doc["id"], [])
        if neighbours:
            item["dependencies"] = neighbours[:2]
        queries.append(item)

    for doc in sample(pool, args.per_kind, 1):
        add("exact", doc, f"{doc['file']}::{doc['name']}")
    for doc in sample(pool, args.per_kind, 2):
        add("traceback", doc, f"Traceback (most recent call last): ValueError in {doc['short']} ({doc['signature']})")
    for doc in sample(pool, args.per_kind, 3):
        add("code", doc, doc["signature"] if doc["kind"] == "class" else f"def {doc['short']}{doc['signature']}")
    en_templates = ["which symbol handles {}", "find the implementation responsible for {}",
                    "where is {} implemented", "locate the code that performs {}"]
    for index, doc in enumerate(sample(pool, args.per_kind, 4)):
        phrase = " ".join(words(doc["short"])[:5]) or doc["short"]
        add("nl-en", doc, en_templates[index % len(en_templates)].format(phrase))
    it_templates = ["quale simbolo gestisce {}", "trova l'implementazione responsabile di {}",
                    "dove è implementato {}", "individua il codice che esegue {}"]
    for index, doc in enumerate(sample(pool, args.per_kind, 5)):
        phrase = " ".join(words(doc["short"])[:5]) or doc["short"]
        add("nl-it", doc, it_templates[index % len(it_templates)].format(phrase))

    args.out.write_text(json.dumps({"version": 2, "generated": True, "seed": args.seed,
                                    "queries": queries}, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"{len(queries)} queries -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
