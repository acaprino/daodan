# Optional local embeddings

Use embeddings only when explicitly selected. The textual index works alone.
Indexing, ranking and graph navigation make no LLM calls. Semantic cards retain
their separate reading cost. This provider is opt-in; retrieval scores do not
establish correctness, independence or permission to edit.

## Runtime and artifacts

Keep the map's original Python interpreter and parser environment for snapshot
and source validation. `embedding_worker.py` starts the explicit optional Python
with `-I` and runs only its own encoding entry. The backend never imports the
project or the map/parser modules. Its private protocol carries status/counts;
numeric output stays in temporary files beside the derived index. The parent
sends an explicit stop and closes or kills the process on failure/timeout.

Provisioning is a separate, explicitly chosen operation. The script metadata pins
NumPy 2.4.6, ONNX Runtime 1.31.0 and tokenizers 0.23.3. Reuse an existing isolated
environment when available; no installation or model download happens in a
query. An unavailable runtime or local artifact produces a failure, not a
fabricated empty result. Windows CPU inference is exercised; Linux has upstream
runtime support but requires its own live probe.

Share weights across projects in `%LOCALAPPDATA%/Daodan/models/EmbeddingGemma2/REVISION/`
on Windows, or `$XDG_CACHE_HOME/daodan/models/EmbeddingGemma2/REVISION/` on Linux
(default `~/.cache`). Omitting `model_dir` selects that per-user revision folder.
An explicit model folder remains supported. Only each project's derived vectors
are project-specific. The folder holds `tokenizer.json`, `onnx/model_q4.onnx` and
its weights `onnx/model_q4.onnx_data` (174,028,800 bytes, 166 MiB), about 206 MB
in all. This avoids repeated disk copies/downloads; RAM loading happens once per
provider process, retained for its session. No global background daemon is installed.

The supported artifact is the q4 text graph of `onnx-community/embeddinggemma-2-ONNX`
(Apache-2.0, base `google/embeddinggemma-2`) at revision
`daa72c51243991dfcaf9f9137d2c573d8f7790c0`. Copy those three files from that
revision. The helper verifies graph SHA-256
`f9eeba97acddf139b8ee2ddf04bc30dceafa88de93fadf74d7644e0d61a477a9`, weights
SHA-256 `c3975f2d1ab7a1878ae31a7d7a9b7804a827aff3800b60dfceafce21cac3df49`
and tokenizer SHA-256
`4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4`
before native loading, then loads the graph by path because its weights are an
external file. It executes no custom model Python or custom operators. The
graph's image, video and audio inputs receive empty arrays; its pooled
`sentence_embedding` (768 dimensions) is the vector.

Documents are prefixed `title: none | text: ` and queries
`task: code retrieval | query: `, the model's retrieval prompts; both prefixes
belong to the provider fingerprint. Inputs are cut at 2048 tokens; this is an
encoder limit, not an LLM context or billing measurement. Each input runs in its
own native inference, without padding, so a cached vector depends only on its
text. On a four-thread CPU an entity takes about 1 to 2 seconds: index a
project once, then refresh only changed entities.

## File request interface

Read a `daodan/embedding-request/v1` JSON file. Required fields are `schema`,
`operation` (`index` or `query`), `manifest` and `index`; `model_dir` is optional. `query`
also requires text and accepts `limit` (1..1000, default 500). Paths below are
illustrative; use the caller-bound run and an explicitly prepared model folder.

```json
{
  "schema": "daodan/embedding-request/v1",
  "operation": "index",
  "manifest": "/project/.codebase-map/runs/run-id/snapshot/manifest.sqlite",
  "index": "/project/.codebase-map/runs/run-id/snapshot/embeddings.sqlite",
  "model_dir": "/prepared-models/EmbeddingGemma2"
}
```

Run with the map interpreter:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/embedding_worker.py" \
  --request REQUEST.json --runtime-python /explicit/optional-environment/python \
  --report-out SNAPSHOT_DIRECTORY/embedding-report.json
```

The index and report stay beside the manifest. Existing reports are never
replaced. Atomic exclusive publication requires same-directory hard links;
unsupported filesystems fail closed. Linked paths, escapes and canonical
store collisions are refused. The manifest
is never rewritten. Stdout contains status, counts and a report path; detailed
results stay on disk. A query never refreshes an index implicitly.

## Cache and consumption

`refresh_index(manifest, index, provider=...)` publishes a complete SQLite
generation atomically. Cache identity includes the exact encoded text (path,
name, signature and source), model, weights, tokenizer, runtime, encoder,
prefixes and document versions. Rename/content changes invalidate affected inputs; deleted entities
and unused vectors disappear from the new generation. An interrupted refresh
retains the previous generation. A stale generation cannot serve a current
query. Locks prevent concurrent publishers; vector checksums, dimensions and
finite nonzero norms are validated before use.

Use `ProcessProvider(optional_python, model_dir, manifest.parent)` as a context
manager. `search(manifest, index, query, provider=..., limit=...)` returns a
`daodan/embedding-result/v1` with snapshot/document/provider/artifact/query
bindings, bounded entity ranks, counts and elapsed time. No vectors enter this
result. Search also publishes an immutable `embedding-query-<digest>.json`
receipt beside the index, covering query, ranks, counts and artifact binding.
An identical receipt can be reused. Pass the result explicitly as
`retrieval.search(..., embedding_result=result)`. The consumer reads the actual
artifact, inventory and receipt; it starts no encoder. Relabeled queries or
changed ranks fail validation. A stale result falls
back to textual ranking with an explicit gap; malformed results are rejected.

Verified exact anchors retain precedence. Remaining ranks use the benchmark's
versioned policy `exact-rrf75-25-k60-v1`: dense weight 0.75, lexical weight 0.25,
rank offset 60. No similarity threshold can close an impact or validation gap.
The provider stays opt-in: it costs indexing time, never tokens.
