# Verification

Level `critical-high` (tier small): Lens 0 and Lens 1 on Critical and High at confidence >= 50%. Severity stays the reviewer's.

| Finding | Lens 0 | Refutation target | Counterexample | Lens 1 | Evidence class | Final severity | Flag |
|---|---|---|---|---|---|---|---|
| F1 `pricing.py:19` | HOLDS, premise_form compliant | none | none | REAL, 97 | reproduced | High | verified |

Details: `verification/F1-lens0.md`, `verification/F1-lens1.md`.

Trailing counts: `unverified (cost-guard)` 0, `unverified (tier)` 3 (AL-1, AL-2, AL-3).
