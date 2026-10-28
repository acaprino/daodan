# Plan: chat entry routing

Date: 2026-10-28. Status: revision 5 (after reviews routing-plan-1 to
routing-plan-4); approved by the user in advance, conditional on a PASS plan
review.

## 1. Binding

- Specification: [chat entry routing](2026-10-28-chat-entry-routing-design.md),
  revision 4, SHA-256 `42b8070f4e4fef20bac0f53011182b8ebea1d3aaf52e084c4a9a419336d5eb58`,
  approved by the user on 2026-10-28 ("Approvo"); O-1 answered "Sì". Work record
  `.daodan/runs/chat-entry-routing-20261028/`, whose `intent.md` binds both.
- User authorizations of 2026-10-28, recorded as grants `g4-fix` (scope
  t1-t12 and G-1 to G-3; written at revision 3, and revisions 4 and 5 change
  only guards and commands, not scope), `g2-commit` and `g3-push` in the run:
  approve this plan, write the code, work directly on `master` in the main
  checkout, one commit per task, push at the end.
- Base: `1631a5272` (master tip when the plan was revised). At that point the
  tree held only this plan's uncommitted revision and another session's
  untracked `docs/specs/2026-10-28-command-perimeter-design.md`.

## 2. Execution setting

- In place on `master`, sequential waves (user decision: "lavora direttamente
  in main"). The run records no loop workspace, because the agenda already
  binds `master` to four open runs on this checkout
  (`20261028-code-access-p3`, `normative-load-20261028`, an `init-` brainstorm
  run and `lock-free-ownership-20261028`); other sessions may be active.
- Shared-checkout guard, before every task commit and before G-1 and G-4:
  1. `git rev-parse HEAD` equals the task's recorded candidate head, otherwise
     stop: refresh the candidate, rerun verification and review;
  2. `git status --porcelain` shows no change outside this task's write set
     under `plugins/`, `adapters/`, `scripts/` and `tests/`, otherwise stop and
     report the foreign paths to the user without touching them;
  3. stage and commit with explicit paths (`git add -- <write set>`, then
     `git commit -- <write set>`), so nothing else staged by another session
     enters the commit;
  4. before the G-1 build and again before its commit, no change of another
     session under the build's inputs and outputs: `plugins/`, `adapters/`,
     `scripts/`, `CLAUDE.md`, `.claude/`, `AGENTS.md`, `.agents/`, `exports/`,
     the root manifests, `docs/catalog.md` and `docs/plugins/`; foreign files
     elsewhere (for example a new `docs/specs/` draft) are left alone;
  5. before G-4, `git fetch`, then `origin/master..HEAD` must contain only this
     run's commits (each carries this run's `Daodan-Task` trailer or is a
     ruling SHA of this run) and `origin/master` must be an ancestor of HEAD;
     anything else stops the push and is reported.
  This plan file itself is committed by explicit path before T1, with this
  run's trailer `Daodan-Task: chat-entry-routing-20261028 plan`, and that
  commit is recorded as ruling `R-0`, so step 5 accepts it.
  A stop leaves this run's work uncommitted and recoverable; nothing of
  another session is reverted, stashed or committed.
- Each task writes its test first and runs the oracle, which must fail as
  stated; then the implementation, the verification, a light pre-commit review
  and one commit with trailer `Daodan-Task: chat-entry-routing-20261028 wave <n>/10`.
  Each wave closes with a light wave review.
- Test commands use the repository convention
  `python -m unittest discover -s tests -p <file> [-k <name>]`: `tests/` is not
  a package, and on this machine `import tests` resolves to another project.
- Implementers: `python-development:python-engineer` for Python,
  `typescript-development:typescript-engineer` for the OpenCode loader,
  `work-controller:isolated-worker` for kernel declarations and documentation.
- Probes and the eval run only in disposable configurations under the run
  directory, never in the user's installation.
- Versions stay at 1.0.0.

## 3. Keyword lines (S-1)

