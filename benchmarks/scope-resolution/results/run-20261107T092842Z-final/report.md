# Run 20261107T092842Z (run_id=bench-2, resolver policy v3)

## C1: FAIL — resolved / delimited_by_evidence
- perimetro 1 (required 2, precision 1.0, recall 0.5); extra: []; budget 1q/1r
- **FAIL** [fixture] required: manca benchmarks/scope-resolution/app/packages/orders/service.py

## C2: PASS — resolved / delimited_by_evidence
- perimetro 4 (required 2, precision 0.5, recall 1.0); extra: ['packages/orders/big_module.py', 'packages/orders/service.py']; budget 5q/4r

## C3: PASS — resolved / delimited_by_evidence
- perimetro 2 (required 1, precision 0.5, recall 1.0); extra: ['packages/shipping/__init__.py']; budget 2q/0r

## C3b: PASS — resolved / delimited_by_evidence
- perimetro 7 (required 1, precision 0.14, recall 1.0); extra: ['packages/orders/api.py', 'packages/orders/big_module.py', 'packages/orders/ledger.py', 'packages/orders/pricing.py', 'packages/orders/service.py', 'packages/payments/__init__.py']; budget 4q/7r

## C4: PASS — clarify / ambiguous_domain_term
- perimetro 0 (required 0, precision None, recall None); extra: []; budget 3q/0r

## C5: PASS — resolved / delimited_by_evidence
- perimetro 7 (required 4, precision 0.57, recall 1.0); extra: ['packages/orders/big_module.py', 'packages/orders/inventory.py', 'packages/payments/refunds.py']; budget 5q/8r

## C6: PASS — partial / unresolved_required_link
- perimetro 6 (required 2, precision 0.33, recall 1.0); extra: ['packages/orders/api.py', 'packages/orders/inventory.py', 'packages/orders/ledger.py', 'packages/orders/pricing.py']; budget 5q/6r

## C7: PASS — resolved / delimited_by_evidence
- perimetro 1 (required 1, precision 1.0, recall 1.0); extra: []; budget 3q/1r

## C8: PASS — partial / budget_exhausted
- perimetro 10 (required 2, precision 0.2, recall 1.0); extra: ['packages/orders/big_module.py', 'packages/orders/inventory.py', 'packages/orders/ledger.py', 'packages/orders/reporting.py', 'packages/orders/service.py', 'packages/payments/__init__.py', 'packages/payments/gateway.py', 'packages/shipping/rates.py']; budget 3q/10r

## Sintesi

| Caso | Esito | Perimetro/required | Precision | Recall | Query/letture |
|---|---|---|---|---|---|
| C1 | FAIL | 1/2 | 1.0 | 0.5 | 1/1 |
| C2 | PASS | 4/2 | 0.5 | 1.0 | 5/4 |
| C3 | PASS | 2/1 | 0.5 | 1.0 | 2/0 |
| C3b | PASS | 7/1 | 0.14 | 1.0 | 4/7 |
| C4 | PASS | 0/0 | None | None | 3/0 |
| C5 | PASS | 7/4 | 0.57 | 1.0 | 5/8 |
| C6 | PASS | 6/2 | 0.33 | 1.0 | 5/6 |
| C7 | PASS | 1/1 | 1.0 | 1.0 | 3/1 |
| C8 | PASS | 10/2 | 0.2 | 1.0 | 3/10 |