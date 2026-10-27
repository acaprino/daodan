# Campaign module contract

Canonical design: `docs/gutsay/gutsy-campaign-design-2026-10-26.md`.
This evaluation does not modify production owners or the completed pilot.
User authorization covers this campaign, CPU only, up to 50,000 model questions,
22 hours global elapsed remote work and USD6 operational budget. No commits,
training, private uploads or live tool side effects.

Each domain owns `<domain>_campaign.py` and `test_<domain>_campaign.py`.
Use Python standard library and existing pinned upstream owners where suitable.

`build_cases(source_dir: Path | None = None) -> list[dict]` returns base cases:

```json
{"id":"routing-0001","domain":"routing","family_id":"explicit-edit",
 "provenance_id":"synthetic-explicit-edit","split":"development",
 "provenance":{"kind":"controlled_synthetic","public":true,"source":null,
 "revision":null,"license":null,"transformations":[],"label_basis":"..."},
 "arms":[{"id":"R1","state":{},"questions":{}}],"oracle":{}}
```

Case IDs and oracle stay outside the model body. An arm is just state/questions;
model requests use the fixed official model ID. Same family/provenance episode
and every perturbation stay in one split. Use `development`, `calibration`,
`verification`; independent groups approximately 20/20/60 percent. Source
records carry exact URL/revision/license/artifact hash. Missing gold is explicit.
600 scenarios per domain is an acquisition target, never a reason to pretend
name substitutions are independent families. Report actual family counts.

`build_auxiliary(cases) -> list[dict]` returns robustness and other domain
diagnostics with the same schema plus `block`, `base_case_id` and related family.
Robustness target: up to 120 verification cases x 4 meaningful perturbations,
fixed arms R3/T1/C1-Q1. Compaction also supplies 24 joint episodes, max four pairs.

`score_case(case, responses: dict, policy: dict | None = None) -> dict` takes
responses keyed by arm ID; each is the complete official HTTP response or null.
Returns `strategies` keyed by procedure, including the zero-model baseline.
Each strategy includes `eligible`, `success` (bool or null when no oracle),
`critical_errors`, `fallback`, `utility_cost` (bytes/retained bytes/error count),
and domain-specific diagnostics. Missing/invalid responses are not successes.
Do not use fallback success as credit for raw predictions. Preserve all eligible
cases in reported denominators and all oracle-labelled fields in paired contrasts.

`policy_candidates() -> list[dict]` exposes the finite preregistered calibration
grid including conservative baselines; `select_policy(cases, responses_by_case)`
chooses using calibration only and returns the policy plus selection evidence.
Frozen verification does not change prompts, grids or policy. `score_case` must
support the selected policy without mutating cases or raw responses.

All data must be public-approved or generated synthetic; no local private code
or credentials. Tests protect label reasoning, policy selection, split grouping,
invalid response behavior and actual owner integration. Review oracles without
seeing model answers. Any unavailable requested dimension remains explicit.
