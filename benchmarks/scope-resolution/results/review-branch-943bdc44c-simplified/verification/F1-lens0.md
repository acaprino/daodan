- premise_verdict: HOLDS
- premise_form: compliant
- reason: pricing.py:18 states one "sconto cliente" and pricing.py:12 defines it as compute_discount; the diff leaves both unchanged and the base subtracts it once at line 19. No counterexample exists: no document or test requires a second subtraction, `net` and `loyalty_percent` are read only in pricing.py so nothing compensates, volume_discount stays in shipping (rates.py:27), and the commit message "aggiorna il calcolo" names no formula.

Searched: base and candidate pricing.py, candidate commit message, base AGENTS.md, callers and callees of compute_total and compute_discount (service.py:26, packet edit-impact-summary.json), all of app/, test_*.py, README.md, CASES.md, ground_truth.json, results/, docs/ including docs/specs/2026-11-04-*.

Present in session, not used as evidence: the user's auto-memory index and the git status snapshot mention this commit (a seeded defect, results/review-light-943bdc44c).
