# Realign

When commits land on the base branch, through a finish or a sync, the
knowledge that describes the project follows them, in this order. Run alone
after a merge made outside the cycle, it realigns the current head.

1. **Records.** Load `project-knowledge:adr-method`. A finish runs `promote`
   for its run's proposed record with `merged_sha`, and the helper marks the
   superseded records in the same transaction. A sync promotes the proposed
   record of every agenda task whose branch the incoming range merged, and
   lists to the user the active records whose cited symbols the range
   changed. A range without records says so.
2. **Map.** Load `codebase-map:map-method`; incrementally update the bound run
   at the new head, carrying unaffected claims. Invalidate affected packets;
   retain obligations per `references/context-cycle.md`. Refresh the changed
   scope's concept index through `abstraction-architect`'s skill. Cards become
   stale automatically; rewrite them only when deepening an area.
3. **Documentation.** Run the `project-knowledge:project-knowledge` drift
   audit on the documents that cite the changed paths and symbols, and apply
   the authorized corrections; `project-knowledge:readme-craft` when the
   README cites them.
4. **Instructions.** Run `project-knowledge:instructions-method` to
   regenerate the loop block from the run and the record index: commands,
   active records, workspace convention. Nothing outside the markers changes.
5. **Head.** Record `last_synced` in the run and compare it with `HEAD`: a
   commit that landed meanwhile gets one more map update before the run
   closes.

A step that cannot run, for a missing runner or an unauthorized edit, stays
open with its reason; the run never closes on it silently.
