- Verdict: REAL
- Confidence: 88
- Reason: At 943bdc44c `pricing.py:19` subtracts `compute_discount` twice, so for net 100 the total is 0.0 at p 50 (base 61.0), −24.4 at p 60 and −122.0 at p 100 (base 0.0), and `service.py:26-30` passes it unguarded to `ledger.py:18`, which writes any value; no document in the work tree declares a loyalty_percent range or non-positive totals as valid, and the `pricing.py:18` docstring ("netto - sconto cliente + IVA") contradicts the double discount.

## Refutation attempts
1. Framework convention: plain Python arithmetic, no framework idiom; nothing makes a double subtraction or non-positive total correct by design.
2. Intentional design: commit message "aggiorna il calcolo" gives no rationale; docstring `pricing.py:18` still states a single customer discount; `service.py:1-6`, `api.py:1-7`, `ledger.py:13-14` describe totals as VAT-inclusive amounts; CASES.md, ground_truth.json, README.md and tests name no loyalty range nor allow negative totals. Not intentional.
3. Preexisting excluded by base policy: base `pricing.py:19` subtracts once, so non-positive totals required p ≥ 100 (zero at 100, negative above); the candidate moves the threshold to p ≥ 50, so 50 ≤ p < 100 is introduced by the diff. The finding already scopes the preexisting part (missing guard, p > 100) out.
4. Misunderstanding of behavior: recomputed net 100 cases (p 50: 100−50−50=0 → 0.0; p 60: −20 + VAT −4.4 = −24.4; p 100: −100 + −22 = −122.0; base p 50: 50+11=61.0); `DefaultPipeline.step` (`service.py:13-15`) runs after the total and only sets `validated`; `Dispatcher._invoke` (`api.py:25-27`) passes the payload as is; `ledger.record` (`ledger.py:13-22`) has no check. Only nuance: with odd-cent nets at exactly p 50 per-call rounding can leave +0.01 (e.g. net 0.03), already covered by "up to cent rounding"; it does not refute the claim.

## Created files
- OUT/verification/J01-F2-lens2.md
