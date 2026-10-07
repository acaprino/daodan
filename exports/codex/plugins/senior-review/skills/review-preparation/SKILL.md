---
name: review-preparation
description: >
  Prepare the existing code, team or PR review inputs without writing another detection prompt.
---

# Review preparation

Input: `variant=code-review|team-review|pr-review`, target, original entry flags,
output root, optional extension selections. Output: resolved target and snapshot,
native review brief, context files, reviewer selection, run identity and evidence discovery.

Load the `project-protocol:project-protocol` skill for execution preflight and confined run
records. A read-only review may use a dirty workspace: record its complete snapshot
and preserve existing edits. Do not create a mutation authorization by reviewing.
Read `references/<variant>.md` inside this skill and execute its preparation stages
once. Existing reviewer inputs remain unchanged. For team review, X-ray analyze is
executed in the coordinator context as documented in Phase 1a, not spawned as a role;
resolve the exact run in runs.json and never substitute a mirror for a missing run.

Native report locations in the reference are relative to the explicit review
output root. When lifecycle supplies a run root, put scratch/context there instead
of creating a second root run. Record the same project snapshot and run identity.
Return missing input/worker evidence as degraded coverage; do not invent findings.
