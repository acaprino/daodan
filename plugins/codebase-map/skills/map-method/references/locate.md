# Locating code for a change

The measured loop for finding the code a request is about, before any edit.
On 23 private tasks it solved as many as any other access path and cost the
least per solved task (map plus lexical search 21, hybrid search 19, a pre-built
packet 19; the differences are within noise), and search results are leads:
`codebase_map_read` verifies the bytes you act on.

## The loop

1. **Names first.** Pull every concrete name out of the request: identifiers,
   file names, error text, traceback frames, the domain nouns it uses. Keep
   them as one list; the failures of the measurement were half-read requests.
2. **Search by name group.** `codebase_map_search(run_id, query)`; without an
   MCP server, `snapshot.py search MANIFEST --query Q`. An exact symbol
   (`path::Name` or a bare identifier) and a traceback frame rank first; other
   words match by subtoken, so `InvoiceTotal` finds `invoice_total`. One query
   per name group, not the whole request pasted at once. A `gaps` entry naming
   `codebase_map_index` means the index is missing, stale or failed: run that
   (with `break_lock` after a crashed build), then search again.
3. **Expand only what is pertinent.** `codebase_map_outline` on the hit's file
   shows its other symbols; `codebase_map_graph` with `hops=1` shows callers and
   callees. Stop at one hop unless a hit is a thin wrapper.
4. **Read by symbol.** `codebase_map_read` with the entity ids you keep; a whole
   file only when it is short. Every hit you read is verified against the
   snapshot; a file edited since the snapshot makes the read fail with
   "source changed; refresh the manifest", which the search does not detect.
5. **Bound the edit.** `codebase_map_edit_impact` on the symbols you will change
   lists callers, tests and obligations.
6. **Reproduce, then fix.** Before the first edit, write one test that fails for
   the reason the request states. Edit, run the tests, stop.

## Budgets from the measurement

- About 6 searches and 10 symbol reads per task; more usually means the names
  came from the wrong half of the request.
- An empty search is reworded once (synonym, the file name, a caller's name);
  the second time, reread the request.
- `grep` over the tree only when no map exists, or to confirm a string literal.
- A search costs no model tokens; its results do enter the context, so keep
  `limit` at 20 and read the top hits rather than widening the list.

## Perimeter

Measured on Python projects, a strong model and precise requests, one
replicate. Vague requests, weak models, large repositories and other languages
are unmeasured; the index covers every parsed language, since subtokens are
language-agnostic. One hypothesis, untested: listing every requirement of the
request before the first edit, and reproducing each, since 9 of the 10 measured
failures had the right file open and did half of the request.
