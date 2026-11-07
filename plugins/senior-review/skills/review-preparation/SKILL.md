---
name: review-preparation
description: >
  Prepare the existing code, team or PR review inputs without writing another detection prompt. Load before dispatching reviewers in senior-review.
---

# Review preparation

Branch input: `variant=code-review|team-review|pr-review`, target, flags, output,
optional bound scope/baseline/candidate. Output: snapshot, brief, context,
selection, run and evidence. Light loads only `references/composition.md` here;
its own method prepares inputs.

Use the host run-record mechanism for preflight and confined run records when
available; if absent, declare the missing run record as a delivery gap. Read-only
reviews may use a dirty workspace: capture its complete snapshot and preserve
edits. Review grants no mutation.

A caller-bound candidate is authoritative. Validate its project/worktree, run,
scope and current snapshot through the host run record before deriving review inputs.
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
| Reviewer catalog | `plugin.toml` (`[components].roles`, `[reviewers.compositions]`) read by `scripts/composition.py catalog`, which writes `CATALOG.json`; descriptions shortlist candidates; Phase 1 reads their mandates to choose suitable reviewers |
| Always, after the roster | `references/composition.md`: bind and validate specialist jobs before recording the complete review or dispatching |

Execute preparation once. Team review Phase 1 understands the scoped object
and selects suitable reviewers in the coordinator's context, using the complete
run resolved from runs.json. It finalizes the roster through
`references/composition.md`; Phase 2 dispatches the bound jobs in isolated contexts.

Reports use the explicit review output root; lifecycle runs keep scratch/context
in their run root. Record the same
snapshot and run identity. Return missing evidence as degraded coverage.

Read `references/stack-dimensions.md` to include React, TypeScript and platform
bindings in the same reviewer selection. For team review this is part of Phase 1,
before presenting the plan; for code and PR review it follows scope resolution.
Preparation never dispatches. Record the activation
evidence or skip reason for each dimension, then pass the complete selection to
review-method. A prepared bundle cannot imply that any selected reviewer ran.

Use the skill inventory actually available in the host. Read `references/knowledge-bindings.md`
inside this skill after resolving scope and the native reviewer selection. Prepare
one `knowledge_selection` against the same candidate snapshot and actual available
skill inventory. Add scope/lens assignments and content fingerprints to this brief;
knowledge selection is open to every classified available stack, not a fixed
language list. Return inventory/classification/match gaps and failed selected loads
explicitly. Reuse the exact prepared record until any of its bindings changes.
