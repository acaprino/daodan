# Test-suite audit history

Newest audit first. Each section is produced by the audit mode of
`testing:test-remediation-method`. Metrics guide investigation; they do not
establish behavioral value or correctness.

## Audit 2026-10-27

**Scope:** whole suite under `tests/`, runner stdlib `unittest`
(`python -m unittest discover -s tests`), plus `tests/opencode/loader.test.mjs` through
`test_opencode_loader.py`.
**Snapshots:** static audit and full run at `51589ac2d` plus the live tree mid-merge
(run started 10:39). Failures reclassified at the published merge `3a69736d8`.
**Execution:** one full timed run (Windows 11, Python 3.13.14, single process), one clean
rerun of every failing module at `51589ac2d`, three identical reruns of the remaining
failures at `3a69736d8`. CI lane (Ubuntu, Python 3.12, PyYAML only) not emulated.
**Run record:** `.daodan/runs/init-987e333f366346228e566bb9920a851c/`
(`findings.md` holds the full auditor report, 21 findings).

| Metric | Value | Delta |
|---|---|---|
| Test files | 146 audited (147 at `3a69736d8`; `test_project_specifications.py` added by the merge, not audited) | first audit |
| Test cases | 2742 test methods static; 2688 collected by the run (setUpClass errors drop whole classes) | first audit |
| Total runtime | 2204.9 s (36.7 min), single process, Windows | first audit |
| Skipped/disabled | 16 fired locally (10 are the whole `test_codebase_map_mcp_wire.py` class); 84 conditional skip sites in 33 files; 0 unconditional skips or expected failures | first audit |
| Failing | Full run: 82 (11 failures, 71 errors). At clean `3a69736d8`: 4 tests (10 failing subtests, 1 error), all deterministic | first audit |
| Flaky (rerun disagreement) | 0 (three identical reruns) | first audit |
| Orphan test files | 0 (retired-name references are absence guards) | first audit |
| Layer distribution (unit/integration/e2e) | undeclared: flat `tests/`, no markers; layer stated, when at all, in module docstrings | first audit |
| Top-10 slowest | `test_skill_catalog` Kotlin selection 132.4 s; `test_lint_plugin_registration` unregistered component 32.4 s; `test_claude_bootstrap_parity` 29.2 s; `test_worktree_exports` 28.8 s; `test_universal_catalog_parity` 26.4 s; `test_worktree_catalog` oversized annotation 19.5 s; `test_worktree_recovery` clean/mixed/forced 19.2 s; `test_worktree_recovery` unrelated head 18.9 s; `test_review_knowledge_ports` 17.4 s; `test_codebase_map_storage_controls` format matrix 15.0 s | first audit |
| Per-module coverage | tooling absent (no coverage tool configured; none installed) | first audit |

### Failure classification

| Failure | At clean `3a69736d8` | Cause | Owner |
|---|---|---|---|
| 66 errors in 11 modules: `plugins/daodan/plugin.toml: invalid TOML: Invalid statement (at line 3, column 1)` | pass | environment: a concurrent session was rewriting the manifest during the merge | none |
| `test_harness_domain_ownership` regex checks at `:121`, `:139`; `test_lint_plugin_registration` `:31`, `:43` | pass | environment: mid-merge working-tree bytes | none |
| `test_work_record` linked-worktree run state `:1019` | pass (failed at `51589ac2d`) | fixed by the merge | none |
| `test_skill_load_budget`: 2 step caps and 5 unit caps exceeded (for example `frd-method/SKILL.md` 560 > 500, `adr-method/SKILL.md` 483 > 428, `delivery-method/SKILL.md` 315 > 300) | fail | product-defect: the merge combined the caps lowered on one line with content added on the `51589ac2d` line, which never had its own CI run | project-delivery owner: trim the units or raise the caps with a recorded reason |
| `test_review_composition` `test_active_pass_rejects_legacy_review_without_composition` `:445`: `validate_pass_review` accepts an active PASS without `required_specialists`/`jobs` | fail | unknown, leaning product-defect (test committed with the in-flight line ahead of the helper) | work-controller run-state owner; keep the test active |
| `test_science_research` `:561`: a refused escaping publish still leaves `.daodan/.daodan-root` and `.daodan/science.lock` | fail | unknown, leaning product-defect (state written before path validation) | research owner; keep active |
| `test_science_research` `:484`: after a failed publish, `list` returns no record (IndexError at `:495`) | fail | unknown | research owner; keep active |

