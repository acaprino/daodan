# Project Knowledge

Project Knowledge owns durable instructions, project guides, technical document
maintenance and README work. It updates existing authoritative documents before
creating parallel copies, distinguishes implemented behavior from approved
intent, and records execution state outside durable instructions.

## Entry points

| Workflow | Purpose | Default |
|---|---|---|
| `/project-knowledge:instructions` | Audit host/project instructions; create or maintain the authoritative destination | Audit-only |
| `/project-knowledge:guide` | Prepare an audience/file plan and write the needed project guide | Plan before writing |
| `/project-knowledge:maintain` | Check generic and twenty-dimension documentation drift | Audit-only |
| `/project-knowledge:readme` | Check or author README while preserving facts and author voice | Audit-only |

Use `--create` for a new instruction file or README, `--audit-only` for read-only
diagnosis, `--plan-only` where supported, `--fix` for authorized changes and
`--commit` when commits are authorized. A caller's existing run and authorization
are reused. Reports belong to the owned `.daodan/runs/<id>/`; application changes
only the files in the authorized plan.

## Reusable methods and roles

The `project-knowledge` skill contains preparation, twenty-dimension drift audit,
guide and application methods, audience adaptation and diagram techniques.
`instructions-method` selects scoped authoritative instruction destinations and
holds working principles, condensed test rules and an instruction example.
`readme-craft` holds README preparation, audit and application techniques.

`instructions-auditor`, `documentation-engineer` and `guide-reviewer` accept
explicit audit-only mode. They return evidence, provenance, scope and unavailable
checks rather than automatically editing their findings. The context explorer
prepares an identified run. Overview, technical, flow, onboarding and operational
writers receive exact owned files and readers. The operational writer owns both
reference and configuration how-to, sharing one verified input set.

Document structure editing belongs to `doc-humanizer`; voice editing belongs to
the independently useful [text-humanizer](text-humanizer.md). A guide is not a
mandatory numbered package, and no minimum document, line or open-question count
is required. A missing or failed worker remains an explicit delivery failure.

## Dependencies and evidence

Required local dependencies are `project-protocol`, `codebase-xray`,
`senior-review` and `text-humanizer`. Dispatch and concurrency use host mechanisms
from the adapters; no team-only plugin is required merely to write a guide.

X-ray remains static. Its exact run, target and snapshot are bound before reuse;
an older mirror is not proof of current implementation. Claims preserve status
and premise provenance. A wrong document, a wrong implementation and unresolved
product intent remain different findings.

Successful application requires relevant source/link checks, current inputs and
accounted deliveries. Generated documents remain under their generator's
ownership. Commands copied from manifests are labelled unexercised unless an
allowed project verification actually ran.

**Related:** [codebase-xray](codebase-xray.md), [senior-review](senior-review.md),
[testing](testing.md), [text-humanizer](text-humanizer.md).
