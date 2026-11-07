# Selection

| Reviewer | Why |
|---|---|
| `senior-review:local-correctness-auditor` | The change is arithmetic in a pure function whose returned value goes to one caller. |
| `senior-review:logic-integrity-auditor` | The value is a money amount; docstrings state a formula and the total flows through checkout into the ledger. |
| `senior-review:artifact-lifecycle-auditor` | The request asks for effects, and this code is a benchmark fixture cited by ground truth, cases, declared results and frozen outputs. |

Automatic roster superseded: `senior-review:code-auditor` and its floor. Not selected, with cause: no trust boundary, resource, concurrency, startup, delivery or interface is touched by this one expression; the persisted format of the total does not change, so `data-representation-auditor` has no conversion to check.

Unavailable competence, declared: testing specialist; Python stack baseline (former python-development methods). Knowledge selection: explicit empty; the host inventory has no classified Python or pricing review knowledge and no catalog preparation mechanism, so canonical catalog validation is unavailable.
