---
name: project-knowledge
description: >
  Prepare, audit and maintain durable project documentation with a file/audience plan. Load when writing guides, reconciling document drift or coordinating knowledge work.
---

# Project knowledge method

## Common contract

Load `project-protocol:project-protocol` for operational records and gates.
Receive or initialize an owned run before dispatch. A caller's existing run is
reused; do not create a competing run or choose an unrelated latest report.
Inputs: project/worktree identity, target scope, snapshot, task intent, existing
documents, evidence paths, audiences, authorized mode, budget and output root.
Modes: audit-only/dry-run, plan-only, fix and commit. Audit-only may write only
the owned run report, never project source or durable knowledge. A requested
missing path is an explicit gap; no automatic broadening of scope.

Operational records remain in the run. Durable documents describe verified
implementation or attributed approved intent, with unknowns labelled. They do
not accumulate progress, branch names, one-run measurements or session status.

Read `references/preparation.md` before dispatch and
`references/documentation-audit.md` for the twenty drift dimensions. For guide
writing read `references/guide-method.md`; for authorized changes read
`references/apply-method.md`. Writer briefs also load
`references/writing-guidelines.md`, `references/audience-adaptation.md` and
`references/diagram-patterns.md` according to the task.

## Reusable dispatch

- Discovery: `codebase-explorer`, with the exact scope and owned context output.
- Documentation drift: `documentation-engineer`, explicitly audit-only until
  application is authorized.
- Cross-document evidence review: `guide-reviewer`, explicitly audit-only.
- Structured writing: overview-writer, tech-writer, flow-writer,
  onboarding-writer and ops-writer, only for their assigned files.
- Existing document structure: doc-humanizer. It changes form, not facts.
- Instruction claims: load `instructions-method` and dispatch instructions-auditor.
- README: load `readme-craft` and execute its audit/apply method in context.

No detector prompt is repeated in this entry method. Every writer receives a
file/audience plan and cannot invent additional files to satisfy a template.
Dispatch and delivery barriers use the host harness. Do not spawn a fixed number
of writers or require a team-only API.

## Result

Preserve native findings and locators. Record changes by owned file, retained or
migrated information, unresolved intent, stale inputs, checks run and checks not
available. A missing reviewer or changed snapshot blocks successful completion.
Validate and close the operational result with the project-protocol method.