| Plugin | Words → target |
|---|---|
| `react-development` | React, JSX, Next.js, React hooks → `react-best-practices` |
| `python-development` | Python → `python-engineer` (agent); pytest → `pytest-patterns`; Pydantic → `pydantic-v2`; uv, pyproject → `uv-package-manager`; asyncio → `async-python-patterns`; PyPI, wheel → `python-packaging`; Python profiling → `python-performance-optimization` |
| `typescript-development` | TypeScript, tsconfig → `typescript-write`; Zod, generics → `mastering-typescript`; knip, unused exports → `knip`; `any`, type safety → `type-safety-rules` |
| `kotlin-development` | Kotlin, coroutines, Jetpack Compose, KMP, Ktor → `kotlin-specialist` |
| `docker` | Dockerfile, Docker image, container → `multi-stage-dockerfile` |
| `tauri-development` | Tauri → `tauri`; Rust → `rust-engineer` (agent) |
| `messaging` | RabbitMQ, AMQP, quorum queues → `rabbitmq-production` |
| `business` | business plan, pricing, go-to-market → `saas-business-plan`; contract, NDA, terms of service → `legal-advisor` (agent); privacy policy, GDPR, DPA → `privacy-doc-generator` (agent) |
| `app-analyzer` | competitor app, app teardown → `app-analyzer` (agent) |
| `dependency-audit` | CVE, vulnerable dependencies, dependency licenses → `dependency-audit` |
| `project-delivery` | ADR, decision record → `adr-method`; FRD, functional requirements → `frd-method` |
| `libgdx-development` | libGDX → `libgdx-development` |
| `obsidian-development` | Obsidian plugin → `obsidian-plugin-development` |
| `xterm` | xterm.js, web terminal → `xtermjs-skill` |
| `browser-extensions` | Firefox extension, WebExtension, Manifest V3 → `firefox-extension-dev` |
| `csp` | OR-Tools, CP-SAT, constraint solver, scheduling optimization → `or-tools-expert` (agent) |
| `research` (with workflows) | scientific papers, arXiv, literature → `science-based-approach` |
| `trading-broker-integration` (with workflows) | IBKR, Interactive Brokers, TWS → `ibkr`; MT5, MetaTrader → `mt5` |

Italian forms are added where they differ ("articoli scientifici", "contratto",
"informativa privacy").

## 4. Waves

All tasks consume `spec:42b8070f`; the recorded waves in `work.json` carry the
exact commands.

