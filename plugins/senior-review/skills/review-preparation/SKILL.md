---
name: review-preparation
description: >
  Prepare the existing code, team or PR review inputs without writing another detection prompt. Load before dispatching reviewers in senior-review or project-lifecycle.
---

# Review preparation

Branch input: `variant=code-review|team-review|pr-review`, target, flags, output,
optional bound scope/baseline/candidate. Output: snapshot, brief, context,
selection, run and evidence. Light loads only `references/composition.md` here;
its own method prepares inputs.

Load `work-controller:work-record` for preflight and confined run records. Read-only reviews may use a dirty workspace: capture its complete snapshot and
preserve edits. Review grants no mutation.

A caller-bound candidate is authoritative. Validate its project/worktree, run,
scope and current snapshot through work-controller before deriving review inputs.
Use its captured baseline and exact candidate content, including scoped untracked
files and their full contents. Exclude the run's output root. Never replace that
target with a branch comparison or the previous commit. Missing baseline content
is a declared comparison gap, not permission to invent a before-state; preserve
the actual candidate and leave any gate needing that comparison unavailable.

## Load map

| Step | Read inside this skill |
|---|---|
| Always, before the variant | `references/candidate-grounding.md`: target kind/basis, governing snapshot policy, ground-truth gate, evidence pack, budget and roster by kind |
| Then | `references/<variant>.md` |
| Reviewer selection | `references/stack-dimensions.md`, then `references/knowledge-bindings.md` |
| Reviewer catalog | `references/reviewer-catalog.json` (compiled): reviewer identities, triggers, prerequisites, host bindings. Never scan role kernels at runtime |
| Always, after the roster | `references/composition.md`: bind and validate specialist jobs before recording the complete review or dispatching |

Execute preparation once under the computed roster and support requirements.
For team review Phase 1a, when selected, the
coordinator executes the `codebase-map:map-method` analyze entry's preflight,
answerable checkpoints, delivery check and publication decision, dispatching
`codebase-map:map-analyst` in one isolated context through the consuming
workflow's declared host harness. Loading either body alone executes nothing;
the analyst is a role, while analyze remains the entry. This step introduces no
second review preparation or final report owner. Required workers retain
isolated contexts. Resolve the exact run in runs.json and never
substitute a mirror for a missing run.

Reports use the explicit review output root; lifecycle runs keep scratch/context
in their run root. Record the same
snapshot and run identity. Return missing evidence as degraded coverage.

Read `references/stack-dimensions.md` to include React, TypeScript and platform
bindings in the same reviewer selection. For team review this is part of Phase 0b,
before presenting the plan; for code and PR review it follows scope resolution.
Preparation never dispatches. Record the activation
evidence or skip reason for each dimension, then pass the complete selection to
review-method. A prepared bundle cannot imply that any selected reviewer ran.

Load the `skill-catalog:skill-catalog` skill. Read `references/knowledge-bindings.md`
inside this skill after resolving scope and the native reviewer selection. Prepare
one `knowledge_selection` against the same candidate snapshot and actual available
skill inventory. Add scope/lens assignments and content fingerprints to this brief;
knowledge selection is open to every classified available stack, not a fixed
language list. Return inventory/classification/match gaps and failed selected loads
explicitly. Reuse the exact prepared record until any of its bindings changes.
