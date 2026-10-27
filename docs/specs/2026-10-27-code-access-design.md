# Code access: search tool, locate guide and worker binding

Status: approved by the owner on 2026-10-27 ("approvata"), after a two-model
review (`.jcode/local/moe/run-20261027-193359-af419e/answer.md`) and the
reviewer's confirmation. Planning follows through the project-delivery cycle.

## Intent and authorization

After the end-to-end gate of 2026-10-27 (run
`.daodan/runs/20261026-code-context-e2e-gate`, `REPORT.md`; diary section
"2026-10-27: end-to-end gate on Modal" in
`docs/research/context-building-benchmarks.md`), the owner asked for a code
access method: a tool, a guide and a prompt so that the harness and the model
know how to find code effectively and efficiently. This document is the
specification that precedes planning, as `2026-10-26-neutral-project-specifications-design.md`
requires. Implementation starts only after approval.

## Evidence

Measured on 23 private tasks, one replicate, Sonnet 5.5 as the agent:

| Arm | Access path | Solved | Cost per solved task | Search latency |
|---|---|---|---|---|
| B0 | map + FTS5 lexical search + reproduce-then-fix | 21/23 | 0.268 USD | 1.24 s |
| B1 | map + hybrid search (EmbeddingGemma 2 + FTS5) | 19/23 | 0.307 USD | 1.55 s |
| A2 | pre-built static packet, no search | 19/23 | 0.338 USD | none |

