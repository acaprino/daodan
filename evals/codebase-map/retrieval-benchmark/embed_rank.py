# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=1.26",
#   "onnxruntime>=1.17",
#   "tokenizers>=0.15",
#   "huggingface_hub>=0.20",
# ]
# ///
"""Encode a benchmark corpus with one pinned ONNX embedding model.

This sidecar is deliberately separate from run_benchmark.py: candidate A stays
stdlib-only, while B and C pay their dependency and download cost only when
selected. Models are downloaded at a pinned revision and the ONNX file digest
is recorded in the output. No custom model code is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from tokenizers import Tokenizer

MODELS = {
    "B": {
        "repo": "jinaai/jina-embeddings-v2-base-code",
        "revision": "516f4baf13dec4ddddda8631e019b5737c8bc250",
        "model_file": "onnx/model_quantized.onnx",
        "query_prefix": "",
        "license": "Apache-2.0",
    },
    "C": {
        # The official nomic-ai/CodeRankEmbed repository ships no ONNX graph.
        # This pinned community INT8 export is recorded here and in RESULTS.md;
        # its digest is computed from the downloaded bytes at run time.
        "repo": "mrsladoje/CodeRankEmbed-onnx-int8",
        "revision": "e74f446dc6e67e29fcee77213472c142f73a6bbb",
        "model_file": "onnx/model.onnx",
        "query_prefix": "Represent this query for searching relevant code: ",
        "license": "MIT (base model); community ONNX export",
        "base_model": "nomic-ai/CodeRankEmbed",
    },
}
FILES = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]


def encode(session, tokenizer, texts: list[str], batch_size: int = 32) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    vectors = []
    input_names = {item.name for item in session.get_inputs()}
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        encoded = tokenizer.encode_batch(batch)
        max_len = max(len(item.ids) for item in encoded)
        input_ids = np.zeros((len(batch), max_len), dtype=np.int64)
        attention = np.zeros((len(batch), max_len), dtype=np.int64)
        for row, item in enumerate(encoded):
            input_ids[row, :len(item.ids)] = item.ids
            attention[row, :len(item.attention_mask)] = item.attention_mask
        feeds = {}
        if "input_ids" in input_names:
            feeds["input_ids"] = input_ids
        if "attention_mask" in input_names:
            feeds["attention_mask"] = attention
        if "token_type_ids" in input_names:
            feeds["token_type_ids"] = np.zeros_like(input_ids)
        outputs = session.run(None, feeds)
        hidden = next(item for item in outputs if item.ndim == 3)
        mask = attention[..., None].astype(np.float32)
        pooled = (hidden.astype(np.float32) * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1.0)
        vectors.append(pooled)
    result = np.vstack(vectors)
    result /= np.maximum(np.linalg.norm(result, axis=1, keepdims=True), 1e-12)
    return result, time.perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--fts-rankings", type=Path, required=True)
    parser.add_argument("--model", choices=sorted(MODELS), required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    config = MODELS[args.model]
    local = Path(snapshot_download(
        repo_id=config["repo"], revision=config["revision"],
        allow_patterns=[config["model_file"], *FILES],
        local_dir=args.cache_dir / args.model))
    model_path = local / config["model_file"]
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    tokenizer = Tokenizer.from_file(str(local / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=8192)
    tokenizer.enable_padding()
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])

    docs = [json.loads(line) for line in args.corpus.read_text(encoding="utf-8").splitlines() if line]
    queries = json.loads(args.queries.read_text(encoding="utf-8"))["queries"]
    fts = json.loads(args.fts_rankings.read_text(encoding="utf-8"))["rankings"]
    doc_vectors, encode_seconds = encode(session, tokenizer, [doc["document"] for doc in docs])

    # Exact anchors stay first, as in candidate A. Without an anchor, dense and
    # lexical ranks are fused with the dense rank carrying most of the weight.
    from run_benchmark import anchors  # same directory when run as a script file

    rankings: dict[str, list[str]] = {}
    latencies: dict[str, float] = {}
    doc_ids = [doc["id"] for doc in docs]
    for query in queries:
        started = time.perf_counter()
        vector, _ = encode(session, tokenizer, [config["query_prefix"] + query["query"]], batch_size=1)
        scores = (doc_vectors @ vector[0]).astype(float)
        dense = [doc_ids[index] for index in np.argsort(-scores)]
        anchor_ids = anchors(docs, query["query"])
        if anchor_ids:
            ranked = anchor_ids + [symbol for symbol in dense if symbol not in anchor_ids]
        else:
            dense_rank = {symbol: index for index, symbol in enumerate(dense)}
            fts_rank = {symbol: index for index, symbol in enumerate(fts.get(query["id"], []))}
            ranked = sorted(doc_ids, key=lambda symbol: (
                0.75 / (60 + dense_rank[symbol]) + 0.25 / (60 + fts_rank.get(symbol, len(doc_ids))),
                symbol))
        rankings[query["id"]] = ranked[:100]
        latencies[query["id"]] = time.perf_counter() - started
    args.out.write_text(json.dumps({
        "model": {**config, "onnx_sha256": digest, "onnx_bytes": model_path.stat().st_size},
        "document_encode_seconds": encode_seconds,
        "rankings": rankings, "latencies": latencies,
    }), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
