# Context and scope holdout: results

Run of 2026-10-24 on Starlette 1.9.0 (37 files, 669 retrieval documents, 263 129
characters of source), 24 frozen queries, `tuning: false`. Scripts: kernel of marketplace
39.0.2 with the context adapter (the path run used the 39.0.3 candidate). Protocol and limits are in `README.md`. Coverage is the
share of each gold entity's lines delivered; it is not task success, and sizes are
characters, not tokens.

## Redesign, phases 1 and 2 (2026-10-25)

Contract: [context packet redesign](../../../docs/superpowers/specs/2026-10-25-context-packet-redesign.md).
Same 24 queries, used now as a paired before/after regression (the gold was consumed while
the defects were diagnosed; the second holdout is frozen for phase 4). The source reader
changed, so the corpus was re-prepared into a fresh manifest with identical source and query
hashes. Results: `evaluate-redesign-natural.json`, `evaluate-redesign-anchor-top1.json`,
`claims-redesign-*.json`, `pathrun-redesign-result.json`.

Mean share of gold entities delivered whole. "Dispatchable" counts a packet only when it is
`ready`; refusals, errors and `incomplete` packets count as zero on all 24 queries.

| Budget (chars) | text | before: packet | packet, natural query | packet with one accepted anchor, dispatchable |
|---:|---:|---:|---:|---:|
| 6 000 | 0.312 | 0.000 | 0.208 (0.188 at the checkpoint) | 0.125, 4 ready (0.167, 6 ready) |
| 12 000 | 0.469 | 0.000 | 0.375 (0.333) | 0.333, 24 ready (0.292) |
| 24 000 | 0.521 | 0.000 | 0.458 (0.438) | 0.438, 24 ready (0.417) |

The checkpoint is commit "Separate the mandatory context core from retrieval leads"; the
final column values add the one permitted format change: raw, unescaped source sections after
a JSON header instead of source inside a JSON string. It raised five cells and lowered the
anchored 6 000 cell, where per-section headers made four core packets too large instead of
six.

- Natural queries stay `incomplete` (`not_localized`) and deliver leads, as the contract
  says; one query with an exact traceback is `ready`. At 24 000 characters English queries
  match text (0.583 and 0.583), Italian ones trail (0.333 against 0.458).
- The anchor is the first lexical hit, often wrong, so dispatchable coverage measures packing
  around an anchor, not localization.
- Raw source is 57%, 74% and 83% of the input at the three budgets (48%, 66% and 75% at the
  checkpoint); the rest is the JSON header of about 2 000 characters and section lines. Text retrieval spends every character on
  raw source and carries no paths, line numbers, hashes or obligations.
- Claims (`gold/claims.json`, 19 claims over q05, q11, q12, q14): text supports 2, 4 and 4;
  the packet 4, 2 and 4 on natural queries and 2, 2 and 2 with the anchor. Neither finds the
  evidence for q05 or q11: that is a retrieval limit, not a packing one.
- False `ready`: none by contract and tests (a `ready` packet always holds its mandatory
  core); a `ready` packet built on a wrong anchor still supports few claims.
- Time per query: 8 to 10 seconds (planning about 3.5, packet 4 to 6), against about 95
  seconds per packet before.
- Real path with the corrected oracle (a semicolon in `path` or `domain` injected cookie
  attributes): preflight `incomplete` with leads, task packet `ready` with the target,
  post-task `ready` listing all 112 obligations, oracle failing before the edit and passing
  after, identical resume, old receipt refused after the refresh.

**Gate after phase 2: not met.** At no budget does the packet deliver as much as text
retrieval (6 to 10 points short on natural queries), and it supports no more claims. As
agreed before the measurement, the redesign stops here: phases 3 (sidecars) and 4 (second
holdout) are not started, the click holdout stays unread, and the verified improvement is
kept. Packets now deliver, refuse with a reason, keep every obligation and take seconds;
they do not yet save characters against plain text.

Where the characters went, found and fixed in phase 2: the projection gap listed every
omitted entity (about 7 100 characters), each lead carried its full entity record, every
line carried its number, every lead carried its file context, a nested function made the
reader return the whole file (10 of 34 files), and a post-task packet carried 110 impact
obligations with full provenance (154 000 characters, now 23 900).

## Registered protocol: natural-language request, equal budget

Mean share of gold entities delivered whole (partial coverage was identical, because the
arms deliver whole bodies):

| Budget (chars) | text | text+graph | scope+packet |
|---:|---:|---:|---:|
| 6 000 | 0.312 | 0.354 | 0.000 |
| 12 000 | 0.469 | 0.438 | 0.000 |
| 24 000 | 0.521 | 0.556 | 0.000 |

- English queries (12) / Italian queries (12) at 24 000: text 0.583 / 0.458, text+graph
  0.694 / 0.417.
