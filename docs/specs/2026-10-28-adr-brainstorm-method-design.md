# Decision records as the project method during brainstorming

Status: draft for approval, 2026-10-28, revision 2 after the claim review.

## Problem

The owner reported on 2026-10-28 that the decision-record working mode never
activates, on new projects or existing ones. Observed causes:

1. The Daodan brainstorm only reads records: `brainstorm.md:10-11`
   (`plugins/project-delivery/skills/delivery-method/references/`) runs
   `resolve`, then writes a specification under `docs/specs/`; it never proposes
   a record. Since commit `457bdd89a` (2026-10-26) the task interview writes one
   only "when a separate technical decision needs an ADR" (`interview.md:34`),
   a judgment without a criterion; before it, the interview always proposed one.
2. `adr-method`'s description (`SKILL.md:6`) says DO NOT TRIGGER WHEN "the user
   only wants brainstorming or advice without recording a decision".
3. A free brainstorming conversation can be taken by a brainstorming skill of
   another plugin that writes its own specifications and knows nothing of records
   (janura-code: 31 such specifications, no record).
4. Records are off by default (`first-use.md:12`, ADR-0005) and turn on only
   through the first-use question or `/daodan:record-decision`.
5. On hosts that start plugin MCP servers (Claude, OpenCode), the work-controller
   server creates `.daodan/` at session start (`work_controller/cli.py:24, 62-64`),
   so the first-use probe (`run_state.py:100-111`) returns `first_use: false` and
   asks nothing. Reproduced in a scratch repository: probe `true`, start
   `controller.py mcp`, probe `false`.

## Owner decisions (2026-10-28)

- The mode works automatically while brainstorming products or features, with no
  Codebase Map, run or other Daodan state required.
- On by default; the first time in a project the user is asked whether to use
  records as the project's method. A no is never asked again in that project, and
  the answer says how to turn records back on.
- ADRs already present in any directory, or FRDs, make the mode active without
  asking. ADR and FRD are the only record kinds; no other document counts.
- It works whatever brainstorming method runs, including another plugin's.

## Behavior

**Project state.** `adr_tool.py state --project ROOT` reads only and returns one of:

- `active`: Daodan's index `docs/adr/README.md` exists (an empty index counts),
  the FRD index `docs/frd/README.md` exists, or the project holds foreign ADRs:
  a directory named by a `.adr-dir` file (adr-tools), or a directory named `adr`,
  `adrs`, `decisions` or `architecture-decisions` holding a file matching
  `(ADR-)?NNNN-*.md`. With Git the search reads `git ls-files`, so ignored paths
  never count; without Git it walks at most six levels, skipping dot directories
  and `node_modules`, `vendor`, `dist`, `build`, `target`, `__pycache__`. Foreign
  directories are returned as `foreign` paths.
- `declined`: `git config --local --get daodan.decisionRecords` is `declined`, or,
  outside Git, `.daodan/adr-declined` exists in the project.
- `undecided`: neither.

**Where records live.** New records always go to `docs/adr/` through the existing
helper, so every caller that reads `docs/adr/README.md` stays valid. On an
`active` project without that index, the first settled decision runs `init-index`
without a question. Foreign records are read as constraints and never written.

**Session hook.** project-delivery declares an optional `session-start` hook,
`skills/adr-method/scripts/adr_hook.py` (timeout 10 s), that calls `state` and adds
context for the main model. It writes nothing. The context names no other plugin.

- `active`: when a product or feature brainstorming settles a decision, whatever
  method is running, record it as a `Proposed` record through
  `project-delivery:adr-method`, show it, promote it only on approval; foreign
  records in the listed paths are constraints.
- `undecided`: at the first decision settled in such a brainstorming, ask once
  whether to use decision records as this project's method, yes by default.
- `declined`: no context.

**The question.** Asked once, at the first settled decision, never at session
start. Yes: `init-index` (commit of the index alone when the project has a commit)
and the decision becomes the first record. No: `adr_tool.py decline` stores the
answer, and the reply says that `/daodan:record-decision` turns records back on.
`init-index` clears a stored decline.

**Recording without Daodan.** Capture needs only the helper; a Daodan run, map,
first-use probe or research checkpoint is used when present, never required.
`--task` takes the run identity or the brainstorm's slug. Each record carries the
chosen approach, rejected alternatives with reasons, invariants, at least one
agreed example and a non-empty scope (domains suffice before code exists), as the
helper requires. `--sha` takes the resolved `HEAD` hash; when the project has no
commit, `propose` and `promote` accept no sha and record `null`.

**Daodan methods.** `brainstorm.md` and the task interview point at adr-method's
capture rule instead of the criterion at `interview.md:34`. `first-use.md` keeps
only the analysis question. The first-use probe drops its `records` field and
counts `.daodan/runs/` instead of a bare `.daodan/`, so neither the MCP store nor
a decline marker silences the analysis question.

