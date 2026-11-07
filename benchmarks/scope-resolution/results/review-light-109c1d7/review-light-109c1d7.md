# Light review `light-109c1d7`

## Verdict

**BLOCK.** One eligible High finding (F1), verified by both lenses (Lens 0 HOLDS,
Lens 1 REAL, confidence 98, `reproduced`). The isolated coordinator could not dispatch
(no Agent tool for sub-agents in this host); the parent session dispatched the saved
brief `jobs/job-01.brief.md` unchanged and the two lenses as separate isolated
sub-agents, mutually blind. Sub-agents in total: 4 (coordinator, reviewer, two lenses).

## Target and basis

- Request: "Rivedi il commit 109c1d7 del benchmark scope-resolution: verifica la modifica e i suoi effetti."
- Shape `light`, kind `changeset`, basis `changeset`, stage `standalone`, scope_id `light-109c1d7`.
- Candidate `109c1d7e07b5e594a1bc3310f14f20df8f926b92` (HEAD of `bench-light-27`, clean tree); base `2889c58ebb08bb047077a01ac97f0f686fac3dab` (parent). Diff: `diff.patch` (1 file, +1/-1).
- Intent: the commit changes `compute_total` in `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` so that `compute_discount(order)` is subtracted twice from the net before VAT; the commit message ("benchmark: aggiorna il calcolo in pricing.py") gives no reason. The user asks for the change and its effects on the code that uses it.
- Governing policy: `git show 2889c58:AGENTS.md`; no nested `AGENTS.md`/`CLAUDE.md` at the base.
- Conclusion scope: `pricing.py`. Read scope (one hop, by `git grep`): `app/packages/orders/service.py:26` (`OrderService.checkout`, the only caller of `compute_total`; the total then goes to `ledger.record`), `test_app_structures.py`, `app/pyproject.toml`.
- Roster (computed, `ROSTER.json`): rigor `standard`, roster `senior-review:code-auditor`, support `senior-review:premise-auditor`, verification `critical-high`, critic `false`, reasons `no raising signal`. `PREPARED-REVIEW.json`: one bound job `job-01` (27 leaf members, body `a8660b6e…`), `review_roster.py check` conforms.

## Tools first

| Tool | Version | Command (cwd `benchmarks/scope-resolution`) | Exit | Output |
|---|---|---|---|---|
| pytest | 9.2.0 (Python 3.13.18) | `python3 -B -m pytest -q -p no:cacheprovider` | 0 | `46 passed, 1 xfailed in 5.28s` (`tools/pytest.txt`) |
| lint / format / types | not configured | — | — | gap: `app/pyproject.toml` declares no tool; `ruff`, `mypy`, `pyright` binaries exist on the machine but were not run (no project configuration); to exercise them: `ruff check benchmarks/scope-resolution/app`, `mypy benchmarks/scope-resolution/app/packages` |
| dependency audit | n/a | — | — | no manifest changed |

Evidence strength of the green run: `git grep compute_total` finds no test calling it;
the only test touching `pricing.py` (`test_app_structures.py:71`) asserts the string
`def compute_discount(`. The tool result therefore does not exercise the changed line.
No red result to preserve as `tool-reported`.

## Findings and verification

### F1 (High): `compute_total` subtracts the customer discount twice

- `benchmarks/scope-resolution/app/packages/orders/pricing.py:19`; introduced by the candidate; evidence class `reproduced`; confidence 95 (reviewer), 98 (Lens 1).
- Owner `senior-review:local-correctness-auditor`; also applied by `logic-integrity-auditor` (unkept postcondition, money rule `[MAP-GAP]`) and `data-representation-auditor` (persisted total). 27 members delivered, 0 failed (`jobs/job-01.md`).
- Trigger: any order with `loyalty_percent > 0` through `OrderService.checkout` (`service.py:26`, sole caller). Net 100 at 10% gives 97.6 instead of 109.8; at 50% gives 0.0; at 60% gives -24.4. The wrong total is returned and appended to `ledger.log` via `ledger.record`.
- Premise: the documented rule at `pricing.py:18` requires the customer discount to be subtracted exactly once.
- Fix direction: restore the base line; if a second concession is intended, give it its own function, docstring and a numeric test.

| Finding | Lens | Worker | Result | File |
|---|---|---|---|---|
| F1 | Lens 0 (premise-auditor Mode 2) | isolated sub-agent | HOLDS, premise_form compliant; the only other discount (`shipping/rates.py:15`) applies to the shipping rate | `verification/F1-lens0.md` |
| F1 | Lens 1 (Reachability / Correctness) | isolated sub-agent, reproduction grant | REAL, confidence 98, `reproduced`: scratch test passes on 2889c58, fails on 109c1d7 | `verification/F1-lens1.md` |

