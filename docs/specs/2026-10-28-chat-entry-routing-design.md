# Chat entry routing

Date: 2026-10-28. Status: draft for approval, revision 4 (after reviews
routing-spec-1 to routing-spec-3; revision 4 fixes the Medium and Low findings of routing-spec-3, which passed revision 3).

## Intent

A user who writes "c'è un bug nel login, risolviamolo", "voglio investigare un
problema" or "rifattorizziamo questa classe" should get the matching workflow
(`/daodan:fix-bug`, `/daodan:investigate-problem`, `/daodan:refactor-code`)
without typing the command, the way Superpowers activates its skills. A plugin
whose knowledge applies to a technology ("React", "Stripe", "FRD") should be
picked up from that word alone.

User decisions (2026-10-28, chat):

- UD-1: activation works **like Superpowers**: text injected when a session
  starts tells the model which entries exist and when they apply. No
  per-message keyword router and no classifier model.
- UD-2: **every plugin** that has something to route takes part now. Each
  plugin chooses one of three levels: its workflows with their trigger
  phrases, keyword lines only, or nothing.
- UD-3: niche development plugins (libgdx-development, obsidian-development,
  xterm, browser-extensions, csp) get keyword lines only.
- UD-4: a plugin injects its text only when it is installed and enabled.
- UD-5: this work comes **before** the lock-free work ownership redesign
  (`docs/specs/2026-10-28-lock-free-work-ownership-design.md`).

## Current state

- No plugin injects its entries when a session starts. `office` has a
  user-prompt hook for Office files (`plugins/office/plugin.toml:20-24`);
  `research` has session and prompt hooks for Science Mode
  (`plugins/research/plugin.toml:20-32`).
- Seventeen plugins ship 65 workflows (`daodan` 31, the verticals 34); seven
  have no `TRIGGER WHEN` clause (`daodan` `document`, `presentation`, `start`,
  `theme`; `research` `science-mode`, `science-research`, `update-research`).
  On Claude they render as plugin commands (`adapters/claude/layout.toml:8`).
- Claude Code caps the skill listing at 1% of the context window and drops the
  descriptions of the least used skills first; the docs say the listing always
  contains every skill name, and that commands were merged into skills [S-1].
  Yet in this session, with about 250 skills installed, the listing showed 6 of
  the 31 `daodan` commands. That contradiction is unexplained (P-1).
- Superpowers injects its `using-superpowers` skill at `SessionStart` as
  `additionalContext` [S-3]. Hook context is capped at 10,000 characters per
  output, and the docs advise factual statements over imperative instructions
  [S-4].
- Hooks today exist only as kernel declarations: `[[hooks]]` in `plugin.toml`
  (`CLAUDE.md:221-226`), with `hooks.lifecycle` declared exactly when hooks exist
  (`scripts/daodan/validate.py:513-517`) and the script under a declared skill
  (`validate.py:535-546`). The shared launcher starts two Python processes and
  exits 1 when the plugin root or script is missing (`scripts/daodan/hooks.py:30-45`,
  pinned by `tests/test_daodan_hooks.py:301-317`). Rendering a hook stamps an
  entry note into every skill and workflow body (`hooks.py:53-58,77-82`,
  `render.py:789,815,922-937`).
- Hosts: Claude and Codex render `hooks/hooks.json` (`hooks.py:14`); OpenCode
  runs callbacks through its loader, one after another, before the first prompt
  (`adapters/opencode/templates/index.js:263,430`), and clears session-start
  context at the first prompt whenever any selected plugin has a
  user-prompt-submit hook (`index.js:433-434`), which `office` and `research`
  have; Copilot's adapter marks plugin hooks unsupported after an issue open on
  2026-09-03 (`adapters/copilot/capabilities.toml:44-49`); Pi exposes lifecycle
  events only to TypeScript extensions and the adapter supports none
  (`adapters/pi/capabilities.toml:52-58`). An OpenCode 2.1.4 probe captured a
  hook's injected context on 2026-10-27
  (`docs/plugins/research/validation.md:46-66`); no Codex hook probe exists.

## Design

### S-1 A routing declaration in each kernel

