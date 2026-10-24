# Mock Gutsy nomination eval

Offline development asset under `evals/senior-review/choicer-eval/mock-nomination/`.
It tests the reviewer-nomination tool contract and policy with a scripted,
deterministic mock of Gutsy. It performs no inference, no network access and
no promotion: nothing here changes production reviewer selection.

## Contents

| File | Role |
| --- | --- |
| `mock_gutsy.py` | `decide(state, questions)` mock compatible with the existing `decode_answers` contract. Modes: `gold-replay` (saved probabilities from `../runs/20261020T100258Z/gutsy-comparison.json`), `oracle` (1.0 gold / 0.0 rest, fixture held inside the mock), `threshold-edge` (0.499/0.5/0.501 at the frozen 0.5 boundary), `abstain` (Z, missing option, malformed probabilities), `failure` (scripted exception). Every answer records `decision_id`, state digest, `qid`, `runtime_identity="mock-gutsy/v1"`. |
| `nomination_policy.py` | Pure policy, stdlib only, no I/O. Frozen profile: per-role threshold (default 0.5, inclusive), mandatory senior-review lenses that a low mock probability can never remove (`senior-review:code-auditor`, `senior-review:security-auditor`; dispatch table in `plugins/senior-review/skills/review-method/references/code-review.md`), Z/missing/malformed handling as ABSTAIN, minimum margin, and an explicit evidence/hunk binding requirement. Missing or failed answers are never negative votes and never fall back to the first hunk. Contains faithful replicas of `all_reviewers_eval.decode_answers` (lines 43-81) and `run_gutsy_benchmark.score_team_probs` (line 129); the latter cannot be imported stdlib-only because it imports `probe_gutsy`, which requires numpy. |
| `gold.py` | Read-only loaders with frozen count guards: 11 Gold C cases, 10 labeled, 23 expected activations; 12 teams, 39 required roles, 22 team roles. Model-visible states built here contain no gold labels, so labels never enter `decide(state, questions)`. |
| `score_mock.py` | Offline CLI. Writes only `decisions.json`, `scores.json`, `REPORT.md` into a new `mock-nomination/runs/<timestamp>/` directory and refuses to overwrite an existing one. Existing frozen `runs/` directories elsewhere are never written. Reuses `../metrics.py` (`_role_metrics`, `_calibration`) when importable, with a documented local replica as fallback. |
| `test_mock_nomination.py` | unittest suite: contract and gold guards, inclusive 0.5 threshold, mandatory-lens retention, ABSTAIN behaviour, gold-replay reproduction of the recorded Suite2 threshold numbers and Suite3 `gutsy_exact_catalog_th_0.50` selection, missing saved gold probability as ABSTAIN, full CLI runs for `--mode abstain` and aggregated `decision_id` uniqueness, and the optional work-graph bridge. |

## Corrections (independent verification)

- `--mode abstain` no longer crashes in the CLI: `score_mock.py` extracts
  probabilities only through `validate_answer`, so a qid the mock omits (or
  answers malformed / with Z) contributes no probability, is recorded as
  ABSTAIN in `team_policy_results` / `suite3_policy_results`, and never
  becomes a negative (0.0 / below-threshold) vote. Calibration receives only
  cases with a complete set of valid probabilities.
- Aggregated `decision_id` values are unique: the team and Gold C mock
  instances in `score_mock.py` share one decision counter, so the fused
  `decisions.json` cannot reuse `mock-000001`-style ids across groups.
- Gold-replay no longer invents a negative for a missing saved probability:
  `mock_gutsy.py` omits that answer (the decision is still recorded), and the
  policy marks it ABSTAIN with reason `missing_answer`.
- `scores.json` records `team_source`: which team source `gold.py` actually
  used, `teams.json` (primary) or `suite.json` (fallback), with its path and
  `fallback_used`.
- Verified runs: `runs/20261021T112245Z` (`gold-replay`, 462 decisions, 462
  unique `decision_id`, `team_source.source = teams.json`) and
  `runs/20261021T112247Z` (`abstain`, completes, 462 ABSTAIN records across
  the team and Suite3 policy results). The frozen `runs/20261021T111811Z`
  was not modified.

## Run

```powershell
python -B -m unittest discover -s evals/senior-review/choicer-eval/mock-nomination -p 'test_*.py' -v
python -B evals/senior-review/choicer-eval/mock-nomination/score_mock.py --mode gold-replay --run-dir runs/<timestamp>
```

Replace `<timestamp>` with a new directory name; an existing target aborts
instead of overwriting. Omit `--run-dir` to generate a UTC timestamp.
Other modes: `--mode oracle|threshold-edge|abstain|failure`.

## Limits

- The mock is scripted. Gold-replay reproduces recorded probabilities and the
  recorded threshold arithmetic; it is not new model evidence and says nothing
  about real Gutsy quality beyond what the frozen run already recorded.
- The threshold-only replay profile (no mandatory lenses, no evidence gate)
  exists only to reproduce those recorded numbers. The default nomination
  profile adds mandatory lenses and the evidence-binding gate, so its
  selections differ by design.
- ABSTAIN means unknown, not negative. A case with abstentions has incomplete
  coverage; the audit record lists each abstention with its reason.
- The work-graph bridge tests import the prototype
  `evals/project-lifecycle/work-graph/controller.py` by file path and drive
  nominated reviewers as `REVIEW_LENS` nodes through
  init/reserve/start/complete/finish with fixture gates in a temporary
  directory, including a `WAVE_BARRIER` that rejects a changed payload under
  the same delivery event and a start packet with invented artifact digests.
  This proves materialization in the prototype graph only. It does not prove
  real reviewer dispatch, real gate verification, or host enforcement.
- Gold labels in this asset are partial benchmark labels; absence of a role
  from `expected_roles` is a proxy negative, not proof of irrelevance.
