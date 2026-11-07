# Run 20261106T075152Z (run_id=bench-exp, policy v2, override {})

## C1: PASS — resolved / delimited_by_evidence
- budget: {'queries': 1, 'reads': 1, 'unique_nodes': 1, 'suppressed_duplicates': 1}
- perimetro: 1 file (required 1, precision 1.0); extra: []; residual: []
- parafrasi 1: PASS — resolved / delimited_by_evidence
- parafrasi 2: PASS — resolved / delimited_by_evidence

## C2: PASS — resolved / delimited_by_evidence
- budget: {'queries': 5, 'reads': 4, 'unique_nodes': 36, 'suppressed_duplicates': 10}
- perimetro: 4 file (required 2, precision 0.5); extra: ['packages/orders/big_module.py', 'packages/orders/service.py']; residual: []
- parafrasi 1: PASS — resolved / delimited_by_evidence
- parafrasi 2: PASS — resolved / delimited_by_evidence

## C3: PASS — resolved / delimited_by_evidence
- budget: {'queries': 2, 'reads': 0, 'unique_nodes': 6, 'suppressed_duplicates': 0}
- perimetro: 2 file (required 2, precision 1.0); extra: []; residual: []
- parafrasi 1: PASS — resolved / delimited_by_evidence
- parafrasi 2: PASS — resolved / delimited_by_evidence

## C3b: PASS — resolved / delimited_by_evidence
- budget: {'queries': 4, 'reads': 8, 'unique_nodes': 43, 'suppressed_duplicates': 5}
- perimetro: 8 file (required 1, precision 0.12); extra: ['packages/orders/api.py', 'packages/orders/big_module.py', 'packages/orders/ledger.py', 'packages/orders/notifications.py', 'packages/orders/pricing.py', 'packages/orders/service.py', 'packages/payments/__init__.py']; residual: []
- parafrasi 1: PASS — resolved / delimited_by_evidence
- parafrasi 2: PASS — resolved / delimited_by_evidence

## C4: PASS — needs_clarification / ambiguous_domain_term
- budget: {'queries': 3, 'reads': 0, 'unique_nodes': 13, 'suppressed_duplicates': 4}
- perimetro: 0 file (required 0, precision None); extra: []; residual: []
- parafrasi 1: PASS — needs_clarification / ambiguous_domain_term
- parafrasi 2: PASS — needs_clarification / ambiguous_domain_term

## C5: PASS — resolved / delimited_by_evidence
- budget: {'queries': 5, 'reads': 8, 'unique_nodes': 39, 'suppressed_duplicates': 15}
- perimetro: 7 file (required 4, precision 0.57); extra: ['packages/orders/big_module.py', 'packages/orders/inventory.py', 'packages/payments/refunds.py']; residual: []
- parafrasi 1: PASS — resolved / delimited_by_evidence
- parafrasi 2: PASS — resolved / delimited_by_evidence

## C6: PASS — incomplete / unresolved_required_link
- budget: {'queries': 5, 'reads': 6, 'unique_nodes': 16, 'suppressed_duplicates': 10}
- perimetro: 6 file (required 2, precision 0.33); extra: ['packages/orders/api.py', 'packages/orders/inventory.py', 'packages/orders/ledger.py', 'packages/orders/pricing.py']; residual: []
- parafrasi 1: FAIL — resolved / delimited_by_evidence — outcome: atteso incomplete, ottenuto resolved (delimited_by_evidence)
- parafrasi 2: FAIL — resolved / delimited_by_evidence — outcome: atteso incomplete, ottenuto resolved (delimited_by_evidence)

## C7: PASS — resolved / delimited_by_evidence
- budget: {'queries': 3, 'reads': 1, 'unique_nodes': 25, 'suppressed_duplicates': 1}
- perimetro: 1 file (required 1, precision 1.0); extra: []; residual: []
- parafrasi 1: PASS — resolved / delimited_by_evidence
- parafrasi 2: PASS — resolved / delimited_by_evidence

## C8: PASS — incomplete / budget_exhausted
- budget: {'queries': 3, 'reads': 10, 'unique_nodes': 124, 'suppressed_duplicates': 90}
- perimetro: 10 file (required 0, precision 0.0); extra: ['packages/orders/big_module.py', 'packages/orders/inventory.py', 'packages/orders/ledger.py', 'packages/orders/notifications.py', 'packages/orders/pricing.py', 'packages/orders/reporting.py', 'packages/orders/service.py', 'packages/payments/__init__.py', 'packages/payments/refunds.py', 'packages/shipping/rates.py']; residual: ['benchmarks/scope-resolution/app/packages/payments/gateway.py', 'benchmarks/scope-resolution/app/packages/orders/api.py']
- parafrasi 1: PASS — incomplete / budget_exhausted
- parafrasi 2: PASS — incomplete / budget_exhausted

## Sintesi

| Caso | Esito | Perimetro/required | Precision | Query/letture | Robusto alle parafrasi |
|---|---|---|---|---|---|
| C1 | PASS | 1/1 | 1.0 | 1/1 | sì |
| C2 | PASS | 4/2 | 0.5 | 5/4 | sì |
| C3 | PASS | 2/2 | 1.0 | 2/0 | sì |
| C3b | PASS | 8/1 | 0.12 | 4/8 | sì |
| C4 | PASS | 0/0 | None | 3/0 | sì |
| C5 | PASS | 7/4 | 0.57 | 5/8 | sì |
| C6 | PASS | 6/2 | 0.33 | 5/6 | NO |
| C7 | PASS | 1/1 | 1.0 | 3/1 | sì |
| C8 | PASS | 10/0 | 0.0 | 3/10 | sì |