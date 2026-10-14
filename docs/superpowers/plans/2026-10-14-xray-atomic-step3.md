# X-ray atomic method step 3 implementation plan

> **For agentic workers:** Use the approved design and execute in the primary checkout. Independent preflight and final review complement native implementation.

**Goal:** Finish role-local X-ray method reads and freeze their measured costs.

**Architecture:** Keep all canonical units and their rules. Workers load their phase pair and evidence; quality reads skipped Phase 6 and comment instructions conditionally. The mapper consumes evidence and a bound analysis without loading snapshot-owner commands.

**Tech Stack:** Markdown kernels, Python stdlib contract tests, all five host adapters.

**Spec:** `docs/superpowers/specs/2026-10-12-xray-atomic-method-design.md`, step 3.

## Global constraints

- No new registered skill, phase unit or team topology.
- Source reading, static coverage, style cascade and shared-manifest ownership retain their requirements.
- No analyst, flag semantics or publication redesign in this step.
- Core and optional budgets only decrease; measured words are not measured runtime tokens.
- Preserve concurrent report-rendering and instruction changes. Serialize shared rebuild/version/catalog/commit work with their owners.

## Review focus

- Lite quality reads no Phase 6 procedures but retains risk taxonomy currently nested beneath Phase 6.
- Full depth and updates retain Phase 6 procedures and read-only documentation diagnosis.
- Comment commands/classification enter only when Phase 6 runs with comments.
- Optional nested reads remain explicit, deduplicated and bounded by frozen allowances.
- A future router change cannot import unrelated phase or snapshot-owner units into a worker.

## Task 1: Role-local reads and guards

Files: `roles/partition-quality-worker.md`, `roles/semantic-interconnect-mapper.md`, and `tests/test_xray_load_budget.py` under the codebase-xray kernel/tests. Structure and behavior need no runtime change.

- [x] Capture pre-phase bytes and obtain independent role/budget assessments.
- [x] Add core-resource closure and sentinel tests. Observe failures for mapper snapshot-owner load and quality skipped/conditional sections.
- [ ] Add closed `not-lite` and conjunction conditions to the measurement guard; update quality selectors and remove mapper snapshot-owner load.
- [ ] Preserve source-reading rules in evidence.md; replace the redundant quality tool paragraph with its canonical reference and retain partition/Wave 1 leads. Diagnosis and comment command copies remain in their conditionally loaded phase unit.
- [ ] Measure all modes, documentation states and optional combinations. Freeze role caps at the maximum after subtracting unchanged optional allowances; reject any cap increase.
- [ ] Assert optional resource closures, required section witnesses, unknown-condition failure and negative cross-role loads. Run `python -m unittest discover -s tests -p test_xray_load_budget.py`.

## Task 2: Verification and publication

Files: plugin version declarations, generated exports/catalogs/docs, and step3 report. Build only after concurrent source owners release the shared publication boundary.

- [ ] Capture an LF candidate and run X-ray load, skeleton, unit, stylesheet and all-five-host contracts.
- [ ] Obtain an independent final review of the owned diff and fix material findings with regressions.
- [ ] Run the full suite and required repository gates on the exact candidate. Do not substitute the concurrent baseline failures for step3 verification.
- [ ] Coordinate version bumps, rebuild all five hosts, regenerate docs, and include only approved changes in the commit.
- [ ] Publish only within the current session's authorization; record the exact tested candidate and publication result.

## Evidence

Run: `.daodan/xray-atomic/runs/20261014-xray-atomic-step3/`.
Disk exhaustion on D: interrupted one quality-worker write. Its original bytes were recovered from the captured pre-phase file. No foreign source or archival output is purged by this plan. Full verification requires enough free disk space.