Lenses ran isolated and blind to each other. Lower severities: none.

## Preexisting issues

None reported (no reviewer ran).

## Gaps and advice

1. Isolated-worker binding unavailable: discovery job not delivered, Lens 1 unavailable, Lens 0 not run. Mandatory coverage missing.
2. Codebase Map unavailable (no map run, no MCP server, no `codebase_map_*` tools): `symbols-at`, `edit-impact`, `stale-callers` recorded as gaps; fallback `git grep` found one caller (`service.py:26`). The diff's hunk header names `compute_discount`; the changed line 19 is inside `compute_total` (17-20).
3. Protocol `review` run record unavailable: no `.daodan` project home; run-record preflight, baseline and candidate gates unavailable; the review is recorded only in this directory.
4. No linter, formatter or type checker configured (see Tools).
5. Roster gaps, verbatim: `no Codebase Map impact packet: callers and digest changes unknown`; `stale-callers schema or base/candidate snapshot binding unavailable or mismatched`; `unmatched content signals have unknown applicability; preparation must ground skip decisions`.
6. Roster advice, verbatim: `required specialist obligations must fit the single discovery; otherwise review-branch is required`.
7. Knowledge selection: explicit empty (`""`); no host skill inventory bound; knowledge validation is a declared gap.

Standalone review: any fix remains the user's decision. To complete this review,
rerun it in a host that supplies an isolated-worker binding (Agent tool) and dispatch
`jobs/job-01.brief.md` unchanged.

## Questions for the author

- `benchmarks/scope-resolution/app/packages/orders/pricing.py:19`: which pricing rule motivates subtracting the customer discount twice? The docstring at `pricing.py:18` still states "netto - sconto cliente + IVA" and the commit message gives no reason; the review could not verify the intent without a reviewer.
- `benchmarks/scope-resolution/test_app_structures.py:71`: no test asserts a value of `compute_total`; is a value oracle for this benchmark fixture intentionally absent?

## Learned facts

- (a) facts used: none.
- (b) findings declined by learned fact: none.
- (c) ended facts: `ledger not written (error: the project home has no .daodan with a .daodan-root sentinel)` (`tools/learned-facts-record.txt`).
- (d) `unavailable (no discovery job in the prepared roster)`: `brief` printed this gap and 0 facts (`tools/learned-facts-brief.txt`, `FACTS.json`). Cause, from reading the scripts: `review_experience.py` `discovery_jobs` (line 296-307) selects jobs with `id` and `input_mode == "discovery"`, while `composition.py bind` writes `job_id` and `input_mode: "independent"`; the two plugin scripts disagree, so the ledger would stay unavailable even with a project home.
- (e) rows_skipped: n/a (`record` did not write); 0 findings to persist.

## Protocol envelope

```json
{
  "review_id": "light-109c1d7",
  "shape": "light", "kind": "changeset", "review_basis": "changeset", "stage": "standalone",
  "candidate": "109c1d7e07b5e594a1bc3310f14f20df8f926b92", "base": "2889c58ebb08bb047077a01ac97f0f686fac3dab",
  "verdict": "BLOCK",
  "retained_findings": ["F1"], "filtered_findings": [],
  "coverage": {"expected_jobs": 1, "delivered": 1, "failed": 0, "not_dispatched": [],
               "reason": "job-01 dispatched by the parent session from the saved brief", "tools": {"pytest": "exit 0"}},
  "degraded_dimensions": [],
  "delivery_ledger": {"expected": 1, "delivered": 1, "failed": 0, "barrier_satisfied": true,
                      "checks": [{"lens": 0, "status": "HOLDS"}, {"lens": 1, "status": "REAL"}]},
  "knowledge_coverage": {"knowledge_selection": "", "status": "no host inventory; validation gap"},
  "learned_facts": {"brief": "unavailable (no discovery job in the prepared roster)", "record": "ledger not written"},
  "run_record": "unavailable (no .daodan project home)",
  "output_path": "benchmarks/scope-resolution/results/review-light-109c1d7/review-light-109c1d7.md",
  "artifacts": ["diff.patch", "numstat.txt", "CONTEXT.json", "CATALOG.json", "ROSTER.json", "BINDINGS.json",
                "PREPARED-REVIEW.json", "DISPATCH.json", "FACTS.json", "jobs/job-01.brief.md", "jobs/job-01.md",
                "verification/STATUS.md", "verification/F1-lens0.md", "verification/F1-lens1.md", "tools/pytest.txt", "tools/learned-facts-brief.txt", "tools/learned-facts-record.txt"]
}
```