- By query type at 24 000 (text / text+graph): exact-name 0.88 / 0.88, decision 0.88 /
  0.88, symptom 0.44 / 0.56, behavior 0.25 / 0.23. At 6 000 the behavior queries deliver
  nothing.
- Lexical retrieval alone: recall at 5, 10 and 20 hits is 0.188, 0.208, 0.312 over 48 gold
  entities (18 multi-entity queries). 56% of gold entities are not in the top 60 hits.
  12 of 24 queries have a gold entity in the top 20.
- **scope+packet refused all 72 attempts** (24 queries, 3 budgets): the plan stayed
  `incomplete` and was localized once (1 of 24), with 68 to 669 analysis entities
  (mean 386 of 669). The packet builder returned `needs_split` with no input every time. It
  did not deliver wrong context; it delivered none.
- Latency per query: text 2.0 s, text+graph 2.5 s, scope 4 s plus about 95 s to build
  one packet.
- The full 263 129 characters exceed every budget, so no arm is credited against full
  context.
- Embedding arm: measured after the registered protocol, once the owner authorized the model
  download (see the section "Embedding arm" below).

## Exploratory, post hoc (not the registered protocol)

1. **One accepted anchor** (`evaluate-anchor-top1-exploratory.json`: the first lexical
   hit; `evaluate-anchor-gold1-exploratory.json`: the first gold entity). The plan is
   localized in 24 of 24 queries, still with a mean of 386 analysis entities, and all 72
   attempts per mode again return `needs_split`.
2. **Narrowed boundary plus anchor** (`boundary-probe-exploratory.json`): read boundary
   limited to the files of the gold entities and the first gold entity as anchor. This
   hands the pipeline the answer's location, so it is an upper bound for "the interview
   already knows the area". Packets by budget:

   | Budget (chars) | ready | needs_split | mean gold delivered whole (all 24) | mean packet size when ready |
   |---:|---:|---:|---:|---:|
   | 24 000 | 0 | 24 | 0.000 | none |
   | 48 000 | 16 | 8 | 0.528 | 44 271 |
   | 96 000 | 23 | 1 | 0.792 | 63 809 |
   | 192 000 | 23 | 1 | 0.792 | 65 095 |

   With the same information, plain text retrieval restricted to those files with the
   first gold entity first delivers 0.844 of gold whole at 24 000 characters and at every
   larger budget. The pipeline does not beat that on coverage and spends roughly two to three
   times the characters. Whatever it adds (obligations, impact, freshness, gaps) is not measured
   by coverage and is not measured here.
3. **Why the packets refuse.** In a minimal ready packet of 44 319 characters, the
   resolver profile is 22 014, impact evidence 12 778, obligations 4 745, and the
   source the task needs 2 660. The smallest mandatory core therefore needs 32 457
   characters, and a recipient limit under that returns `needs_split` for a single small
   function. In addition, `scope_planner._candidate` turns every discovered candidate,
   retrieval leads included, into an analysis row that requires source, and the packet
   builder makes the current source of every such row mandatory. A wide plan therefore
   asks for most of the project.
4. Plain text at larger budgets, unrestricted (`text-high-budgets-exploratory.json`):
   0.521 at 24 000, 0.635 at 48 000, 0.698 at 96 000 and at 192 000.

## Embedding arm (`embedding-arm.json`, `embedding-packets-24000.json`)

The owner authorized the model download on 2026-10-24, after the registered run. The pinned
community INT8 ONNX export of CodeRankEmbed (138 619 279 bytes, digests checked against the
constants in `embedding_worker.py`) was fetched once into the plugin's shared model
directory. The fusion policy is the one the plugin ships (reciprocal rank fusion, 0.75 dense
and 0.25 lexical, k 60); nothing was tuned on these queries. The lexical column reproduces
the registered text arm exactly (0.312, 0.469, 0.521), which checks that both runs used the
same index, queries and delivery rule.

Mean share of gold entities delivered whole, same budgets and same whole-body delivery rule:

| Budget (chars) | lexical | dense only | fused (shipped) | fused + Jedi graph |
|---:|---:|---:|---:|---:|
| 6 000 | 0.312 | 0.441 | 0.469 | 0.510 |
| 12 000 | 0.469 | 0.580 | 0.545 | 0.545 |
| 24 000 | 0.521 | 0.663 | **0.736** | 0.681 |

- Paired per query, fused against lexical: 7 wins, 1 loss, 16 ties at 6 000; 7, 3 and 14 at
  12 000; 9, 2 and 13 at 24 000. Mean differences +0.156, +0.076 and +0.215. Twenty-four
  queries from one library give a direction, not a significance test.
- By language at 24 000 (lexical / fused): English 0.58 / 0.82, Italian 0.46 / 0.65. By
  type: exact-name 0.88 / 1.00, symptom 0.44 / 0.67, behavior 0.25 / 0.67, **decision 0.88 /
  0.75**. Dense alone is worse than lexical on decision queries (0.50) and better on
  behavior ones (0.64).
