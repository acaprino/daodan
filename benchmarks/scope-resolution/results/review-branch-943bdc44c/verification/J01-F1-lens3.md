- Verdict: REAL
- Severity_vote: High
- Confidence: 75
- Reason: `pricing.py:19` subtracts `compute_discount` twice, so every checkout with loyalty_percent != 0 returns a wrong total through `service.py:26-30` and persists it silently to the ledger (`ledger.py:18`), which is a significant, certain correctness defect in a core money path. It is not Critical: orders with loyalty 0 are unaffected, no security boundary is crossed, nothing is lost or crashes, and the order inputs needed to recompute exist at call time.

## Created files
- D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-21468-15616718-0-134385288314645589-0/tmp/claude/97ac78b7f1ca461f/ffc3cc44-fa2a-4b57-a36e-c0ffb6e3d931/scratchpad/review-branch-943bdc44c/verification/J01-F1-lens3.md