Retrieval was a tie: read per file, both search arms surfaced the gold change in
23 of 23 runs. Agents used a median of 6 searches and about 10 symbol reads per
task. Nine of ten failures had the right file open and missed part of the
request. The pre-registered rule reads both comparisons as "no improvement".
The experiment's search tool called `retrieval.search(index, text, anchors=[],
limit=200)` and showed the first 20 entities with their signature
(`harness/gate_mcp.py:33`, `harness/loc.py:67-68`).

What the product has today (paths relative to `plugins/codebase-map/skills/map-method/`):

- `scripts/retrieval.py` builds the FTS5 index (`daodan/retrieval-index/v1`,
  ranking `exact-fts5-bm25-v1`, optional fusion `exact-rrf75-25-k60-v1`) and
  exposes `search(index_path, query, *, anchors, limit, embedding_result)`.
- Nothing in the product builds that index: `references/mcp.md:123-125` states
  that no command-line entry or MCP tool builds it. Only tests and the eval
  harness call `refresh_index`.
- `retrieval.search` has one caller, `scripts/scope_planner.py:493`, inside the
  context packet, and only when the caller names the index in `--indexes`
  (`project-delivery`'s `cycle_packets.py:384-389` passes its optional
  `indexes` configuration through). No MCP tool or CLI returns ranked results to
  the agent. `codebase_map_outline` offers only an unranked substring match on
  names and paths.
- Consumers give no search instruction. `project-delivery`'s
  `references/worker-brief.md:19` hands the implementer a `task-packet` as its
  read context. `work-controller`'s `isolated-worker.md` has no code-access line.
  `references/standalone.md:14-21` lists outline, graph, meta query and
  artifact, then edit impact and read.

The measured access path exists as a library function and as an experiment
harness tool, not as a product tool, and no agent is told to use it.

## Contract

1. **The lexical index is a run artifact, built with the map.** `snapshot.py
   write` and `snapshot.py carry` end by refreshing `<manifest
   directory>/retrieval.sqlite` through `retrieval.refresh_index` (incremental by
   document digest, `<index>.lock`, atomic replace, as today). `--no-index`
   skips it. The run artifact list already names `snapshot/retrieval.sqlite`.
   Queries never build or repair the index: a read stays a read, works on
   read-only storage and pays no cold build. The dense index stays explicit
   through `embedding_worker.py` and opt-in per project, by the owner's decision
   of 2026-10-27 ("opzionale", off by default).
2. **Refresh and repair are a deliverable.** `snapshot.py index MANIFEST
   [--check]` and the MCP tool `codebase_map_index(run_id, check=False)`
   (writes) report one state: `fresh` (binding and digests match), `missing`,
   `stale` (binding mismatch or digest drift), `corrupt` (file present, not a
   readable index), `failed` (FTS5 unavailable, lock held, write error). Without
   `--check` the command rebuilds `missing`, `stale` and `corrupt` and returns
   `fresh` or `failed`; with `--check` it reports and writes nothing. CLI exit
   codes: 0 `fresh`, 1 `failed`, 2 invocation error. Backfill of an existing map
   (a frozen snapshot, a run published before this change) is the same command
   on that manifest: it writes only `retrieval.sqlite` and its lock beside the
   manifest, never a snapshot file or a digest, so a published run keeps its
   identity. `_require_fts5`'s message is unchanged and surfaces as `failed`.
3. **A search tool returns ranked results.** MCP
   `codebase_map_search(run_id, query, anchors=[], limit=20)`, annotated
   read-only, and CLI `snapshot.py search MANIFEST --query Q [--anchor A ...]
   [--limit N] [--embedding-result PATH]`. Both call `retrieval.search`
   unchanged. `embedding_result` is not in the MCP schema: an agent cannot
   produce that receipt, so the wrapper passes `None` and fusion stays an
   explicit CLI or consumer choice. The result keeps the
   `daodan/retrieval-result/v1` envelope (exact, ambiguous, gaps, capabilities,
   truncated, ranking_policy) and trims each record to `entity_id`, `kind`,
   `path`, `start_line`, `end_line`, `signatures`, `provenance`, `score`. No
   source text: reading stays with `codebase_map_read`. A `missing`, `stale` or
   `corrupt` index returns the gap named after that state with the exact
   `codebase_map_index` or `snapshot.py index` call to run; nothing raises and
   nothing is rebuilt. `limit` is 1 to 100 at the MCP tool and 1 to 1000 at the
   CLI, the library's own bound, so acceptance 2 replays the experiment's
   recorded `limit=200` unchanged. The query reaches
   `retrieval.search` byte for byte: no sanitation, no fallback that could
   change the ranking.
4. **The context packet keeps working and gains the index on purpose.** With
   the index built by contract 1, a consumer that names it in `--indexes` moves
   from the `retrieval_missing` gap to exact matches and retrieval leads at
   `scope_planner.py:493`. This is intended: the packet becomes the measured
   index's view instead of a declared absence. It is also a behavior change for
   `project-delivery`'s `task-packet`, so it is declared here and pinned by the
   regression in acceptance 5 (same request, index absent then present:
   candidates, leads, token count and latency recorded before and after). A
   consumer that does not name the index sees no change.
5. **A locate guide states the measured loop.** New `references/locate.md` in
   `codebase-map:map-method`, at most 60 lines: extract names from the request
   (identifiers, error text, file names, traceback frames, domain nouns); search
   with them, exact symbol or traceback first, subtokens second, one query per
   name group; expand only what is pertinent with `codebase_map_outline` on the
   hit's file and `codebase_map_graph` one hop; read by symbol with
   `codebase_map_read`, a whole file only when it is short; call
   `codebase_map_edit_impact` on the symbols to change; before the first edit,
   write a test that fails for the reason the request states; edit, run the
   tests, stop. Budgets from the measurement: about 6 searches and 10 symbol
   reads per task; an empty search is reworded once, then the request is
   reread; `grep` over the tree only when no map exists. One stated hypothesis,
   marked untested: list every requirement of the request before the first edit
   and reproduce each, since 9 of 10 failures were half-read requests.
   `standalone.md` step 2 points to `locate.md`; `reading.md`'s Task views gains
   the row "Locating code for a change".
6. **Consumers bind the guide.** `project-delivery`'s `worker-brief.md` keeps
   the `task-packet` as the starting point of the read context and adds the
   locate line: the guide, the five tools, and the CLI form where no MCP server
   runs. The packet is never a substitute for the search; whether packet leads
   make agents skip the search is a behavioral hypothesis measured by
   acceptance 7, not assumed. `senior-review`'s
   `investigation-method/SKILL.md:29-34` takes `search` before `edit-impact`
   when a map exists. `work-controller` is not touched: it is a leaf and the
   brief carries the binding.

## Boundaries and acceptance

- No change to ranking, tokenizer, schema, `refresh_index` or `retrieval.search`
  themselves. No new dependency: FTS5 comes with the interpreter's SQLite.
- Versions: `codebase-map` 8.11.0 to 8.12.0 (new tools and reference);
  `project-delivery` and `senior-review` patch bumps; the marketplace release
  number does not move.
- Hand-maintained enumerations updated together: the tool table in
  `references/mcp.md:66-86`, `standalone.md`, the tool tuple in
  `tests/test_codebase_map_mcp_wire.py:130-131`, the prose assertions in
  `tests/test_codebase_map_compat.py`, and the tool count in
  `docs/plugins/codebase-map.md:288`.
- Acceptance, in order:
  1. **Environment pin, recorded with every parity result:** SHA-256 of
     `retrieval.py`, SQLite version and FTS5 compile options
     (`PRAGMA compile_options`), each frozen task's `tree_sha256` and
     `index_sha256` from `tasks/<id>/task.json`, and the exact query, anchors
     and limit of every replayed call. Ranking and tokenizer version strings are
     necessary, not sufficient.
  2. **Parity through the new path, zero model cost:** for every search query
     recorded in the 69 Modal run logs (`results/runs-modal/<run_id>/loc.jsonl`),
     `snapshot.py search` on an index produced by `snapshot.py index` over a
     copy of the frozen tree returns the same first 20 entities, in the same
     order, as the experiment's gate tool on the frozen index. The replay never
     uses an index prepared by hand or by the harness. Traceback-shaped queries
     are replayed as recorded; if any fails, the fix is a versioned
     preprocessing step shared by replay, CLI and MCP, or a structured error,
     never a silent rewrite.
  3. **Determinism:** two rebuilds of the same tree give identical `documents`
     digests and identical first-20 lists for the whole query set. `ORDER BY
     2,entity_id` at `retrieval.py:280` already breaks ties; the check verifies
     it and adds no ordering of its own.
  4. **Lifecycle tests on fixtures:** `snapshot.py write` produces
     `retrieval.sqlite` and `--no-index` does not; `carry` on a compatible
     snapshot updates incrementally, on an incompatible one rebuilds; the
     incremental result equals a clean rebuild after insert, update, delete,
     rename, Unicode identifiers and an empty query; `index --check` reports
     `missing`, `stale`, `corrupt` and `fresh` with the stated exit codes; a
     crashed build (lock left behind, half-written file) is repaired by `index`;
     two concurrent writers leave one valid index; `search` on a `missing` or
     `corrupt` index returns the gap and writes nothing; the wire test lists
     `codebase_map_search` as read-only and `codebase_map_index` as writing.
  5. **Context packet non-regression:** one bug request and one change request
     through `snapshot.py context`, index absent then present, recording
     candidates, leads, token count and wall time; the difference is reviewed
     and recorded in the plan, and the index-absent output is byte-identical to
     today's.
  6. **Latency, measured, split and baselined:** median and p95, cold and warm,
     on the Phazly snapshot of the experiment (1,217 documents) and on the
     Daodan repository, hardware stated: full build at `write`, incremental
     refresh at `carry`, one `search` (tree verification included). The
     experiment's 1.24 s per search is the only baseline today; the
     implementation sets no target until these numbers exist.
  7. **End-to-end consumer gate, instrumented:** a small run of the
     `project-delivery` repair cycle on fixture bugs, with the brief of contract
     6, recording per task whether `codebase_map_search` was called, how many
     ranked results were consumed before the first read, outcome, tokens and
     wall time. The gate passes when the tool is used on every task; a task that
     skips it is a defect of the brief, not of the tool.
  8. `python -m unittest discover -s tests`, every linter and
     `python scripts/daodan_build.py --check` pass on all five hosts.

## Verification and limits

- The measured gain holds for Python, a strong agent and precise requests. The
  guide states that perimeter. Vague requests, weak models, large repositories
  and other languages are unmeasured; the index already covers every parsed
  language, since subtokens are language-agnostic.
- `_verify_tree` rehashes the whole tree on every search. On 1,200 documents
  this is inside the 1.24 s measured; a larger tree may need a cached
  verification. Out of scope, recorded here, decided after acceptance 6.
- The reproduce-first step is a prompt obligation on the worker. The repair
  cycle's split (`testing:test-writer` writes the failing test, the stack's
  specialist fixes) is unchanged.
- Expected effort: two waves of micro-tasks; model spend limited to the plan,
  the review cycle and acceptance 7; the replay costs nothing.

## To close during planning, before the first implementation task

1. Where `refresh_index` writes on a frozen snapshot: confirm from
   `retrieval.py:109-122` that only `retrieval.sqlite` and its lock land beside
   the manifest, so the backfill of contract 2 is non-destructive.
2. Whether the 69 frozen task indexes already carry the FTS5 tables at the
   current schema, which decides whether acceptance 2 rebuilds or reuses.
3. Whether `retrieval.search` accepts every recorded traceback query unchanged:
   replay the query set in a REPL before writing any preprocessing.
4. Full build versus incremental refresh for the first release: decided on the
   cost measured in acceptance 6 on 1,217 documents.

## Open decision

Approve this specification to proceed to planning, or amend it. The earlier
open decision (build with every snapshot or on demand) is resolved by the
review: build at `write` and `carry`, queries strictly read-only, explicit
backfill and repair.
