# Deepen an area

Cards record a symbol's purpose, contracts, effects and failures in the analysis
root's `cards.sqlite`. Stored digests determine freshness against each snapshot.
Deepen only the requested area; reuse complete fresh cards. `semantic-map.md`
projects this evidence, exposing unread, stale and incomplete cards for this method.

## Coordinator

1. Bind the latest complete run; verify the area with `snapshot.py diff --verify`.
   Update stale paths incrementally first. Without analysis, create the target's
   base snapshot; never default to full analysis.
2. Resolve the area. A task's area is the symbols it names and their one-hop
   callers and callees from `snapshot.py edit-impact`; an area given as a path
   is every symbol under it; no area is the whole target.
3. Run `semantic_map.py MANIFEST --path AREA`. Read its JSON `reading_requests`,
   including incomplete fresh cards. Nothing listed: dispatch nothing.
4. Dispatch `codebase-map:map-analyst` with mode `cards`, the manifest, the
   list and an expected delivery, in batches of at most 100 symbols.
5. Regenerate the view. Verify every listed symbol has a fresh, complete card
   or the analyst's reason for remaining gaps.
6. Keep the view's provenance beside it; preserve finished phase reports.

## Analyst in cards mode

For each listed symbol read its verified source and its neighbours through
`snapshot.py edit-impact MANIFEST --target SYMBOL`; a stale card is a lead,
never the answer. Reuse a fresh card's fields and fill its gaps; submit the complete
merged card because upsert replaces its payload. Write one card per symbol:

- `purpose`: one or two sentences on what it is for.
- `preconditions`, `postconditions`, `invariants`: what callers must hold and
  what it guarantees, each from the source.
- `side_effects`: writes, I/O, network, global state, time.
- `failure_modes`: what it raises or returns on failure, and what it leaves
  behind.
- `confidence`: `high` when read in full with its callers, `medium` when a
  neighbour was unresolved, `low` otherwise; `notes` for anything unverified.

Write JSON batches through `snapshot.py meta-upsert MANIFEST --input -`.
Deliver cards written, absent symbols and refused cards with reasons, plus
observed LLM tokens or `unavailable`; never estimate them as measured.
Only the card store is writable in cards mode; source and finished runs stay untouched.
