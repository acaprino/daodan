# Deepen an area

A card is the map's reading of one symbol: purpose, preconditions,
postconditions, invariants, side effects, failure modes. Cards outlive every
run in the analysis root's `cards.sqlite`, carry the digests of the symbol
they were written against, and are judged `fresh` or stale whenever a
snapshot is queried. So the map deepens where work happens and only for what
changed: a card still fresh is never written again.

## Coordinator

1. Bind the latest complete run and verify the area against the current tree
   with `snapshot.py diff --verify`; stale paths go through the incremental
   update first. With no analysis, write a base snapshot of the target before
   anything else; a full analysis is never the default.
2. Resolve the area. A task's area is the symbols it names and their one-hop
   callers and callees from `snapshot.py edit-impact`; an area given as a path
   is every symbol under it; no area is the whole target.
3. List the symbols without a fresh card: `snapshot.py meta-query MANIFEST
   --path AREA --no-history`, keeping `uncovered` and every stale state.
   Nothing listed: the area is deep already, and nothing is dispatched.
4. Dispatch `codebase-map:map-analyst` with mode `cards`, the manifest, the
   list and an expected delivery, in batches of at most 100 symbols.
5. Verify with the same query that every listed symbol is `fresh` or carries
   the analyst's reason.

## Analyst in cards mode

For each listed symbol read its verified source and its neighbours through
`snapshot.py edit-impact MANIFEST --target SYMBOL`; a stale card is a lead,
never the answer. Write one card per symbol:

- `purpose`: one or two sentences on what it is for.
- `preconditions`, `postconditions`, `invariants`: what callers must hold and
  what it guarantees, each from the source.
- `side_effects`: writes, I/O, network, global state, time.
- `failure_modes`: what it raises or returns on failure, and what it leaves
  behind.
- `confidence`: `high` when read in full with its callers, `medium` when a
  neighbour was unresolved, `low` otherwise; `notes` for anything unverified.

Write the batch with `snapshot.py meta-upsert MANIFEST --input -`, the cards
as JSON on standard input, and deliver the command's result: cards written,
symbols the snapshot lacks, cards refused with their reason. The card store is
this mode's only write; analyzed source and finished runs stay untouched.
