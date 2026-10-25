---
description: >
  Deepen the project's Codebase Map on an area, or on the whole project: the lite map first when none exists, or the depth chosen at the project's first use, then the cards of the symbols that lack a fresh one.
  TRIGGER WHEN: the user asks to map, analyze or understand the structure of code, or to refresh the map.
  DO NOT TRIGGER WHEN: the user wants a written guide (use write-docs) or a verdict on a change (use review-changes).
argument-hint: "[area]"
---

# Map the code

$ARGUMENTS

Load the skill `codebase-map:map-method`, and `work-controller:work-record` for
the first-use probe.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. As
this command is an analysis, the first use asks the depth and not whether to analyze.
Without a complete analysis of the project, or
when the user asks for a new run, run the analyze entry (`references/entry-analyze.md`) at
lite depth, or at the depth, phases and run name the user asks for; for a large,
multi-language or multi-workspace scope it recommends the team entry
(`references/entry-team-analyze.md`) and the user chooses, unless they named it. With
an analysis, update it incrementally when stale. Then deepen the area above, or the
whole target, as `references/deepen.md` directs.
