# J01-F2 — Lens 3 (Severity Calibration)

- Verdict: REAL
- Severity_vote: Medium
- Confidence: 75
- Reason: The double subtraction at `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` lowers the zero-total threshold from p > 100 to p ≥ 50, and `service.py:26-28` passes the value unchecked to `ledger.py:18`, which writes zero or negative totals into the accounting ledger; the impact is real financial-record corruption, but it is partial and conditional on loyalty_percent ≥ 50 (an atypical value for a loyalty discount), and it is removed by fixing the shared root line, so "possible, partial impact" fits Medium rather than High.

## Calibration notes
- Impact: wrong-sign monetary records in the ledger (`ledger.py:13-22` appends `id\ttotal` with no validation); no data loss, no security effect, no crash.
- Likelihood: requires p ≥ 50; for 0 < p < 50 the total is wrong but positive (that is the separate double-discount finding, not this one).
- Workaround: correcting `pricing.py:19` restores the base threshold; a range check before `ledger.record` (`service.py:28`) also contains it.
- Not Low: the zero/negative range 50 ≤ p ≤ 100 is newly reachable through the public `Dispatcher.handle("checkout", ...)` path (`api.py:29-31`, `api.py:37`), with no guard anywhere in scope.

## Created files
- OUT/verification/J01-F2-lens3.md
