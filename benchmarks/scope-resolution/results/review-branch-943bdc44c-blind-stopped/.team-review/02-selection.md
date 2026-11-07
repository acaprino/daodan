# Selection: branch-943bdc44c-simplified

Tier `small`, verification `critical-high` (Lens 0 and Lens 1 on Critical and High), no critic: fixed by `review_roster.py`.

## Selected, each on the whole scope

| Reviewer | Why |
|---|---|
| `senior-review:local-correctness-auditor` | The change is one arithmetic expression; its mandate is values, arithmetic and the returned outcome against the local contract and callers. |
| `senior-review:logic-integrity-auditor` | The request asks for the effects; its mandate is money rules across components, here `compute_total` through `checkout` and the dynamic callback to the ledger. Scoped semantic context is in `01-context.md`. |

## Considered, not selected

| Reviewer | Why not |
|---|---|
| `senior-review:api-contract-auditor` | No formal boundary or schema in scope; the signature is unchanged and the docstring rule belongs to logic integrity. |
| `senior-review:data-representation-auditor` | The commit changes no stored format, type or rounding step; the ledger line format is untouched. |
| Automatic `code-auditor` floor (security, data integrity, distributed, temporal, resource and other families) | The diff has no signal for them: no boundary, I/O, persistence or concurrency code changed. Superseded by this selection. |

## Needed competence that is unavailable

- Python baseline: the target is `.py`; the former python-development methods are not in the base. Declared gap.
- Testing specialist: not in the base. The absence of an amount test is reported as a gap unless a reviewer reports it under its own mandate.
- Knowledge selection: explicit empty selection (`""`): the available host skills hold no pricing or domain knowledge for this scope. No catalog preparation mechanism exists, so canonical catalog validation is unavailable.