CI run 40488674799 on `3a69736d8` (Ubuntu, Python 3.12) confirms the last four rows: `Ran 2755 tests in 418.568s`, `FAILED (failures=15, errors=3, skipped=80)`. It adds two failures that no Windows run here showed:

| Failure (CI only) | Cause | Owner |
|---|---|---|
| `test_project_specifications` `test_durable_instructions_carry_neutral_path_and_design_routing`, all five hosts: `'docs/specs/' not found` in the rendered instruction block | unknown; new in the merge and outside this audit's static scope | project-delivery / project-knowledge owner |
| `test_office_creative_comparison` and `test_office_design_compare` directory-link escape tests: `NotADirectoryError` on `inputs/linked` | unknown, Linux-only; raised inside the in-repository fixture paths of F01 | office test owner, with F01 |

CI runs the suite about 5 times faster and skips 80 tests against 16 here. That gap is the platform, SDK and grammar lanes of F02, F06 and F07.

### Findings summary

**High**
- **F01 Fixtures inside the repository.** Six modules build temp trees inside the checkout and inside real run records (`test_process_binding.py:22`, `test_office_design_compare.py:26`, `test_office_records.py:23`, `test_office_creative_comparison.py:29`, `test_office_creative_records.py:22`, `test_office_unified_contract.py:40`). The run created `.daodan/runs/20261026-office-binding-repair/tmp`, `.daodan/runs/20261026-office-unified-delivery/tmp-tests` and the untracked `office-verification-tmp/`. Cause: test-isolation.
- **F02 MCP servers run in no lane.** `test_codebase_map_mcp_wire.py:23` and `test_moe_mcp.py:14` need the `mcp` SDK, which neither CI nor the local machine has. Cause: environment.
- **F03 Bundled-path linter untested.** `scripts/lint_bundled_paths.py` is a required CI gate, but no test proves any of its passes still detects a defect.

**Medium**
- **F04 Other linter passes untested.** Four dependency-graph passes and three registration passes have no negative test.
- **F05 Publication lane missed PyYAML.** `publish-marketplaces.yml` lacked the install until the merge, and no contract test pins it (`test_publish_workflow_contract.py:95`).
- **F06 Windows lane missing.** Windows-only regression tests (for example `test_daodan_render.py:669`) never run in CI.
- **F07 Tree-sitter lane missing.** Grammar-based parsing tests never run in CI, except the documented `test_xray_scripts.py` split.
- **F08 Load-budget rule broken.** `test_xray_load_budget.py:3` says caps only decrease, but commit `7afb0bfc2` raised 11 caps without a rationale.
- **F09 No not-vendored guards.** The "Deliberately not vendored" retirements and the superpowers decision have no retirement guard.

**Low (12):** F10 Worktrunk live probes in an undocumented opt-in lane; F11 wording checks duplicated by byte-equality checks in rendering tests; F12 skip used as a precondition in `test_office_palette.py:306`; F13 a vacuous pass in `test_cutover_identity.py:33-37`; F14 three equivalent duplicate checks; F15 mixed scopes in `test_review_composition.py` and 18 imports between test modules; F16 17 modules need the working directory on the import path; F17 bytecode written into `plugins/`; F18 acceptance tests that check only the exit code; F19 an RDAP double that accepts any request; F20 a read-confinement check that can pass with zero reads; F21 about 4.2k lines of vertical helper scripts with no test.

**Gaps:** the merge's test changes and `test_project_specifications.py` were not audited. Contradiction checks (D6) were sampled, not exhaustive. Coverage tooling is absent, and the CI lane was not emulated.

### Recommended remediation order

1. Make `master` green. Fix the failures that still fail at `3a69736d8`:
   - load budget;
   - review composition;
   - the two science-research tests;
   - project specifications;
   - the two Linux-only office link tests.

   Then fix F01 before the next full run.
2. Fix the CI lanes: F02, F05, F06, F07, F10, F17.
3. Add the missing gate protection: F03, F04, F09. Then repair the oracles: F08 (after the owner decides), F13, F18, F19, F20, F12.
4. Consolidate by churn through `/daodan:maintain-tests` or `/daodan:tidy-repo`:
   - `test_daodan_host_rendering.py` (F11, F14b);
   - the cutover, publish-workflow and catalog-parity trio (F14a, F14c, F13);
   - `test_review_composition.py` (F15);
   - the shared fixtures of the office contract tests (F15, F16).
5. The vertical owners decide on F21.