- A plugin opts in with a `[routing]` table in `plugin.toml`, declarative
  metadata only:
  - `workflows = true` lists the plugin's workflows with their triggers;
  - `[[routing.keywords]]` rows, each with `words` (one to eight short terms)
    and `target` (a skill, role or workflow of the same plugin), add one line
    each. A role target is written as an agent to dispatch, and is left out on
    a host that gives roles no registered identity (Codex passes roles inline,
    `docs/hosts.md:149`).
- A plugin without `[routing]` contributes nothing. A plugin with `[routing]`
  declares the `hooks.lifecycle` capability as optional; the validator requires
  it, checks every `target`, and rejects a `[routing]` that would produce no
  line on any host. On a host where a plugin produces no line, that plugin
  ships no routing text and no routing hook.
- Levels for this release (UD-2, UD-3):

| Level | Plugins |
|---|---|
| Workflows, plus keywords where listed | `daodan`; `research` (keyword line for scientific papers); `digital-marketing`; `trading-broker-integration` (keywords IBKR, MT5); `frontend-review`; `pwa-expert`; `rag-development`; `stripe`; `opentelemetry`; `ai-tooling`; `system-utils`; `learning`; `grabber-development`; `marketplace-ops` |
| Keywords only | `react-development`, `python-development`, `typescript-development`, `kotlin-development`, `docker`, `tauri-development`, `messaging`, `business`, `app-analyzer`, `dependency-audit`, `project-delivery` (ADR, FRD), `libgdx-development`, `obsidian-development`, `xterm`, `browser-extensions`, `csp` |
| Nothing | the internal providers reached through `daodan` entries: `work-controller`, `model-routing`, `skill-catalog`, `report-rendering`, `worktree-manager`, `codebase-map`, `project-lifecycle`, `project-knowledge`, `testing`, `clean-code`, `abstraction-architect`, `repo-hygiene`, `peer-review`, `moe`, `platform-engineering`, `senior-review`, `office`, `text-humanizer` |

  The keyword words of each plugin are chosen in the plan and shown with it.

### S-2 Delivery, compiler-owned

- From `[routing]` the compiler renders one generated text file per plugin
  package, and the host's mechanism to deliver it. This is a new kind beside
  `[[hooks]]`: its own model field, validation and rendering, and **no** entry
  notes in bodies.
- Claude and Codex: a session-start hook named `entry-routing` in
  `hooks/hooks.json`, with its own launcher of one Python process. It resolves
  the plugin root as the existing launcher does, reads the text file and prints
  `hookSpecificOutput.additionalContext`. Once started, it exits 0 with no
  output on any error (root, file, encoding). A missing Python interpreter
  fails before any launcher runs, as for every Python hook; the host reports
  it and the session still starts. On Claude the hook runs at startup, resume,
  clear, compact and fork, so the text survives a compaction [S-4]; on Codex
  the same matcher is unprobed until P-3.
- A plugin with both `[[hooks]]` and `[routing]` (`research`) gets one
  `hooks/hooks.json` holding both entries.
- OpenCode: no process. The manifest's `daodan` key names each plugin's text
  file; the loader reads the files of the selected plugins once per session
  and keeps them in a routing slot that the context hook pushes on every model
  request. Unlike `startup`, that slot is never cleared by a prompt
  (`index.js:433-434`). The context hook is registered whenever routing text or
  lifecycle hooks are selected; today the setup returns early when no hooks are
  selected (`index.js:390-392`). Each read is confined to the installed package
  root; a missing or unreadable file is skipped with one log line, and the other
  plugins' routing and hooks still register. The loader change comes with its
  `node --test` cases, and the registration linter checks that every routing
  file the manifest names exists.
- `CLAUDE.md:221-226` and `docs/hosts.md:463-480` are amended to describe this
  kind; `[[hooks]]` and the `office` and `research` hooks keep their contract.

### S-3 Content

- A fixed preamble per plugin, written as facts: these are the plugin's entry
  workflows and knowledge; a request that matches a line runs through that
  entry, invoked with the host's skill or command mechanism, or dispatched as an
  agent when the line says so, before other work.
- Workflow lines: the entry's identity on that host (`/daodan:fix-bug` on
  Claude; the adapter's identity elsewhere) and its `TRIGGER WHEN` clause, or
  its first sentence when it has none.
