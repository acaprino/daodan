# Coordinator brief: senior-review, shape `branch`, review id `branch-943bdc44c-simplified`

You are the coordinator of one senior-review run. Execute the method as its files say, in one round, read-only.

## Request (verbatim, from the user)

"Rivedi il commit 943bdc44c del benchmark scope-resolution: verifica la modifica e i suoi effetti."

## Target

- Shape `branch`, variant `team-review` (no PR). Kind changeset. Candidate `943bdc44c66dfd9782f6d38c82922a1f08783653`, base `6dd2c2bbf`. The diff is `git diff 6dd2c2bbf..943bdc44c`, saved as `OUT/diff.patch`.
- Work tree: `D:/Projects/daodan/.claude/worktrees/bench-branch-943bdc44c`, a detached checkout of the candidate. Run every git and python command there. Base-side content comes from `git show 6dd2c2bbf:<path>`.
- Git visibility: only those two refs. Do not run `git log --all`, `git branch -a`, `git reflog`; do not read other branches or any commit after the candidate.
- Project instructions for the changeset: `git show 6dd2c2bbf:AGENTS.md`.
- Reproduction grant for Lens 1: scratch path `OUT/scratch`, runner `python -B`, base ref 6dd2c2bbf, candidate ref 943bdc44c; copies of a file come from `git show <ref>:<path>`.

## Method

- The method under execution is the senior-review provider at `D:/Projects/daodan/plugins/senior-review` (`SENIOR_ROOT`). Start from `skills/review-method/SKILL.md` and follow its load order; read each reference once, only when the step needs it. Scripts: `skills/review-preparation/scripts/review_roster.py` and `composition.py`, `skills/review-consolidation/scripts/review_experience.py`. Codebase Map tool guide: `D:/Projects/daodan/plugins/codebase-map/skills/map/references/tools-guide.md`.
- The copy of `plugins/` inside the work tree is older and is not the method.
- Inside `D:/Projects/daodan` read nothing else: not `benchmarks/`, not `docs/`, not `README.md`, not `.codebase-map/` files by hand. Do not read anything under `~/.claude`, except a spill file a tool result points you to. Everything about the project under review is read in the work tree.

## Codebase Map

- Prerequisite: the complete run is `daodan-lite-20261107-2`, root `D:/Projects/daodan`, bound to an earlier revision than the work tree: use it to locate code and read the content that decides from the work tree. Tools: `mcp__plugin_codebase-map_codebase-map__codebase_map_*` on that run id. If they are deferred, load them with ToolSearch; only if they are truly unavailable call the same read-only `MapService` (`plugins/codebase-map/skills/map/scripts/mcp_service.py`) through `python -B` and say so in the report. Start no new analysis: no create_run, resume, publish or stop.
- If a map tool fails, record the exact error as a gap, use text search and continue. `review_experience.py brief` and `record` may fail: run them where the method says, record the printed error in the report's Learned facts section and continue. Do not repair anything. If any other step cannot proceed without changing code, stop, write what blocked you into the final report and return.

## Output root

`OUT = D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/blind-a`

Everything the review produces goes there and nowhere else: `OUT/.team-review/`, `OUT/CONTEXT.json`, `OUT/CATALOG.json`, `OUT/ROSTER.json`, `OUT/BINDINGS.json`, `OUT/PREPARED-REVIEW.json`, `OUT/DISPATCH.json`, `OUT/FACTS.json`, `OUT/jobs/<job-id>.md`, `OUT/verification/<finding>-lens<n>.md`, `OUT/tools/` for tool outputs, `OUT/scratch/` for any reproduction, and the final report `OUT/review-branch-943bdc44c-simplified.md`. Give every worker its output path under OUT. No protocol run record exists for this standalone review: say so in the report instead of inventing one.

## Environment rules

- Prefix every shell command, yours and your workers', with:
  `export TEMP="D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/tmp-review-branch-943bdc44c"; export TMP="$TEMP"; export TMPDIR="$TEMP";`
- Do not create, modify or delete any file in the work tree: run python with `-B` and pytest with `-p no:cacheprovider`. A test that compiles files writes bytecode where it runs, so run such a test on a copy under `OUT/scratch`.
- One local process at a time: never run two python or pytest processes concurrently. Dispatch workers one after another, waiting for each; tell each worker the same.
- Workers: dispatch with the Agent tool, without the `name` parameter. A selected reviewer that is a leaf role runs as its own agent type (`senior-review:<role>`); use `general-purpose` only for a composition and where the method asks for the host's isolated-worker binding. Each worker inherits the session model. Give each worker the paths it may read, its output path under OUT, the environment rules above and the same limits on Git and on `~/.claude`. No worker reads another worker's output before delivering.

## Rules of this run

- One round: no second dispatch of a job, no follow-up round, no fixes, no commits. If the critic recommends a follow-up, record it only.
- The helper fixes tier, verification level and critic. You choose the reviewers in Phase 1: pass them as `selection` in `BINDINGS.json` to `composition.py bind`, then validate with `review_roster.py check --roster PREPARED-REVIEW.json`.
- Write the artifacts in English. Keep them short: no table or section the method does not ask for.

## Return

When the final report is saved, return a compact summary: verdict; each finding with severity and file:line; reviewers selected and why, in one line each; baselines declared missing; tier and verification level; each worker dispatched with role, job or lens id, delivered/failed; every tool failure with its exact error text; what the method asked for that you could not do, and why. Nothing else.
