# work-controller restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `project-protocol` with `work-controller` (skill `work-record`), move model routing into a new `model-routing` plugin and the review roster into `senior-review`, with every consumer renamed and every gate green.

**Architecture:** Three moves, smallest first. Routing scripts and references leave for `model-routing`; `review_roster.py` leaves for `senior-review`; what remains is renamed in place to `work-controller`, whose only skill is `work-record`. Behavior does not change: files move, identities are renamed, the compiler regenerates every host.

**Tech Stack:** Python 3 standard library, the repository compiler (`scripts/daodan_build.py`), `unittest`.

**Spec:** `docs/adr/ADR-0002-work-controller.md`. This plan is part 1 of 2. Part 2 (decision map and tickets, clarification contract and question shape, generic interview, graph composition with `graphlib`) is planned after part 1 lands, because its paths are the ones part 1 creates.

## Global Constraints

- Review scope and applicable check breadth remain distinct; this restructure adds no independent reading-depth policy.
- `work-controller` declares no dependencies (ADR-0002 INV-001). `model-routing` declares none either.
- No Daodan plugin depends on a Shinatama plugin (INV-002).
- Standard library only.
- Run state stays under `.daodan/`; `run_state.py` behavior is unchanged.
- `work-record/SKILL.md` must not grow: `tests/test_skill_load_budget.py` caps every step that loads it.
- Never hand-edit `exports/` or the root manifests; rebuild.
- Dated records under `docs/superpowers/` keep retired names, except the links ADR-0002 names: the 2026-10-20 and 2026-10-24 specifications.
- Versions: `work-controller` 1.0.0, `model-routing` 1.0.0, each touched consumer a minor bump, marketplace `metadata.version` 38.11.0 → 39.0.0 (a plugin is removed).
- Commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A shipped body still names `plugins/project-protocol/...` or `project-protocol:`: on an installed host the read fails silently. Pinned in Task 3 step 6 (zero-hit grep) and by `lint_bundled_paths.py`.
2. A host keeps a retired `project-protocol` package next to `work-controller`. Pinned in Task 3 step 8 (`exports/*/plugins/project-protocol` absent).
3. `model-routing` silently gains a dependency on `work-controller` through a "load the work record" sentence. Pinned by `lint_dependency_graph.py` in Task 1 step 6.
4. The roster moves but a coordinator still resolves `PROTOCOL_ROOT`. Pinned in Task 2 step 4 (zero-hit grep for `PROTOCOL_ROOT`).
5. A consumer keeps using the run record but loses its declared dependency, or keeps one it no longer uses. Pinned by `lint_dependency_graph.py` in Task 3 step 7.

---

### Task 1: model-routing plugin

**Files:**
- Create: `plugins/model-routing/plugin.toml`, `plugins/model-routing/skills/model-routing/SKILL.md`, `plugins/model-routing/skills/model-routing/SKILL.toml`, `docs/plugins/model-routing.md`
- Move (git mv) from `plugins/project-protocol/skills/project-protocol/` to `plugins/model-routing/skills/model-routing/`: `scripts/{tier_router,task_router,build_model_catalog,benchmark_snapshot,capability_resolver,registry_fetch,usage_pricing,build_model_prices,price_crosscheck}.py`, `references/{model-catalog.json,model-prices.json,price-rules.json,task-routing.md,model-catalog-refresh.md}`
- Modify: `plugins/project-protocol/skills/project-protocol/SKILL.md:74-75` (drop the routing pointer), `plugins/project-lifecycle/skills/lifecycle-method/references/preflight.md:12`, `plugins/project-lifecycle/plugin.toml`, `plugins/daodan/plugin.toml`, `CLAUDE.md` dependency table
- Test: `tests/test_{tier_router,task_router,task_routing_binding,task_routing_host_binding,build_model_catalog,benchmark_snapshot,capability_resolver,registry_fetch,usage_pricing}.py`

**Interfaces:**
- Produces: skill identity `model-routing:model-routing`; helper path `${CLAUDE_PLUGIN_ROOT}/skills/model-routing/scripts/task_router.py`; method `references/task-routing.md` under that skill.