- Recall over the 48 gold entities at 5, 10, 20 and 60 hits: lexical 0.188, 0.208, 0.312,
  0.438; dense 0.292, 0.396, 0.458, 0.667; fused 0.312, 0.396, 0.500, 0.729. Gold entities
  outside the first 60 hits: 56% lexical, 33% dense, 27% fused.
- Cost, cold, on CPU (4 intra-op threads, one input per pass): index build 126.5 s for 669
  entities, 2.95 MB on disk, encoder working set about 410 MB (sampled every 0.25 s, so an
  approximation of the peak). Per query: lexical 1.25 s, dense 4.15 s (query encoding plus
  pure Python scoring of 669 vectors), fused call 1.42 s on top.
- **The composition does not improve.** With the dense result as lead source, the planner and
  packet builder at 24 000 characters returned `needs_split` for 24 of 24 queries. The plan
  stayed `incomplete` in all of them and was localized once; the mean analysis scope grew to
  589 entities (512 to 669) from 386, because the dense ranking is complete and every lead
  becomes a source-requiring row. Gold was inside the scope in every query only because the
  scope covered nearly everything. Better retrieval does not help while leads are mandatory.
- Limits: the export is a community conversion, not the vendor's artifact; one corpus; the
  dense rank list was cut at 500 for the leads and at 60 for recall; nothing here measures
  task success or tokens.

## Impact scenarios (oracle: regular-expression call sites in the mutated copy)

Twelve targets were chosen, three per kind; two (a body change and a hub change) could
not be mutated into valid source and were skipped, so 10 ran, with 28 call sites in the
oracle. Every site the map reported was a true site (precision 1.00 wherever anything was
reported). Recall by call site:

| Kind | Oracle sites | Lexical edges only | With Jedi edges |
|---|---:|---:|---:|
| Signature change (3 targets) | 5 | 4 | 5 |
| Body change (2) | 3 | 2 | 3 |
| Heavily used function (2) | 15 | 0 | 15 |
| Removal (3) | 5 | 2 (see note) | 2 |

- Removal was scored against the base map with its Jedi edges in both columns, because the
  removed symbol no longer exists in the candidate.
- Jedi edges: 25 of 28 sites (0.89). Lexical edges alone: 6 of 23 for the three
  non-removal kinds.
- The three missed removal sites belong to `FileResponse._open_file`, a method decorated
  with `@asynccontextmanager`. Jedi resolves the decorated name into a stub outside the
  project, the resolver reports `no-project-targets`, and the impact packet shows no
  callers and no gap. A probe with `@contextmanager` and `@asynccontextmanager` on a toy
  class reproduces it. This is silent: nothing in the packet says the callers are unknown.
- `stale-callers` flagged the changed symbol in all 10 runs.

## One real lifecycle path (`pathrun-result.json`)

A script played coordinator and editor on a copy, through the public command lines only:
index, edges, protocol record, preflight, task packet, resume, verify, a real edit checked
by a behavior oracle, protocol barrier, refreshed manifest with its own index and edges,
post-task, semantic map, and a check of the old receipt.

- Every command exited 0; resume returned the identical receipt (same path, same digest);
  the receipt from before the edit was refused after the refresh (exit 1); the oracle
  failed before the edit and passed after; cards stayed 40 unread in the semantic map.
- All three packets (preflight, task packet, post-task) were `needs_split`: no source was
  delivered, `R1` stayed `support_status: missing`, and the impact obligations stayed
  open. The path therefore proves the receipts, binding, resume and staleness mechanics,
  not that a packet reached a worker.
- The first run of this path failed at post-task because the retrieval index of the old
  manifest was reused after the refresh (`retrieval index belongs to a different
  candidate`), and a second run timed out at the adapter's fixed 120 seconds under load.
  The first is the documented behavior and is now stated in the usage guide; the second is fixed in the adapter (the provider may run for the
  request's `max_seconds`, at least 120).
- The edit is synthetic. Starlette already refuses those cookie names with
  `http.cookies.CookieError`; the guard changes the exception type to `ValueError`. No LLM
  worker was dispatched.

## Static host check (`static-hosts.json`)

For each of the five host packages, 12 files of the context surface (the exported
contract, the references, the three scripts, the lifecycle adapter and the consumer
references) are byte-identical to the kernel or carry the kernel text after the host
binding, with the documented placeholder adaptation only. The four exported schemas
(`context-request`, `scope-plan`, `context-packet`, `map-slice`) are identical in all five
exports. This is structural evidence. No installed host ran any of it.

## Not measured

Task success, LLM token use and cost (no billing data, no tokenizer), memory use, timeouts
under a hard host limit, the embedding arm on a second corpus or language, a second language, a project larger
than 669 entities, any installed-host execution, and the value of obligations and
impact evidence that coverage does not count.