## Unit edits within the word caps

No cap is raised (`tests/test_skill_load_budget.py`); each edit replaces text.

- `adr-method/SKILL.md` (409/412): the research paragraph (lines 37-40) leaves,
  because `brainstorm.md` and `interview.md:15-18` already compose that
  checkpoint; line 11 becomes "inside a Daodan run"; the description drops the
  brainstorming exclusion and triggers on a settled product or feature decision;
  a capture section holds the three states and the question; the load map gains
  `state` and `decline` and loses the "First use" row.
- `interview.md` (274/275): lines 34-37 become one sentence pointing at
  adr-method's capture rule, keeping "do not duplicate the full design into an
  ADR"; line 11 drops "With decision records,".
- `brainstorm.md` (196/200): "With decision records, load ... `resolve` the
  scope; name conflicts" becomes "load `project-delivery:adr-method`: `resolve`
  the scope, name conflicts and capture each settled decision".
- `first-use.md`: the records question and step 3 leave.
- `record-decision.md`: "This command implies yes to decision records, so it
  asks only about the analysis" leaves.

## Examples

- EX-1 New Git project, no records; a brainstorm settles "store sessions in
  Redis". Asked once, the user answers yes: `docs/adr/README.md` and
  `ADR-0001-store-sessions-in-redis.md` (`Proposed`) exist and are shown.
- EX-2 Same, the user answers no: `daodan.decisionRecords=declined` in the local
  Git config, the reply names `/daodan:record-decision`, and later sessions add
  no context and ask nothing.
- EX-3 Project with `doc/adr/0001-use-postgres.md` (adr-tools): no question; the
  next settled decision creates `docs/adr/ADR-0001-<slug>.md`; `0001` is
  untouched and cited as a constraint.
- EX-4 Project with only `docs/frd/README.md`: no question; the first settled
  decision runs `init-index` and becomes `docs/adr/ADR-0001-<slug>.md`.
- EX-5 A brainstorm that only explores and settles nothing: no question, no file.
- EX-6 A declined project runs `/daodan:record-decision`: the decline is cleared
  and the index is created.
- EX-7 Empty folder without Git, answer no: `.daodan/adr-declined` exists and the
  first-use probe still returns `first_use: true`.

## Invariants

- INV-1 The question is asked at most once per project checkout.
- INV-2 A record becomes `Accepted` only on approval of its exact text (ADR-0004).
- INV-3 The hook and `state` write nothing.
- INV-4 Capture requires no map, run, first-use probe or research checkpoint.
- INV-5 Foreign record files are never written.
- INV-6 New records live only in `docs/adr/`.

## Rejected alternatives

- RA-1 Off by default, chosen at first use (ADR-0005): it never ran.
- RA-2 Only the Daodan brainstorm records decisions: it misses other plugins'
  brainstorming.
- RA-3 A prompt hook matching brainstorming keywords: fragile with dictated
  Italian; one session-start context is enough.
- RA-4 Writing new records into a foreign directory: needs foreign numbering and
  README handling, breaks INV-5 and every caller of `docs/adr/README.md`.
- RA-5 A decline marker under `.daodan/` in Git projects: needs main-checkout
  resolution owned by work-controller and an ignore rule nobody guarantees; the
  local Git config is shared by worktrees and never committed.
- RA-6 A committed decline marker: a no would need its own commit.

## Hosts

Claude and Codex register the hook through the generated `hooks/hooks.json`,
OpenCode through its loader; `hooks.lifecycle` is declared optional. Copilot and
Pi have no native interception: there the rule lives in `brainstorm.md`, the
interview and adr-method, so another plugin's brainstorming on those hosts is
not covered.

## Scope

- project-delivery: `plugin.toml` (hook, optional `hooks.lifecycle`, minor
  version); `adr_hook.py` (new); `adr_tool.py` (`state`, `decline`, `init-index`
  clears a decline, no-sha `propose`/`promote` without a commit); adr-method
  `SKILL.md`; `brainstorm.md`, `interview.md`, `first-use.md`.
- work-controller: `run_state.py` probe (`records` removed, `.daodan/runs/`).
- daodan: `record-decision.md`.
- Docs and evals: `docs/decision-records.md`, `docs/plugins/project-delivery.md`,
  `evals/project-lifecycle/cases.md` cases `first-use-choices` and
  `records-off-cycle` rewritten to this behavior.
- Records: ADR-0005 is `Proposed`, so it cannot take a version 2; it is retired
  as superseded by the owner's 2026-10-28 decision, and ADR-0008 records this
  decision for separate approval.
- Tests: helper `state`/`decline`/no-sha, hook output per state, probe, word caps.

Known limit: reviews and other callers read only `docs/adr/`, so foreign records
constrain brainstorming and interviews but not reviews.
