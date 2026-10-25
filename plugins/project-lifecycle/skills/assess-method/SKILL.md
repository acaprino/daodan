---
name: assess-method
description: >
  Diagnose project coherence and technical debt through canonical specialist audits and an executable roadmap.
  TRIGGER WHEN: the user asks for project health, a coherence assessment, technical-debt diagnosis or a prioritized maintenance roadmap, including /daodan:check-health and the assessment stage of /daodan:run-maintenance.
  DO NOT TRIGGER WHEN: implementing an approved change, repair or verification cycle (use project-delivery:delivery-method), running a full Senior Maintainer campaign (use maintainer-method), or preparing a consultant dossier (use handover-method).
---

# Project assessment

Load skill `work-controller:work-record` for run ownership, snapshots, authorization,
delivery accounting and result validation. Assessment is read-only for product
and durable project files; only run-owned reports and an explicit Codebase Map
run are permitted outputs.

Read `references/assess.md` before selecting or dispatching auditors. Load
`codebase-map:map-method` and dispatch `codebase-map:map-analyst` in an isolated
context as that unit directs. Keep each specialist's native report, exact candidate and declared gaps. Consolidate an
executable roadmap without turning coherence findings into a correctness
verdict. Implementation, repair, verification and consolidation after the
assessment belong to `project-delivery:delivery-method`.

For native result wrappers and workspace dispositions, read
`references/native-reports.md`. Before closing, the coordinator loads any requested
HTML view through skill `report-rendering:report-renderer` and reads its
`references/project-run-view.md`.
