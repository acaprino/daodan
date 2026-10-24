# Mock Gutsy nomination run

Mode: `gold-replay` (runtime_identity `mock-gutsy/v1`). Offline only; no inference performed.
Metrics source: imported ../metrics.py (_role_metrics, _calibration).

Gold guards: {'gold_c_cases': 11, 'gold_c_labeled': 10, 'gold_c_activations': 23, 'teams': 12, 'team_required': 39, 'team_roles': 22}.
Answer decisions recorded: 462; tool failures: 0.
Suite2 threshold-only replay matches recorded gutsy-comparison numbers: {'0.45': True, '0.50': True, '0.55': True, '0.60': True, '0.65': True}.
Suite3 per-case selection at 0.50 matches recorded gutsy_exact_catalog_th_0.50: True.

The threshold-only replay profile (no mandatory lenses, no evidence gate) exists solely to
reproduce the recorded threshold numbers. Default nomination adds the mandatory senior-review
lenses and the evidence-binding gate; those numbers differ by design and are not claimed here.
