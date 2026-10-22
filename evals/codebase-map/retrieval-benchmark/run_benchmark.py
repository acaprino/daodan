#!/usr/bin/env python3
"""Retrieval benchmark for Codebase Map symbol search candidates.

Candidate A is stdlib-only: exact anchors plus code-aware SQLite FTS5 and a
one-hop graph expansion. Candidates B and C add ONNX embeddings through
embed_rank.py, invoked with `uv run --script` when requested.

The corpus is a Codebase Map snapshot. By default it targets this repository's
`plugins/` tree, so generated host exports do not duplicate every symbol five
times. Gold symbol ids are checked against the corpus before scoring.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPTS = REPO / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))

import snapshot  # noqa: E402
import semantic_store  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
STOPWORDS = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "with", "from",
             "il", "lo", "la", "di", "e", "per", "con", "una", "uno", "che", "del", "della"}


def subtokens(text: str) -> list[str]:
    out: list[str] = []
    for raw in TOKEN_RE.findall(text or ""):
        pieces = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", raw)
        pieces = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", pieces)
        for piece in pieces.split():
            token = piece.lower()
            if len(token) >= 2 and token not in STOPWORDS and token not in out:
                out.append(token)
    return out


def render_signature(record: dict | None) -> str:
    if not record:
        return ""
    parts = []
    for param in record.get("params", []):
        text = param["name"]
        if param.get("kind") == "var_positional":
            text = "*" + text
        elif param.get("kind") == "var_keyword":
            text = "**" + text
        if param.get("annotation"):
            text += f": {param['annotation']}"
        if param.get("default") is not None:
            text += f" = {param['default']}"
        parts.append(text)
    suffix = f"({', '.join(parts)})"
    if record.get("returns"):
        suffix += f" -> {record['returns']}"
    if record.get("bases"):
        suffix += " bases " + " ".join(record["bases"])
    if record.get("attributes"):
        suffix += " attributes " + " ".join(item["name"] for item in record["attributes"])
    if record.get("decorators"):
        suffix += " decorators " + " ".join(record["decorators"])
    return suffix


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def metrics_for(ranked: list[str], expanded: list[str], query: dict) -> dict:
    expected = query.get("expected", [])
    dependencies = query.get("dependencies", [])
    grades = {symbol: 3 for symbol in expected}
    grades.update({symbol: 2 for symbol in dependencies if symbol not in grades})
    top10, top20 = ranked[:10], ranked[:20]
    first = next((index + 1 for index, symbol in enumerate(top10) if symbol in expected), None)
    dcg = sum(grades.get(symbol, 0) / math.log2(index + 2) for index, symbol in enumerate(top10))
    ideal = sorted(grades.values(), reverse=True)[:10]
    idcg = sum(grade / math.log2(index + 2) for index, grade in enumerate(ideal))
    return {
        "symbol_recall_at_20": len(set(top20) & set(expected)) / len(expected) if expected else 0.0,
        "mrr_at_10": 1.0 / first if first else 0.0,
        "ndcg_at_10": dcg / idcg if idcg else 0.0,
        "dependency_recall_at_15": (
            len(set(expanded[:15]) & set(dependencies)) / len(dependencies) if dependencies else None),
    }


def aggregate(rows: list[dict]) -> dict:
    def mean(key):
        values = [row[key] for row in rows if row.get(key) is not None]
        return sum(values) / len(values) if values else None

    return {key: mean(key) for key in
            ("symbol_recall_at_20", "mrr_at_10", "ndcg_at_10", "dependency_recall_at_15")}


def build_corpus(manifest: Path) -> tuple[list[dict], dict[str, list[str]], float]:
    started = time.perf_counter()
    docs = []
    adjacency: dict[str, list[str]] = {}
    with open_snapshot(manifest) as store:
        with semantic_store.semantic_reader(store) as db:
            index = semantic_store._ImpactIndex(db)
            for row in db.execute(semantic_store._SYMBOL_SELECT).fetchall():
                fields = semantic_store._symbol_fields(row)
                callers, callees = semantic_store._direct_edges(db, index, row)
                neighbours = {}
                for group in (callers, callees):
                    for item in group.values():
                        neighbours[item[0][0]] = neighbours.get(item[0][0], 0) + item[1]
                adjacency[fields["symbol_id"]] = [symbol for symbol, _ in sorted(
                    neighbours.items(), key=lambda item: (-item[1], item[0]))]
                signatures = fields["signatures"] or []
                rendered = "; ".join(render_signature(item) for item in signatures)
                qualified = fields["name"]
                document = " ".join(value for value in (
                    fields["kind"], qualified, rendered, fields["file"],
                    " ".join(sorted({item[0][2] for group in (callers, callees) for item in group.values()})),
                ) if value)
                docs.append({
                    "id": fields["symbol_id"], "file": fields["file"], "name": qualified,
                    "short": qualified.split(".")[-1], "kind": fields["kind"],
                    "signature": rendered, "document": document,
                })
    docs.sort(key=lambda item: item["id"])
    return docs, adjacency, time.perf_counter() - started


def build_fts(docs: list[dict], path: Path) -> float:
    started = time.perf_counter()
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE docs(id TEXT PRIMARY KEY, file TEXT, name TEXT, short TEXT, kind TEXT, signature TEXT, document TEXT)")
        db.execute("CREATE VIRTUAL TABLE fts USING fts5(id UNINDEXED, symbol_exact, symbol_subtokens, signature_text, document_text)")
        for doc in docs:
            exact = f"{doc['id']} {doc['name']} {doc['short']}"
            sub = " ".join(subtokens(exact + " " + doc["file"]))
            signature_tokens = " ".join(subtokens(doc["signature"]))
            document_tokens = " ".join(subtokens(doc["document"]))
            db.execute("INSERT INTO docs VALUES(?,?,?,?,?,?,?)",
                       (doc["id"], doc["file"], doc["name"], doc["short"], doc["kind"], doc["signature"], doc["document"]))
            db.execute("INSERT INTO fts VALUES(?,?,?,?,?)",
                       (doc["id"], exact, sub, signature_tokens, document_tokens))
    return time.perf_counter() - started


def anchors(docs: list[dict], query: str) -> list[str]:
    lowered = query.lower()
    raw_tokens = {token.lower() for token in re.findall(r"[A-Za-z0-9_.]+", query)}
    short_counts = {}
    for doc in docs:
        short = doc["short"].lower()
        short_counts[short] = short_counts.get(short, 0) + 1
    scored = []
    for doc in docs:
        score = 0
        short = doc["short"].lower()
        if doc["id"].lower() in lowered or ("." in doc["name"] and doc["name"].lower() in raw_tokens):
            score = 3
        elif (short in raw_tokens and ("_" in short or len(short) >= 12)
              and short_counts.get(short, 0) <= 5):
            score = 2
        elif "/" in doc["file"] and doc["file"].lower() in lowered:
            score = 1
        if score:
            scored.append((-score, short_counts.get(short, 0), -len(doc["name"]), doc["id"]))
    return [symbol for *_, symbol in sorted(scored)]


def fts_ranking(db: sqlite3.Connection, docs: list[dict], query: str, limit: int = 100) -> tuple[list[str], float]:
    started = time.perf_counter()
    terms = subtokens(query)[:40]
    ranked = anchors(docs, query)
    if terms:
        match = " OR ".join(f'"{term}"*' for term in terms)
        try:
            rows = db.execute(
                "SELECT id FROM fts WHERE fts MATCH ? ORDER BY bm25(fts, 10.0, 5.0, 3.0, 1.0) LIMIT ?",
                (match, limit)).fetchall()
            for (symbol,) in rows:
                if symbol not in ranked:
                    ranked.append(symbol)
        except sqlite3.OperationalError:
            pass
    return ranked, time.perf_counter() - started


def expand(ranked: list[str], adjacency: dict[str, list[str]]) -> list[str]:
    out: list[str] = []
    for seed in ranked[:20]:
        for symbol in (seed, *adjacency.get(seed, [])):
            if symbol not in out:
                out.append(symbol)
    return out


def score_rankings(name: str, rankings: dict[str, list[str]], latencies: dict[str, float],
                   queries: list[dict], adjacency: dict[str, list[str]], extra: dict) -> dict:
    per_query = []
    for query in queries:
        ranked = rankings.get(query["id"], [])
        values = metrics_for(ranked, expand(ranked, adjacency), query)
        per_query.append({"id": query["id"], "kind": query["kind"],
                          "latency_seconds": latencies.get(query["id"], 0.0),
                          "top_5": ranked[:5], **values})
    values = [item["latency_seconds"] for item in per_query]
    return {"model": name, "status": "ok", **extra,
            "metrics": aggregate(per_query),
            "latency": {"mean_seconds": sum(values) / len(values) if values else 0.0,
                        "p95_seconds": percentile(values, 0.95)},
            "queries": per_query}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=REPO / "plugins",
                        help="corpus target when --manifest is not supplied")
    parser.add_argument("--manifest", type=Path, help="existing snapshot manifest")
    parser.add_argument("--queries", type=Path, default=HERE / "queries.json")
    parser.add_argument("--out", type=Path, default=HERE / "results" / "latest")
    parser.add_argument("--models", default="A", help="comma list: A,B,C,D")
    parser.add_argument("--keep-snapshot", action="store_true")
    args = parser.parse_args(argv)
    models = [item.strip().upper() for item in args.models.split(",") if item.strip()]
    if not models or any(item not in {"A", "B", "C", "D"} for item in models):
        raise SystemExit("models must be a comma list containing A, B, C and/or D")

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = args.manifest or (args.out / "manifest.sqlite")
    snapshot_seconds = 0.0
    if not args.manifest:
        started = time.perf_counter()
        snapshot.write_snapshot(args.target, manifest)
        snapshot_seconds = time.perf_counter() - started

    queries = json.loads(args.queries.read_text(encoding="utf-8"))["queries"]
    docs, adjacency, corpus_seconds = build_corpus(manifest)
    known = {doc["id"] for doc in docs}
    missing = sorted({symbol for query in queries
                      for symbol in query.get("expected", []) + query.get("dependencies", [])
                      if symbol not in known})
    if missing:
        raise SystemExit("gold symbols missing from corpus:\n" + "\n".join(missing))
    (args.out / "corpus.jsonl").write_text(
        "".join(json.dumps(doc, ensure_ascii=False) + "\n" for doc in docs), encoding="utf-8")
    (args.out / "adjacency.json").write_text(json.dumps(adjacency), encoding="utf-8")

    fts_seconds = build_fts(docs, args.out / "corpus.sqlite")
    rankings_a: dict[str, list[str]] = {}
    latencies_a: dict[str, float] = {}
    with sqlite3.connect(args.out / "corpus.sqlite") as db:
        for query in queries:
            rankings_a[query["id"]], latencies_a[query["id"]] = fts_ranking(db, docs, query["query"])
    (args.out / "rankings-a.json").write_text(json.dumps(
        {"rankings": rankings_a, "latencies": latencies_a}), encoding="utf-8")

    results = {"corpus": {"target": str(args.target), "manifest": str(manifest),
                          "files_and_symbols": len(docs),
                          "snapshot_build_seconds": snapshot_seconds,
                          "corpus_build_seconds": corpus_seconds,
                          "fts_build_seconds": fts_seconds},
               "models": []}
    if "A" in models:
        results["models"].append(score_rankings(
            "A exact+code-aware-FTS5+graph", rankings_a, latencies_a, queries, adjacency,
            {"index_build_seconds": snapshot_seconds + corpus_seconds + fts_seconds}))
    for key, label in (("B", "B jina-embeddings-v2-base-code ONNX INT8+FTS5+graph"),
                       ("C", "C CodeRankEmbed ONNX INT8+FTS5+graph"),
                       ("D", "D EmbeddingGemma 2 text ONNX INT8+FTS5+graph")):
        if key not in models:
            continue
        uv = shutil.which("uv")
        if uv is None:
            results["models"].append({"model": label, "status": "unavailable",
                                      "reason": "uv is required to run embed_rank.py"})
            continue
        output = args.out / f"rankings-{key.lower()}.json"
        started = time.perf_counter()
        proc = subprocess.run(
            [uv, "run", "--no-project", "--script", str(HERE / "embed_rank.py"),
             "--corpus", str(args.out / "corpus.jsonl"), "--queries", str(args.queries),
             "--fts-rankings", str(args.out / "rankings-a.json"), "--model", key,
             "--cache-dir", str(args.out / "models"), "--out", str(output)],
            capture_output=True, text=True)
        elapsed = time.perf_counter() - started
        if proc.returncode != 0:
            results["models"].append({"model": label, "status": "failed",
                                      "reason": (proc.stderr or proc.stdout)[-4000:]})
            continue
        payload = json.loads(output.read_text(encoding="utf-8"))
        results["models"].append(score_rankings(
            label, payload["rankings"], payload["latencies"], queries, adjacency,
            {"index_build_seconds": elapsed, "model_metadata": payload["model"],
             "document_encode_seconds": payload["document_encode_seconds"]}))
    (args.out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