- A `DO NOT TRIGGER WHEN` clause is kept whole, with its condition, when it
  holds at least one parenthesized pointer `(use A)` or `(use A or B)`, each
  name being a workflow of the same plugin or a `/plugin:workflow` identifier
  of a plugin that the source plugin requires. Each name is rewritten to that
  entry's identity on the host. A clause without such a pointer, and a pointer
  to a plugin that is not required, is dropped, so the text never names an
  entry that may be disabled.
- Keyword lines: the words and the target's identity on that host.
- The `daodan` preamble adds two facts: its entries are the primary entry
  points for project work whatever the stack or domain, and a vertical entry
  applies when the request is specific to that domain.
- Preambles are Markdown templates of the compiler; lines are derived at build
  time; nothing is listed by hand.
- The build fails when one plugin's text exceeds 9,000 characters [S-4].

### S-4 What "enabled" means on each host

- Claude, Codex: the plugin is enabled in the host's plugin settings.
- OpenCode: the plugin is in the loader's resolved selection, which includes the
  dependency closure of selected plugins (`index.js:132`); excluding `research`
  while `daodan` is selected keeps `research` and its text.
- Copilot, Pi: nothing is injected; the workflow descriptions are the only
  routing. `docs/hosts.md` states it, and P-5 rechecks Copilot.

### S-5 Probes before claims

All in disposable configurations, never the production installation:

- P-1 (Claude): whether plugin commands appear in the skill listing at all,
  why only 6 of 31 did here, and whether a command named in hook context can be
  invoked while absent from the listing.
- P-2 (Claude): the same with workflows rendered as plugin skills. If P-1 shows
  commands missing or uninvokable and P-2 shows skills listed and invokable,
  the Claude adapter renders workflows as skills, keeping every
  `/<plugin>:<workflow>` name.
- P-3 (Codex) and P-4 (OpenCode): the routing text reaches the model, on Codex
  also after a compaction, on OpenCode also after a second prompt with `office`
  selected. Until a probe
  passes, `docs/hosts.md` marks that host "generated, not probed".
- P-5 (Copilot): whether the current Copilot CLI runs a plugin's session-start
  hook. If it does, the Copilot adapter gains the hook in a later change; this
  spec does not render it.

### S-6 Activation eval

- `evals/entry-routing/`, prompts in Italian and English: 40 task prompts across
  the core `daodan` flows, 10 vertical or keyword prompts (SEO audit, IBKR
  audit, deep research, a React question, an FRD), 15 prompts that must not
  start a workflow (explanations, small talk, questions about code).
- Each prompt runs headless in a disposable Claude configuration, with and
  without the routing hooks; the first entry invoked is read from the
  transcript.
- Targets (agent proposal, A-2): with the hooks, at least 85% of task and
  vertical prompts invoke the expected entry first, at most 10% of non-task
  prompts invoke any entry, both better than without the hooks. A miss changes
  the preamble or descriptions and runs again; the report keeps every run.

## Invariants

- INV-1: On Claude, Codex and OpenCode, each enabled plugin (S-4) contributes
  exactly its own routing text for the whole session; a disabled or absent
  plugin contributes nothing.
- INV-2: Routing lines derive from kernel declarations and workflow frontmatter
  at build time; the drift gate covers them.
- INV-3: Routing delivery only adds context. It never runs a workflow, writes a
  file or blocks a prompt; once started, the launcher exits 0 with no output on
  any error.
- INV-4: No plugin's routing text exceeds 9,000 characters.
- INV-5: The routing hook adds no note to any skill or workflow body.
- INV-6: A host claim about hook execution rests on a passed probe; otherwise
  the docs mark it unprobed.

## Examples

- EX-1: "c'è un bug nel login, risolviamolo" → `/daodan:fix-bug` first.
- EX-2: "voglio investigare perché i test falliscono" → `/daodan:investigate-problem`.
- EX-3: "rifattorizziamo la classe UserService" → `/daodan:refactor-code`.
- EX-4: "come funziona il modulo di login?" → no workflow; an answer.
- EX-5: "fai un audit SEO del sito" → `/digital-marketing:seo-audit` when that
  plugin is enabled.
- EX-6: "questo componente React rirenderizza troppo" → the React knowledge
  target is loaded.
- EX-7: after `/compact`, every enabled plugin's text is present again.
- EX-8: with `digital-marketing` disabled on Claude, its text is absent and EX-5
  gets no vertical entry.