- [ ] **Step 1: Point the nine test files at the new location.** Replace `"plugins" / "project-protocol" / "skills" / "project-protocol" / "scripts"` (and its string form) with `"plugins" / "model-routing" / "skills" / "model-routing" / "scripts"`.
- [ ] **Step 2: Run them, expect failure.** Run from `tests/`: `python -m unittest test_tier_router test_task_router test_task_routing_binding test_task_routing_host_binding test_build_model_catalog test_benchmark_snapshot test_capability_resolver test_registry_fetch test_usage_pricing`. Expected: errors, scripts not found.
- [ ] **Step 3: Move the files with `git mv`** as listed under Files. In the moved `task-routing.md:53,65` and `model-catalog-refresh.md:68`, `skills/project-protocol` becomes `skills/model-routing`; `model-catalog-refresh.md:142` bumps `model-routing`; `task-routing.md:92` reads "through the work record's `run_state.py update`".
- [ ] **Step 4: Write the plugin.** `plugin.toml`: `name = "model-routing"`, `version = "1.0.0"`, description "Per-request model routing: host inventory, classifier signals, deterministic model and effort selection, confirmation binding, model catalog and prices.", capabilities copied from project-protocol (`required = ["repository.read", "repository.write", "shell.execute"]`, `optional = ["network.fetch"]`), `[dependencies] required = []`, `skills = ["model-routing"]`. `SKILL.md`: description "Select the model and effort for each LLM job through task_router.py, and refresh the model catalog and prices. TRIGGER WHEN: a coordinator routes an LLM job, or the catalog or prices need a refresh."; body of at most 8 lines pointing to `references/task-routing.md` and `references/model-catalog-refresh.md`. `SKILL.toml` copies project-protocol's (`kind = "method"`).
- [ ] **Step 5: Rewire the consumer.** In project-protocol `SKILL.md` delete "For models, routing, pricing or dispatch/resume,\nread `references/task-routing.md`." In `preflight.md:12` the Models row loads `model-routing:model-routing`, `references/task-routing.md`. Add `model-routing` to `[dependencies].required` of `project-lifecycle` and `daodan`; minor-bump both. CLAUDE.md table: new row `| model-routing | none |`, `model-routing` added to the project-lifecycle row. Write `docs/plugins/model-routing.md` with a two-sentence explanation above the generated markers (copy the marker shape from `docs/plugins/project-protocol.md`).
- [ ] **Step 6: Verify.** Re-run step 2's command: OK. Then `python scripts/daodan_build.py && python scripts/sync_plugin_docs.py && python scripts/lint_dependency_graph.py && python scripts/lint_bundled_paths.py && python scripts/lint_plugin_registration.py`: all rc 0.
- [ ] **Step 7: Commit** "Move model routing into its own model-routing plugin".

### Task 2: review roster into senior-review

**Files:**
- Move (git mv): `plugins/project-protocol/skills/project-protocol/scripts/review_roster.py` → `plugins/senior-review/skills/review-preparation/scripts/review_roster.py`
- Modify: `plugins/senior-review/skills/review-method/references/light.md:24-27`, `plugins/senior-review/skills/review-preparation/references/candidate-grounding.md:99-103`, `plugins/senior-review/skills/review-preparation/references/composition.md`, `plugins/senior-review/plugin.toml` (bump), `plugins/project-protocol/contracts/work.toml:91`, `plugins/project-protocol/skills/project-protocol/SKILL.md:142`
- Test: `tests/test_review_roster.py`, `tests/test_review_composition.py`

**Interfaces:**
- Produces: helper path `${CLAUDE_PLUGIN_ROOT}/skills/review-preparation/scripts/review_roster.py`, same CLI (`compute --shape light|branch ...`).

- [ ] **Step 1: Point both tests at the new path**, run them from `tests/`: expected failure, script not found.
- [ ] **Step 2: `git mv` the script.**
- [ ] **Step 3: Rewrite the calls.** `light.md` and `candidate-grounding.md` run `python "${CLAUDE_PLUGIN_ROOT}/skills/review-preparation/scripts/review_roster.py" compute ...` with the same arguments; delete the sentences that define `PROTOCOL_ROOT`. `work.toml:91` and work-record `SKILL.md:142` say "senior-review's `review_roster.py`". Minor-bump senior-review.
- [ ] **Step 4: Verify.** Tests from step 1: OK. `git grep -n PROTOCOL_ROOT -- plugins scripts tests`: no output. `python scripts/daodan_build.py && python scripts/lint_bundled_paths.py`: rc 0.
- [ ] **Step 5: Commit** "Give the review roster to senior-review".

### Task 3: rename project-protocol to work-controller with skill work-record

**Files:**
- Move: `plugins/project-protocol/` → `plugins/work-controller/`; `plugins/work-controller/skills/project-protocol/` → `plugins/work-controller/skills/work-record/`; `docs/plugins/project-protocol.md` → `docs/plugins/work-controller.md`; `tests/test_project_protocol.py` → `tests/test_work_record.py`
- Modify: every non-export file `git grep -l project-protocol` lists in `plugins scripts tests adapters evals docs CLAUDE.md README.md .claude`, excluding `evals/**/runs/` and `docs/superpowers/` other than the 2026-10-20 and 2026-10-24 specifications; `.claude-plugin/marketplace.json` (39.0.0); then regenerate `AGENTS.md` and `.agents/skills/`.

