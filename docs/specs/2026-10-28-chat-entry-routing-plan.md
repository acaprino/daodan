# Plan: chat entry routing

Date: 2026-10-28. Status: **proposed plan; execution not authorized**.

## 1. Binding

- Specification: [chat entry routing](2026-10-28-chat-entry-routing-design.md),
  revision 4, SHA-256 `42b8070f4e4fef20bac0f53011182b8ebea1d3aaf52e084c4a9a419336d5eb58`,
  approved by the user on 2026-10-28 ("Approvo"); O-1 answered "Sì". Work record
  `.daodan/runs/chat-entry-routing-20261028/`, whose `intent.md` binds both.
- Approving this plan grants no code, commit, merge or push; those are asked
  separately before execution.
- Base: `5cf722b54`. The uncommitted workspace reservation work in the main
  checkout stays untouched.

## 2. Execution setting

- `WORKTREE` from the base, created through `worktree-manager`; every task,
  test and commit happens there.
- Waves run sequentially. Each task writes its test first and runs the oracle,
  which must fail as stated; then the implementation, the verification, a light
  pre-commit review and one commit with trailer
  `Daodan-Task: chat-entry-routing-20261028 wave <n>/12`. Each wave closes with a
  light wave review.
- Implementers: `python-development:python-engineer` for Python,
  `typescript-development:typescript-engineer` for the OpenCode loader,
  `work-controller:isolated-worker` for kernel declarations and documentation.
- Probes and the eval run only in disposable configurations under the run
  directory, never in the user's installation.
- Versions stay at 1.0.0; `check_version_bumps.py` will fail on the range and
  is reported.

## 3. Keyword lines (S-1, shown for approval)

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

Italian forms are added where they differ (for example "articoli scientifici",
"contratto", "informativa privacy").

## 4. Waves

All tasks consume `spec:42b8070f`.

| Wave | Task | Write set | Oracle (fails before) | Verification | Covers |
|---|---|---|---|---|---|
| 1 | T1 routing model | `scripts/daodan/model.py`, `scripts/daodan/load.py`, `tests/test_daodan_routing.py` | `python -m unittest tests.test_daodan_routing`: `ImportError` on `RoutingSpec` | same, passes: `[routing]` parsed, unknown keys rejected | S-1 |
| 2 | T2 routing validation | `scripts/daodan/validate.py`, `tests/test_daodan_routing.py` | new cases fail: missing `hooks.lifecycle`, unknown target, empty routing accepted | `python -m unittest tests.test_daodan_routing tests.test_daodan_hooks` | S-1 |
| 3 | T3 routing text | `scripts/daodan/routing.py`, `scripts/daodan/routing_preamble.md`, `scripts/daodan/routing_daodan.md`, `tests/test_daodan_routing_text.py` | `ModuleNotFoundError: daodan.routing` | same, passes: host identities, TRIGGER clause or first sentence, pointer rule (EX-14), role lines absent on Codex (EX-12), 9,000 cap (EX-10) | S-3, INV-2, INV-4 |
| 4 | T4 Claude and Codex delivery | `scripts/daodan/hooks.py`, `scripts/daodan/render.py`, `tests/test_daodan_routing_render.py` | no `entry-routing` hook in a rendered fixture | same plus `tests.test_daodan_hooks`: hook rendered, merged with `[[hooks]]` for `research`, no entry notes (INV-5), launcher exits 0 silently on missing root, file and encoding (EX-9) | S-2, INV-3, INV-5 |
| 5 | T5 OpenCode delivery | `scripts/daodan/catalogs.py`, `adapters/opencode/templates/index.js`, `tests/opencode/loader.test.mjs` | new loader cases EX-11, EX-13 fail | `python -m unittest tests.test_opencode_loader tests.test_daodan_routing_render` | S-2, S-4, EX-11, EX-13 |
| 5 | T6 registration check | `scripts/lint_plugin_registration.py`, `tests/test_lint_plugin_registration.py` | new case "manifest names a missing routing file" passes the linter | `python -m unittest tests.test_lint_plugin_registration` | S-2 |
| 6 | T7 level test | `tests/test_routing_levels.py` | `ModuleNotFoundError` | its eight group tests fail until wave 7 (expected) | S-1 table |
| 7 | T8a to T8h kernel declarations, 4 `plugin.toml` each: (a) daodan, research, digital-marketing, trading-broker-integration; (b) frontend-review, pwa-expert, rag-development, stripe; (c) opentelemetry, ai-tooling, system-utils, learning; (d) grabber-development, marketplace-ops, react-development, python-development; (e) typescript-development, kotlin-development, docker, tauri-development; (f) messaging, business, app-analyzer, dependency-audit; (g) project-delivery, libgdx-development, obsidian-development, xterm; (h) browser-extensions, csp | the four manifests | `tests.test_routing_levels.<group>` fails | the same group test passes | S-1, UD-2, UD-3 |
| 8 | T9 instructions routing line (O-1) | `plugins/project-knowledge/skills/instructions-method/SKILL.md` | `rg -n "fix-bug" ` on its Loop block finds nothing | the Loop block names the core `/daodan:` entries in one sentence | O-1 |
| 8 | T10 documentation | `CLAUDE.md`, `docs/hosts.md` | `rg -n "\[routing\]" CLAUDE.md docs/hosts.md` finds nothing | both describe the routing kind; hosts marked "generated, not probed" | S-2, INV-6 |
| 9 | T11 eval harness | `evals/entry-routing/cases.json`, `evals/entry-routing/run_eval.py`, `evals/entry-routing/README.md` | `python evals/entry-routing/run_eval.py --check` fails: file missing | `--check` validates 65 cases (40 task, 10 vertical or keyword, 15 non-task) without calling a model | S-6 |
| 10 | T12 rebuild and gates | `AGENTS.md`, `docs/catalog.md` and the regenerated `docs/plugins/*.md` (granularity exception: generated output committed with the kernel, as in run `20261027-code-access`) | `python scripts/daodan_build.py --check --support` reports drift | build, `--check --support`, both sync checks, linters 1 to 4 and 9, `python -m unittest discover -s tests` | INV-2 |
| 11 | T13 probes and measured eval | `docs/hosts.md`, `evals/entry-routing/RESULTS.md` | `RESULTS.md` absent | P-1 to P-5 recorded; eval with and without hooks; session start time; targets of S-6 met or the miss reported | S-5, S-6, A-1, A-4 |
| 12 | T14 Claude layout, only if P-1 fails and P-2 passes | `adapters/claude/layout.toml`, `tests/test_daodan_host_rendering.py`, generated output | the rendered Claude package has `commands/` for workflows | workflows render as skills with the same `/<plugin>:<workflow>` names; gates of T12 rerun | S-5 |

T14 is skipped and recorded when the probes do not call for it; if it runs,
T13's eval runs again on the new layout.

Lead for P-1: later in the same session that showed 6 of the 31 `daodan`
commands, a refreshed listing showed all 31 with their descriptions, after the
installed package had been updated at 14:24. P-1 first checks whether the first
listing came from a stale package rather than from the budget.

## 5. Cost

About 20 tasks and 30 light reviews. Estimate: 5 to 8 hours of agent time and
several million tokens, mostly reviews and the eval (65 prompts, twice, about
130 headless sessions of a few thousand tokens each).
