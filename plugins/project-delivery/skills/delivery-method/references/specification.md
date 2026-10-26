# Project specification

Write new specifications in `docs/specs/YYYY-MM-DD-<slug>-design.md`, unless the
user or project explicitly selects another destination. Never add a plugin brand
to the path. Reuse supplied specifications, including historical branded paths;
do not move, overwrite or duplicate them without authorization.

Once the approach is settled, draft the specification without waiting for a
separate writing request. Scale detail to the work: intent, users, success,
scope/non-goals, constraints, chosen and rejected alternatives (`RA-*`), observable
nominal/boundary/rejection examples (`EX-*`), invariants (`INV-*`) and open questions.
Distinguish user decisions, agent assumptions and unresolved choices.

Before planning or scaffolding, review through `senior-review:review-method`,
shape `light`, kind `spec`, stage `record`. Resolve blockers; show the exact document
and SHA-256 for approval through the work record's question rule, also without
ADRs. A prior “do it” is not approval of unseen text. Reuse existing approval of
unchanged bytes; specification approval grants no implementation or commit permission.

In the run's `intent.md`, bind the project-relative path, SHA-256 and approval
question/run identity. Link the recorded answer; never copy the specification.
Carry this binding into the plan and worker briefs. Before planning, execution, resume or closure, verify the bytes and approval. Changes invalidate approval and dependent
plans; reopen only affected decisions. Worktree handoffs must preserve the same
bytes at the bound path without overwriting other work.

ADRs record separate technical decisions and cite the specification. FRDs retain
their evidence-bound requirements; neither replaces this document.