| Wave | Task | Write set | Oracle fails because | Covers |
|---|---|---|---|---|
| 1 | T1 routing model | `scripts/daodan/model.py`, `load.py`, `tests/test_daodan_routing.py` | no `RoutingSpec` | S-1 |
| 2 | T2 routing validation | `scripts/daodan/validate.py`, `tests/test_daodan_routing.py`, `tests/test_daodan_hooks.py` | routing with `hooks.lifecycle` and no `[[hooks]]` is rejected (`validate.py:516-517`, pinned at `test_daodan_hooks.py:175-179`); missing capability, unknown target and empty routing are accepted | S-1 |
| 3 | T3 routing text | `scripts/daodan/routing.py`, `routing_preamble.md`, `routing_daodan.md`, `tests/test_daodan_routing_text.py` | no `scripts.daodan.routing` | S-3, EX-10, EX-12, EX-14, INV-2, INV-4 |
| 4 | T4 rendering and Claude/Codex delivery | `scripts/daodan/hooks.py`, `render.py`, `tests/test_daodan_routing_render.py` | no `entry-routing` hook and no routing text file; `render.py` writes the text file into the Claude, Codex and OpenCode packages; cases also cover merges with `[[hooks]]` for `research` and `project-delivery`, no entry notes, nothing on Copilot and Pi, the launcher's silent exit 0 | S-2, S-4, EX-9, INV-3, INV-5 |
| 5 | T5 OpenCode delivery | `scripts/daodan/catalogs.py`, `adapters/opencode/templates/index.js`, `tests/opencode/loader.test.mjs`, `tests/host-probes/opencode/index.js`, `tests/test_daodan_catalogs.py` (exception: the probe copy must stay byte-identical, `tests/test_host_probe_fixtures.py:52-56`) | EX-11, EX-13, a missing routing file and a path outside the package root fail | S-2, S-4, EX-11, EX-13, INV-1 |
| 6 | T6 registration check | `scripts/lint_plugin_registration.py`, `tests/test_lint_plugin_registration.py` | a missing routing file passes the linter | S-2 |
| 6 | T7 level test | `tests/test_routing_levels.py` | the file does not exist; verification requires exactly eight failures, each "declares no [routing]" | S-1 table |
| 7 | T8a to T8h kernel declarations, groups of four `plugin.toml`: (a) daodan, research, digital-marketing, trading-broker-integration; (b) frontend-review, pwa-expert, rag-development, stripe; (c) opentelemetry, ai-tooling, system-utils, learning; (d) grabber-development, marketplace-ops, react-development, python-development; (e) typescript-development, kotlin-development, docker, tauri-development; (f) messaging, business, app-analyzer, dependency-audit; (g) project-delivery, libgdx-development, obsidian-development, xterm; (h) browser-extensions, csp | the group's test fails | S-1, UD-2, UD-3 |
| 8 | T9 instructions routing line (O-1) | `plugins/project-knowledge/skills/instructions-method/SKILL.md` | its Loop block names none of the six core entries; verification also runs `tests/test_project_specifications.py`, which forbids activation guarantees in that block | O-1 |
| 8 | T10 documentation | `CLAUDE.md`, `docs/hosts.md` | neither describes the routing kind | S-2, INV-6 |
| 9 | T11 eval harness | `evals/entry-routing/cases.json`, `run_eval.py`, `README.md`, `tests/test_entry_routing_eval.py` | the test file does not exist; it covers `--check` (65 cases: 40 task, 10 vertical or keyword, 15 non-task) and `--verify-results` on a fixture | S-6 |
| 10 | T12 Claude layout, run only if P-1 fails and P-2 passes, otherwise recorded as skipped | `adapters/claude/layout.toml`, `tests/test_daodan_host_rendering.py` | the new test `test_claude_workflows_render_as_skills` fails while the fresh Claude render still has workflow `commands/` | S-5 |

## 5. Closing steps, outside the task gate

The protocol's commit gate accepts only paths in a task's write set, at most
six (`run_state.py:1167-1169`, `contracts/work.toml:71-72`), while one build
rewrites several hundred generated files. These steps are therefore recorded as
rulings in the run (`id`, `task` naming the step, `sha`, `decision`, `reason`,
`cost_if_wrong`, non-empty `evidence`), after the shared-checkout guard of
section 2. A source defect that G-1's suite exposes is fixed by a new planned
task (test first, verification, light review, commit), never inside G-1.

- G-1 rebuild: `python scripts/daodan_build.py`, then `--check --support`, both
  sync checks, linters 1 to 4 and 9 and `python -m unittest discover -s tests`.
  One commit holds exactly the files the build and the two synchronizers
  rewrote (`exports/**`, root manifests, `AGENTS.md`, `docs/catalog.md`,
  `docs/plugins/*.md`). `check_version_bumps.py` fails on the range because
  versions stay at 1.0.0; its output goes in the ruling.
- G-2 probes and measured eval (P-1 to P-5, with the eval with and without
  hooks, session start time and the A-5 reinstall check), recorded in
  `docs/hosts.md` and `evals/entry-routing/RESULTS.md`, one commit.
- G-3, only after T12 ran: G-1 again and the eval again.
- G-4 push `master` (grant `g3-push`).

`tests/test_daodan_hooks.py` failed once in five runs at the base (review
routing-plan-2). A failure there during T2 or T4 is rerun once; a repeat is
investigated before the task continues.

Lead for P-1: later in the session that showed 6 of the 31 `daodan` commands,
a refreshed listing showed all 31, after the installed package had been
updated at 14:24. P-1 first checks whether the first listing came from a stale
package.

## 6. Cost

19 tasks, about 29 light reviews, then the closing steps. Estimate: 5 to 8
hours of agent time and several million tokens, mostly reviews and the eval
(about 130 headless sessions).
