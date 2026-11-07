# Scope: branch-943bdc44c

- **Request (verbatim):** "Rivedi il commit 943bdc44c del benchmark scope-resolution: verifica la modifica e i suoi effetti."
- **Shape / variant / kind / basis:** branch / team-review (no PR) / changeset / changeset (actual delta).
- **Target:** `git diff 6dd2c2bbf..943bdc44c`; candidate 943bdc44c66dfd9782f6d38c82922a1f08783653, base 6dd2c2bbf. Diff saved at `OUT/diff.patch`.
- **Work tree:** `D:/Projects/daodan/.claude/worktrees/bench-branch-943bdc44c` (detached at the candidate, read-only).
- **Intent:** The candidate changes the order-total computation in `compute_total` (benchmarks/scope-resolution/app/packages/orders/pricing.py:19 @943bdc44c) so that `compute_discount(order)` is subtracted twice from the net; the commit message "benchmark: aggiorna il calcolo in pricing.py" ("update the calculation in pricing.py") states what changes but no reason, so the *why* is `intent: unknown` (no task, PR or commit text supports one; no caller channel to ask before dispatch — carried as a question for the author).
- **Flags:** reviewers=auto, all=false, no_context=false, fast=false, rigorous=false.

## Files

| File | Status | Evidence |
|---|---|---|
| benchmarks/scope-resolution/app/packages/orders/pricing.py | modified (1+/1-) | `git diff --stat 6dd2c2bbf..943bdc44c`; hunk `@@ -16,5 +16,5 @@ def compute_discount(order):`, changed line 19 @943bdc44c (line 19 @6dd2c2bbf) |

- `conclusion_paths`: the file above. `read_scope`: that file, plus one hop of callers/callees resolved in Phase 1.
- Extensions: `.py` only. No manifest, lockfile, CSS, markup, configuration or `.github/` change.

## Governing policy

- `git show 6dd2c2bbf:AGENTS.md` (root; no nested AGENTS.md/CLAUDE.md in the tree). Rules relevant here: style/format belong to the configured linter/formatter, not to reviews; specs are tested in `benchmarks/`, each benchmark declares its parameters and measured results in its README.

## Gaps

- No protocol run record exists for this standalone review (no host run-record mechanism): preflight, snapshot validation through a run record and publication are declared unavailable.
- Codebase Map MCP tools (`mcp__plugin_codebase-map_codebase-map__codebase_map_*`) are not exposed in the coordinator session; the coordinator calls the same read-only `MapService` backend (`plugins/codebase-map/skills/map/scripts/mcp_service.py`) through `OUT/tools/map_call.py` with `python -B`.

## Pre-review work tree

`git status --porcelain` in the work tree at 2026-11-07T15:19:11Z:

```text
(empty: clean)
```

## Plan (Phase 0b)

- **Snapshot:** candidate 943bdc44c (work tree above); base 6dd2c2bbf. Map run `daodan-lite-20261107-2` (complete, `latest_completed`, repo_revision 7bd0ff186c50, created 2026-11-07T11:59:11Z, parser bbbd90a8...). Scoped freshness: the run's `raw_hash` of pricing.py (`d656c18b842129ac...`) equals the base blob; the candidate blob is `25a541956810c4f8...`, so map facts about pricing.py describe the base side only.
- **Roster:** `ROSTER.json` from `review_roster.py compute --shape branch --kind changeset --id branch-943bdc44c --stage standalone`: tier `small`, reason "no raising signal", roster `senior-review:code-auditor`, support `senior-review:premise-auditor`, verification `high-and-above`, critic `false`. 26 required specialist obligations, all leaves of `senior-review:code-auditor` (computed-roster and code-review floor).
- **Jobs:** composed in Phase 1 Step 3 (`02-selection.md`) and bound with `composition.py bind` (`PREPARED-REVIEW.json`).
- **Stack dimensions** (review-preparation `references/stack-dimensions.md`):
  - `python`: active (target is `.py`; `app/pyproject.toml`). Owner `senior-review:code-auditor` through the host isolated-worker binding; former python-development methods unavailable: declared gap.
  - `dependencies`: skip, no manifest or lockfile in the diff (`git diff --stat` lists only pricing.py).
  - `react`, `typescript`, `platform`: skip, no JS/TS/JSX file, TypeScript configuration or client-platform code in the target.
- **Knowledge:** `knowledge/selection.json` (fingerprint `af96a6fdd282cd2a...`): `senior-review:defect-taxonomy` (correctness, security) assigned to job-01; canonical catalog validation unavailable (no host catalog preparation mechanism).
- **Verification level:** `high-and-above` (Lens 0 when eligible, Lenses 1-2, Lens 3 after survival); critic not in tier.
- **Evidence pack** (candidate, read-only; outputs in `OUT/tools/`):

| Tool | Version | Command | Exit | Output |
|---|---|---|---|---|
| ruff | 0.15.20 | `ruff check --no-cache <pricing.py>` | 0 "All checks passed!" | tools/ruff-check.txt |
| ruff | 0.15.20 | `ruff format --check --no-cache <pricing.py>` | 0 "1 file already formatted" | tools/ruff-format.txt |
| vulture | 2.16 | `python -B -m vulture --min-confidence 80 <pricing.py>` | 0, no output | tools/vulture.txt |
| radon | 6.0.1 | `radon cc -s <pricing.py>` | 0; vat_amount, compute_discount, compute_total all A (1) | tools/radon.txt |
| pytest | 9.1.1 | `python -B -m pytest -p no:cacheprovider -q test_app_structures.py` on `git archive` copies (scratch/evidence-pack/{cand,base}) | 0 both: 11 passed | tools/pytest-app-structures.txt |
| mypy / pyright | absent | — | gap: install with `pip install mypy` or `pip install pyright` | — |
| complexipy | absent | — | gap: install with `pip install complexipy` (radon used) | — |

  The project declares no build, lint or test command for the app (`app/pyproject.toml` has none) and no secret scanner. No test imports `pricing`; `test_app_structures.py` only checks text and compilation (it runs `compileall`, which writes bytecode, so it was run on scratch copies).
- **Gaps:** `codebase_map_graph` failed (see 01-context.md); stale-callers unavailable (single base-side run, no candidate run; starting one not authorized); edit-impact engine store `missing_store` (lexical edges only); no protocol run record.