- EX-9: the root of a plugin package is missing at session start: the routing
  hook prints nothing, exits 0, and the session starts.
- EX-10: a plugin's text would exceed 9,000 characters: the build fails naming
  the plugin.
- EX-11: on OpenCode with `daodan` selected, the routing text is in the model
  context on the first and on the third prompt, although `office` has a
  user-prompt-submit hook.
- EX-12: the `csp` keyword line appears on Claude as an agent to dispatch; on
  Codex `csp` ships no routing text and no routing hook.
- EX-13: on OpenCode with `options.plugins: ["stripe"]`, whose closure has no
  lifecycle hook, the `stripe` routing text is in the model context.
- EX-14: the `fix-bug` line keeps "the user only wants to understand a problem
  (use /daodan:investigate-problem)"; the `organize-files` line of
  `system-utils`, which does not require `daodan`, drops its pointer to
  `/daodan:refactor-code`.

## Rejected alternatives

- RA-1, keyword router on every message: the user chose session-start text (UD-1).
- RA-2, classifier model per message: latency, cost and an API key.
- RA-3, one central hook in `daodan` listing every plugin: it would name
  commands of plugins that are not installed or enabled (UD-4).
- RA-4, a hand-written `[[hooks]]` row and script in each of the 30 kernels: 30
  copies of one launcher and one text format, and every one would stamp entry
  notes into its bodies (`hooks.py:53-58`).

## Assumptions (agent, not user decisions)

- A-1: Session start cost on Claude and Codex is one process per routing
  plugin, run in parallel on Claude; OpenCode reads files and starts none. The
  plan measures it; the target is under 3 seconds added with every plugin
  enabled.
- A-2: The eval targets of S-6 are the agent's proposal; the user may change
  them at approval.
- A-3: When Superpowers is also installed, both texts coexist; Daodan's text
  speaks only for its own entries.
- A-4: With every plugin enabled the injected text is about 15,000 to 20,000
  characters per session, about 4,000 to 5,000 tokens: the workflow lines of the
  14 workflow plugins measure 11,892 characters before preambles and keyword
  lines (`daodan` 5,697). The plan reports the measured total.
- A-5: Versions stay at 1.0.0 (owner rule of 2026-10-28). Whether Claude, Codex
  and Copilot refresh an installed package whose version did not change is
  unverified; the plan checks it on the disposable configuration and reports
  the reinstall step if one is needed.

## Success criteria

- Compiler tests: `[routing]` validation (capability, targets, empty routing);
  the hook and its text on Claude, Codex and OpenCode and nothing on Copilot
  and Pi; host identities in lines; no entry notes; the size cap.
- Existing tests that pin the old hook model (`tests/test_daodan_hooks.py:170-179,
  233-234,301-317`) keep their meaning for `[[hooks]]`; new tests pin the
  routing kind.
- Launcher tests: output shape per host; exit 0 and no output on each error.
- Loader tests (`node --test` through `tests/test_opencode_loader.py`): EX-11,
  EX-13, a missing routing file, a path outside the package root.
- Compiler tests: EX-12, EX-14, and `research`'s merged `hooks/hooks.json`.
- P-1 to P-5 recorded, and the Claude layout decision applied.
- The eval report meets the S-6 targets and shows the baseline; session start
  measured under 3 seconds.
- `python scripts/daodan_build.py --check --support`, the linters,
  `sync_plugin_docs.py --check`, `sync_codex_instructions.py --check` and
  `python -m unittest discover -s tests` pass.
- `scripts/check_version_bumps.py` fails on the range, because kernels change
  while versions stay at 1.0.0 (A-5); that result is reported, not silenced.

## Open questions

- O-1: Should `init-project` also write a routing statement into the project's
  instruction file, which every host reads, Copilot and Pi included?

## Sources

- S-1: https://code.claude.com/docs/en/skills.md (listing budget, names always
  listed, commands merged into skills).
- S-2: https://code.claude.com/docs/en/plugins-reference.md ("Prefer `skills/`
  for new plugins").
- S-3: https://raw.githubusercontent.com/obra/superpowers/main/hooks/hooks.json
  and its `hooks/session-start` script.
- S-4: https://code.claude.com/docs/en/hooks.md (`additionalContext`,
  10,000-character cap, factual wording, parallel hooks).
