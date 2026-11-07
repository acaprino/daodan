# Coordinator brief: senior-review, shape `branch`, review id `branch-943bdc44c`

You are the coordinator of one senior-review run. Execute the method exactly as its files say, in one round, read-only. You dispatch the workers the method requires with the Agent tool; you never fix code, never re-run a review round, never widen the roster the helper computes.

## Request (verbatim, from the user)

"Rivedi il commit 943bdc44c del benchmark scope-resolution: verifica la modifica e i suoi effetti."

## Target

- Shape `branch`, variant `team-review` (no PR). Target kind: changeset. The candidate is commit `943bdc44c66dfd9782f6d38c82922a1f08783653`, base `6dd2c2bbf`. The diff to review is `git diff 6dd2c2bbf..943bdc44c`.
- Work tree: `D:/Projects/daodan/.claude/worktrees/bench-branch-943bdc44c`, a detached checkout of the candidate. Run every git and python command there. Do not create, modify or delete any file inside it: run python with `-B` and pytest with `-p no:cacheprovider`. Base-side content comes from `git show 6dd2c2bbf:<path>`.
- Git visibility: only the two refs above. Do not run `git log --all`, `git branch -a`, `git reflog`; do not read other branches or any commit after the candidate.

## Method

- The method under execution is the installed senior-review provider at `D:/Projects/daodan/plugins/senior-review` (`SENIOR_ROOT`; main checkout, commit facd9d076). Start from `skills/review-method/SKILL.md`, then `skills/review-preparation/SKILL.md` and its `references/candidate-grounding.md`, `references/team-review.md`, `references/composition.md`; `skills/review-method/references/team-review.md`; `skills/review-quality-gates/SKILL.md` and its references; `skills/review-consolidation/SKILL.md`, `references/team-review.md`, `references/learned-facts.md`; `skills/defect-taxonomy` as the method says. Scripts: `skills/review-preparation/scripts/review_roster.py` and `composition.py`, `skills/review-consolidation/scripts/review_experience.py`. The Codebase Map tool guide is `D:/Projects/daodan/plugins/codebase-map/skills/map/references/tools-guide.md`.
- The copy of `plugins/` inside the work tree is older and is not the method: read the method only from `D:/Projects/daodan/plugins/senior-review` and `D:/Projects/daodan/plugins/codebase-map`.
- Inside `D:/Projects/daodan` read nothing else: not `benchmarks/`, not `docs/`, not `README.md`, not `.codebase-map/` files by hand. Everything about the project under review is read in the work tree.
- Project instructions (AGENTS.md) for the changeset come from the base: `git show 6dd2c2bbf:AGENTS.md`.

## Codebase Map

- Prerequisite: the complete run is `daodan-lite-20261107-2` (`latest_completed` in runs.json), root `D:/Projects/daodan`, bound to revision 7bd0ff186. `benchmarks/scope-resolution/app` at that revision is identical to the base 6dd2c2bbf. Use the MCP tools `mcp__plugin_codebase-map_codebase-map__codebase_map_*` on that run id for Phase 0 and Phase 1 (symbols_at, edit_impact, graph, search, read, outline, modules, stale_callers). Start no new analysis: no create_run, resume, publish or stop.
- Known tool failures you may meet: `edit_impact` and `graph` may fail with `ModuleNotFoundError` (`edge_view`, `store_graph`). If a tool fails, record the exact error in the context file as a gap, apply the fallback the method names (text search, with `fallback: text search` beside each reference it produced), and continue. Do not repair anything.
- `review_experience.py brief` and `record` may fail (schema mismatch, missing run record). Run them where the method says; on failure record the printed error in the report's Learned facts section and continue. Do not repair anything.
- If any other step cannot proceed without changing code, stop, write what blocked you into the final report, and return.

## Output root

`OUT = D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/review-branch-943bdc44c`

Everything the review produces goes there and nowhere else: `OUT/.team-review/` (state.json, 00-scope.md, 01a-review-knowledge-leads.md, 01-context.md, 02-selection.md, 99-consolidated.md, 98-verification.md, 97-coverage-gaps.md as the method produces them), `OUT/diff.patch`, `OUT/CONTEXT.json`, `OUT/CATALOG.json`, `OUT/ROSTER.json`, `OUT/BINDINGS.json`, `OUT/PREPARED-REVIEW.json`, `OUT/DISPATCH.json`, `OUT/FACTS.json`, `OUT/jobs/<job-id>.md`, `OUT/verification/<finding>-lens<n>.md`, `OUT/tools/` for tool outputs, `OUT/scratch/` for any reproduction, and the final report `OUT/review-branch-943bdc44c.md` with the protocol envelope. Give every worker its output path under OUT. No protocol run record exists for this standalone review: say so in the report instead of inventing one.

## Environment rules

- Prefix every shell command, yours and your workers', with:
  `export TEMP="D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/tmp-review-branch-943bdc44c"; export TMP="$TEMP"; export TMPDIR="$TEMP";`
- One local process at a time: never run two python or pytest processes concurrently. Dispatch each worker in the foreground and wait for it to finish before dispatching the next one; tell each worker to run at most one local process at a time.
- Workers: dispatch them with the Agent tool. Role workers (`senior-review:<role>`) exist as agent types; where the method asks for the host's isolated-worker binding use `general-purpose`. Each worker inherits the session model. Give each worker the paths it may read (work tree, OUT files admitted by the method, `D:/Projects/daodan/plugins/senior-review` role files named by its bindings), its output path under OUT, the environment rules above, and the same git visibility limit. No worker reads another worker's output before delivering.
- Reproduction grant for Lens 1, when the method reaches it: scratch path `OUT/scratch`, runner `python -B`, base ref 6dd2c2bbf, candidate ref 943bdc44c; the work tree stays unmodified, so base and candidate copies of a file are taken with `git show <ref>:<path>` into the scratch path.

## Rules of this run

- One round: no follow-up review round after the critic, no second dispatch of a job, no fixes, no commits. If the critic recommends a follow-up, record it as a recommendation only.
- The helper decides tier, verification level and critic: run `review_roster.py compute --shape branch`, then `composition.py catalog` and `bind`, then `review_roster.py check` on the dispatch. Follow the roster; the members of the jobs come from Phase 1 Step 3 of the preparation method.
- Write the artifacts in English. Every reference carries path, line range and content version (run id or commit).

## Return

When the final report is saved, return a compact summary: verdict; each finding with severity and file:line and, for each, the question id in `01-context.md` (`## Questions`) that led to it and the context reference that question cites, or "no question" if none did; the baselines declared missing in `02-selection.md`; tier and roster; each worker dispatched with role, job or lens id, delivered/failed; every tool failure met, with its exact error text; what the method asked for that you could not do, and why. Nothing else.
