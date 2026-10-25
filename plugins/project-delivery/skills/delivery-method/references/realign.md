# Realign

After base commits land through finish or sync, realign project knowledge in
this order. Alone, realign the current head after an external merge.

1. **Records.** Load `project-delivery:adr-method`; nothing is promoted
   here. A finish runs `verify` with `merged_sha` on each `Accepted` record
   stage D confirmed the code conforms to; its own record still `Proposed` is
   reported as unapproved. Then `validate --sha HEAD_SHA` lists the `drifted`
   records, reported to the user with their files. A range without records
   says so.
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
   regenerate the loop block from the run and records resolved in step 1:
   commands, records, workspace convention. Nothing outside markers changes.
5. **Head.** Record `last_synced` in the run and compare it with `HEAD`: a
   commit that landed meanwhile gets one more map update before the run
   closes. After all steps succeed, set `integration.realigned: true`.

A step that cannot run, for a missing runner or an unauthorized edit, stays
open with its reason; the run never closes on it silently.
