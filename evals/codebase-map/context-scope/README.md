# Context and scope holdout

Machine-only harness that measures how much of the source a task needs each way of
preparing context delivers inside the same character budget, on a project that
was never used for tuning. It measures localization and context delivery. It does
not measure task success, correctness of the delivered code or LLM token savings.

## Protocol

- **Corpus.** Starlette 1.9.0 (BSD-3-Clause), 37 files of the `starlette` package,
  about 263 000 characters of source. File hashes are in `gold/corpus-sha256.json`.
  Reproduce it with `pip download starlette==1.9.0 --no-deps` and compare the hashes;
  the corpus is not vendored here.
- **Queries and gold.** `gold/queries.json` holds 24 queries, 12 English and 12
  Italian, split across behavior, symptom, decision and exact-name questions. One
  model wrote queries and gold blind to the retrieval code; a second pass read every
  gold body independently (`gold/queries-verification.json`: 23 confirmed, 1 amended,
  0 dropped). Italian queries and queries without code names are not derived from
  the identifiers of their gold.
- **Frozen.** `evaluate.py prepare` copies the package, stores the query and source
  hashes in `.evaluation/frozen.json`, and builds the snapshot, the retrieval index
  and the Jedi edges once. `evaluate.py evaluate` refuses to run if a hash changed.
  Nothing was tuned on these queries (`tuning: false`).
- **Arms at equal budget** (6 000, 12 000 and 24 000 characters):
  `text` (lexical retrieval filled in rank order), `text+graph` (the top three hits,
  their callers and callees from the Jedi edges, then the rest) and `scope+packet`
  (the scope planner followed by the context packet builder, with a recipient
  budget). Coverage is the share of each gold entity's lines that the arm delivers:
  `full_gold` counts entities delivered whole, `partial_gold` the mean fraction.
  A packet that refuses (`needs_split`, nothing delivered) scores zero and is also
  counted separately, so abstention is visible.
- **Full context** is 263 129 characters, larger than every budget, so it is not a
  baseline that fits and no arm is credited with beating it.
- **Impact scenarios** (`impact.py`) mutate copies of the project: a signature
  change, a body change, a removal and a change to a heavily used function, three
  targets each. The oracle is a regular-expression search for call sites in the
  mutated copy, independent of the map. Names that collide with builtin container
  methods are not eligible, because a textual oracle cannot tell them apart.
- **Path run** (`pathrun.py`) drives one real lifecycle path through the public
  command line interfaces on a copy: natural request, indexes, preflight, task
  packet, resume, a real edit checked by a behavior oracle, protocol barrier,
  refreshed map in a new manifest, post-task receipt, semantic map, and a check that
  the old receipt is refused. A script plays the coordinator and the editor.
- **Embedding arm** (`embedding_arm.py`) compares lexical, dense, fused and fused-plus-graph
  orderings on the same queries with the shipped fusion policy, and can run the planner and
  the packet builder with the dense result as lead source. The pinned model must already be
  in the plugin's shared model directory; the harness never downloads it. Use the Python of
  the evaluation environment for the project (its parser fingerprint must match the
  prepared manifest) and pass `--encoder-python` for an interpreter that has numpy,
  onnxruntime and tokenizers.
- **Static hosts** (`static_hosts.py`) compares the code context surface of the five
  exported packages with the kernel and checks the four exported schemas.

## Commands

```text
CODEBASE_MAP_SCRIPTS=<kernel>/plugins/codebase-map/skills/map-method/scripts
python harness/evaluate.py prepare  --project P --source <starlette dir> --queries gold/queries.json --environment <venv with jedi>
python harness/evaluate.py evaluate --project P --shard K/N --out part-K.json     (N independent processes)
python harness/evaluate.py merge    --parts part-*.json --out results/evaluate-result.json
python harness/impact.py   --project P --workdir NEW --environment <venv> --out results/impact-result.json
python harness/pathrun.py  --source <starlette dir> --work NEW --environment <venv> --out results/pathrun-result.json
python harness/embedding_arm.py --project P --out results/embedding-arm.json --cold-index --encoder-python <python with numpy, onnxruntime, tokenizers>
python harness/embedding_arm.py --project P --out part-K.json --reuse-index --packets 24000 --shard K/4 --encoder-python <same>
python harness/static_hosts.py <repository root> results/static-hosts.json
```

The scripts use the standard library plus the plugin's own scripts. `prepare`,
`impact.py` and `pathrun.py` need Jedi in the environment passed as `--environment`.
Run `pathrun.py` outside any Git repository: the protocol records the enclosing
repository's head in the run identity, so a commit made meanwhile changes it.

## Results and limits

See `RESULTS.md`. One public library, gold written by models and checked by a second
pass, no human adjudication, characters instead of tokens, no installed-host runtime
probe, and an embedding arm on one corpus with a community export of the model.