**Interfaces:**
- Consumes: Task 1 and Task 2 already removed routing and roster.
- Produces: skill `work-controller:work-record`, role `work-controller:isolated-worker`, contracts `work-controller/contracts/work.toml` and `work-controller/contracts/project-result.toml`, helper `${CLAUDE_PLUGIN_ROOT}/skills/work-record/scripts/run_state.py`, compiler constant `INLINE_WORKER_REFERENCE = "work-controller/isolated-worker"`.

- [ ] **Step 1: Rename the tests first.** `git mv tests/test_project_protocol.py tests/test_work_record.py`; apply step 3's replacements to `tests/`. Run `python -m unittest discover -s tests -p "test_work_record.py"`: expected error, path not found.
- [ ] **Step 2: Move the kernel** with the two `git mv` commands above. `plugin.toml`: `name = "work-controller"`, `version = "1.0.0"`, description "Run records, agenda, gates, grants and recovery for coordinated work, shared by Daodan and Shinatama: the work record and the isolated worker.", `skills = ["work-record"]`. `SKILL.md`: `name: work-record`, heading `# Work record`, same word count or fewer.
- [ ] **Step 3: Replace identities, in this order,** over the Modify scope: `project-protocol:project-protocol` → `work-controller:work-record`; `project-protocol:isolated-worker` → `work-controller:isolated-worker`; `project-protocol/isolated-worker` → `work-controller/isolated-worker`; `project-protocol/contracts/` → `work-controller/contracts/`; `plugins/project-protocol/skills/project-protocol/` → `plugins/work-controller/skills/work-record/`; `skills/project-protocol/` → `skills/work-record/`; `"project-protocol"` → `"work-controller"` in `plugin.toml` dependency arrays and test fixtures. Every remaining bare `project-protocol` is read and rewritten by hand (prose, the CLAUDE.md "leaf" paragraph, the dependency table row and column entries).
- [ ] **Step 4: Compiler constants.** `scripts/daodan/model.py:23`, `composition.py:132,166`, `render.py:1120`, `reviewer_catalog.py:128,141,275`, `lint_dependency_graph.py:237`, `lint_fact_anchors.py:63-117` take the new identities and paths.
- [ ] **Step 5: Bumps and regeneration.** Minor-bump every plugin whose files changed in steps 3-4 (`check_version_bumps.py` names any missed one); marketplace 39.0.0. Run `python scripts/daodan_build.py`, `python scripts/sync_plugin_docs.py`, `python scripts/sync_codex_instructions.py`.
- [ ] **Step 6: Zero stale names.** `git grep -n -E 'project-protocol' -- . ':!exports' ':!docs/superpowers' ':!evals/**/runs' ':!docs/adr/ADR-0002-work-controller.md'`: only historical prose that names the retired plugin as retired, each line read.
- [ ] **Step 7a: Legacy record compatibility.** Initialize records through the archived pre-rename helper, then show, resume, validate and complete them through the new helper. Preserve recorded identities and evidence, including delivered review lenses and critic. New dispatch uses only the new identity.
- [ ] **Step 7: All gates.** The nine consistency gates (`daodan_build.py --check --support`, `sync_plugin_docs.py --check`, `sync_codex_instructions.py --check`, `lint_dependency_graph.py`, `lint_bundled_paths.py`, `lint_plugin_registration.py`, `lint_fact_anchors.py`, `lint_host_vocabulary.py`, `adapters/copilot/policies/xray-guard/test_xray_guard.py`) rc 0, then `python -m unittest discover -s tests`: OK.
- [ ] **Step 8: Retired package gone.** `ls exports/*/plugins | grep -c project-protocol`: 0. `python scripts/check_version_bumps.py origin/master HEAD`: ok.
- [ ] **Step 9: Commit** "Replace project-protocol with work-controller and its work-record skill", push, confirm `consistency` and `publish-marketplaces` succeed on GitHub.

## After part 1

- Shinatama (separate repository) switches its dependency to `work-controller@daodan` where it used `project-protocol@daodan`, if anywhere; today its three Daodan edges are `text-humanizer`, `report-rendering` and three development plugins.
- Part 2 plan: decision map and tickets on `graphlib`, clarification contract and question shape, generic interview, graph composition.
