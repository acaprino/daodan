---
name: review-preparation
description: >
  Prepare the existing code, team or PR review inputs without writing another detection prompt.
---

# Review preparation

Input: `variant=code-review|team-review|pr-review`, target, original entry flags,
output root; optionally the caller's resolved scope, baseline and candidate
bindings. Output: resolved target and snapshot,
native review brief, context files, reviewer selection, run identity and evidence discovery.

Load the `project-protocol:project-protocol` skill for execution preflight and confined run
records. A read-only review may use a dirty workspace: record its complete snapshot
and preserve existing edits. Do not create a mutation authorization by reviewing.

A caller-bound candidate is authoritative. Validate its project/worktree, run,
scope and current snapshot through project-protocol before deriving review inputs.
Use its captured baseline and exact candidate content, including scoped untracked
files and their full contents. Exclude the run's output root. Never replace that
target with a branch comparison or the previous commit. Missing baseline content
is a declared comparison gap, not permission to invent a before-state; preserve
the actual candidate and leave any gate needing that comparison unavailable.

Read `references/<variant>.md` inside this skill and execute its preparation stages
once. Existing reviewer inputs remain unchanged. For team review, X-ray analyze is
executed in the coordinator context as documented in Phase 1a, not spawned as a role;
resolve the exact run in runs.json and never substitute a mirror for a missing run.

Native report locations in the reference are relative to the explicit review
output root. When lifecycle supplies a run root, put scratch/context there instead
of creating a second root run. Record the same project snapshot and run identity.
Return missing input/worker evidence as degraded coverage; do not invent findings.

Read `references/stack-dimensions.md` to include React, TypeScript and platform
bindings in the same reviewer selection. For team review this is part of Phase 0b,
before presenting the plan; for code and PR review it follows scope resolution.
Preparation selects reviewers without dispatching them. Record the activation
evidence or skip reason for each dimension, then pass the complete selection to
review-method. A prepared bundle cannot imply that any selected reviewer ran.
