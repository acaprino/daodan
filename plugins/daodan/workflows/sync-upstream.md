---
description: >
  Bring other people's work into this copy: fetch, report what arrived and whether it touches an open task, fast-forward only, then realign map, records and documentation.
  TRIGGER WHEN: the user wants to pull, update from upstream, or see what others changed.
  DO NOT TRIGGER WHEN: the user wants their own work merged (use finish-task).
---

# Sync with upstream

Load the skills `project-lifecycle:lifecycle-method` and
`work-controller:work-record`.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-lifecycle:lifecycle-method` and follow its
`references/first-use.md` first. Open a run with operation `consolidate` and follow
the lifecycle method's `references/sync.md`. A diverged branch or an uncommitted edit in
the incoming paths stops with the options; the choice is the user's.
