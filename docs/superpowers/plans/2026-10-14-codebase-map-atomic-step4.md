# Codebase Map Atomic Step 4 Implementation Plan

> **For agentic workers:** Execute the approved tasks with isolated ownership, meaningful failing tests and a fresh final review. Use the project-protocol ledger to preserve deliveries and completion gates.

**Goal:** Move classic analysis into an isolated owner and make partial runs, recovery and publication mechanically distinguishable.

**Architecture:** The entry confirms scope and update choices, prepares a run and snapshot, dispatches one `map-analyst`, verifies delivery and publishes. The analyst reads phase units and source in one isolated context and writes only its run. `snapshot.py` owns the mode table and delivery gate.

**Tech Stack:** Neutral Markdown/TOML, standard-library Python, five generated host exports.

**Spec:** `docs/superpowers/specs/2026-10-12-xray-atomic-method-design.md`, step 4. The subsequent approved rename replaces `codebase-xray`, `xray-method` and `.codebase-xray/` with `codebase-map`, `map-method` and `.codebase-map/`; legacy aliases and migration remain supported.

## Global Constraints

- Static analysis only; preserve the perimeter, stylesheet rules and three coverage figures.
- No analyzed-source edits, worker questions or worker publication.
- Preserve every phase skeleton and declared team extension.
- Existing budgets and optional allowances never increase. Measure the new analyst separately.
- Questions, requested views, delivery verification and mirror publication belong to the entry.
- One new role, `map-analyst`; no new registered skill or executor.
- Preserve concurrent renderer changes. Serialize shared version, index and publication writes.
- Rebuild all five hosts; host rendering checks are structural evidence, not live execution.
- One step-4 source commit with relevant plugin and marketplace bumps. Step 5 stays separate.

## Review Focus

1. A stopped or empty worker cannot satisfy delivery; skipped and inherited artifacts have distinct validation.
2. Resume cannot change mode, flags, target or confirmed earlier source binding.
3. Partial runs never replace the mirror; a complete lite/classic run removes old full/team files.
4. Nested references cannot move analysis back into a long-lived coordinator.
5. Audit consumes a specific current run and launches no Map under `--diff`.

## Task 1: Mode table and delivery gate

**Owner:** `step4_gate`. **Files:** `snapshot.py`, `test_codebase_map_run_controls.py`.

**Interfaces:** `prepare RUN_DIR`, `check RUN_DIR --json`, `publish RUN_DIR`; `delivery` schema 1 records immutable mode/flags, produced/inherited/skipped artifacts and invocation controls. Check reports missing, empty, unexpected, invalid inheritance, stale/undocumented claims, deferred artifacts, first incomplete phase and publication eligibility.

- [ ] Add tests for full/lite/update/docs-only/single-phase, valid and invalid provenance, stop/resume, empty/unexpected delivery, immutable bindings and mirror replacement. Observe intended failures.
- [ ] Implement the single mode table and guarded run-local preparation. `--phase` and `--stop-after` accept 1..6; explicit resume accepts 1..7, requires an exact run name and drops the invocation's stop.
- [ ] Verify earlier artifacts on resume. Preserve incomplete later update claims and distinguish expected deferred files from delivery gaps.
- [ ] Publish only eligible native delivery through a locked transaction; preserve unrelated roots, registry entries and run histories, and restore captured mirror bytes on failure.
- [ ] Run existing snapshot tests and new controls tests; deliver logs and report.

## Task 2: Thin entry and isolated analyst

**Owner:** `step4_owner`. **Files:** classic entry and sidecar, `map-analyst`, router/run/snapshot/update units, Phase 0 and team publication paragraphs, structural owner tests.

**Interfaces:** Task 1 commands and ledger. Shared `preflight`, required-isolation `analysis` role, shared `publish`. Root owns load-budget and Phase 7 adaptation.

- [ ] Add structural tests that fail on inline reading, absent isolation, worker questions/publication and obsolete flag semantics.
- [ ] Keep scope/update confirmations in entry. Initial snapshot write follows confirmation; carry precedes preparation for updates. The analyst owns subsequent snapshot refresh.
- [ ] Move execution/source reading to the analyst's bounded phase loads. Single-phase analysis derives prerequisites from source without inventing earlier files.
- [ ] Bind stop/resume and expected delivery to the helper. Render and verify requested views in the entry before publishing.
- [ ] Keep team topology unchanged; bind its legitimate extra artifacts to the same gate.
- [ ] Run owner and mode-contract tests, measure coordinator/analyst loads and deliver the report.

## Task 3: Composed consumers and bounded audit

**Owner:** `step4_composition`. **Files:** affected review/lifecycle sidecars and nested invocation paragraphs, abstraction audit acquisition, composition tests.

- [ ] Add failing tests for dispatch declarations, nested isolation and audit run bindings.
- [ ] Declare `codebase-map/map-analyst` wherever a workflow runs classic Map; preserve the required provider and existing workers.
- [ ] Audit selects the newest target-bound run holding 01..04. Verify snapshot freshness; read current runs, update stale ones only through phase 4, and create missing maps only through phase 4.
- [ ] Bind a caller-selected partial or team parent internally for a new classic update; preserve common flags and never inherit team 08 into that child. This is a new run, not a mode-changing resume.
- [ ] Under `--diff`, launch no Map and list changed files outside the diff as gaps.
- [ ] Run composition checks and deliver the report.

## Task 4: Integration, review and publication

**Owner:** coordinator. **Files:** load-budget and host regressions, Phase 7 ownership clause, plugin docs, versions and generated packages.

- [ ] Follow declared phase reads in budget tests; assert coordinator closure excludes phase/source units. Keep prior worker guards and lower entry caps to measured values.
- [ ] Bind Phase 7 completion/views to the entry. Add five-host required isolation and negative-capability regressions.
- [ ] Incorporate the concurrent renderer's published base using only owned source changes. Generate an LF candidate and run repository gates and full suite with a usable fixture environment.
- [ ] Obtain one independent final review and resolve material findings with meaningful tests.
- [ ] Bump every changed plugin, including the skill index provider, and marketplace metadata; regenerate all exports and documentation/instruction parity.
- [ ] Commit only owned changes, push `master`, verify exact-revision CI/release, validate the canonical result and preserve foreign work.

## Deferred to the next step

Tightening each atomic unit is step 5. The approved second classic `humanize` run follows step 4 and must be recorded separately from compiler evidence; it requires the installed-host execution path used by the existing baseline.
