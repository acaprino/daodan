# Verification: branch-943bdc44c

Panel per `senior-review:review-quality-gates` `references/verification-panel.md`. Required level from the roster: `high-and-above`; 2 consolidated findings above the 50 confidence floor (≤ 25), so both were verified. Cost guard: not triggered. Lens 0: `senior-review:premise-auditor` Mode 2 (both premises carry the negative quantifier "no"). Lenses 1-3: host isolated-worker binding `general-purpose`, one fresh context per lens per finding, no peer findings. Lens 1 reproduction grant: scratch `OUT/scratch/<finding>-lens1/`, runner `python -B`, base 6dd2c2bbf, candidate 943bdc44c.

| Finding | Lens 0 | Lens 1 | Lens 2 | Lens 3 | Final severity | Flag |
|---|---|---|---|---|---|---|
| J01-F1 `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` | HOLDS; premise_form compliant | REAL, 97, **reproduced** | REAL, 92 | REAL, severity_vote High, 75 | High | verified |
| J01-F2 `benchmarks/scope-resolution/app/packages/orders/pricing.py:19` | HOLDS; premise_form **non-compliant** (stated "returns a negative value" for every net > 0 is false by cent rounding: net 0.02, p 60 gives 0.0, `pricing.py:14,19,20`); re-derived minimal premise "some reachable order with net > 0 and 50 ≤ p ≤ 100 gets a total ≤ 0 while base gives > 0, and nothing on the default dispatch path rejects or clamps it" HOLDS | REAL, 97, **reproduced** | REAL, 88 | REAL, severity_vote Medium, 75 | Medium | verified |

`unverified (cost-guard)`: 0. Filtered: 0. Premise-refuted: 0. Contested: 0. Premise-contested: 0.

## Reproductions (Lens 1)

- J01-F1: `Dispatcher.handle("checkout", {"id": "o1", "sku": "A", "qty": 1, "net": 100, "loyalty_percent": 10})` after `register_defaults()`, from `git archive` copies of each ref, run from scratch working directories with `ORDER_NOTIFY_HANDLERS="email_receipt=builtins:id"` (no-op stub, identical on both refs). Base: returned 109.8, ledger `o1\t109.8`, PASS, exit 0. Candidate: returned 97.6, ledger `o1\t97.6`, `AssertionError: FAIL: got 97.6, expected 109.8`, exit 1. Without the env variable both refs raised `KeyError: 'ORDER_NOTIFY_HANDLERS'` at `notifications.py:13`, after the ledger write (`service.py:28`), so the wrong total was already recorded. Details: `verification/J01-F1-lens1.md`.
- J01-F2: same path, net 100, p 50 / 60 / 75 / 99: base records 61.0 / 48.8 / 30.5 / 1.22; candidate records 0.0 / −24.4 / −61.0 / −119.56 (p 100 printed only: base 0.0, candidate −122.0). Stub `ORDER_NOTIFY_HANDLERS=email_receipt=noop_notify:send` on both refs. Details: `verification/J01-F2-lens1.md`.
- Both lenses removed their test files and copies; their scratch directories are empty; the work tree `git status --porcelain` stayed empty.

## Lens deliveries

| Delivery | Worker | Output | Status |
|---|---|---|---|
| J01-F1 Lens 0 | senior-review:premise-auditor | verification/J01-F1-lens0.md | delivered |
| J01-F1 Lens 1 | general-purpose | verification/J01-F1-lens1.md | delivered |
| J01-F1 Lens 2 | general-purpose | verification/J01-F1-lens2.md | delivered |
| J01-F1 Lens 3 | general-purpose | verification/J01-F1-lens3.md | delivered |
| J01-F2 Lens 0 | senior-review:premise-auditor | verification/J01-F2-lens0.md | delivered |
| J01-F2 Lens 1 | general-purpose | verification/J01-F2-lens1.md | delivered |
| J01-F2 Lens 2 | general-purpose | verification/J01-F2-lens2.md | delivered |
| J01-F2 Lens 3 | general-purpose | verification/J01-F2-lens3.md | delivered |
