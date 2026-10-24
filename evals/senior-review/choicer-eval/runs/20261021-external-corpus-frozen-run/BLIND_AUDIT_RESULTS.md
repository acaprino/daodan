# Blind code-only audit results

- Exact slot agreement across all 35 items x 8 lenses: `264/280 (94.3%)`
- Jupiter rubric gate (`>=9/11` positives and `<=2/30` explicit negatives per reader): `pass`
  - Reader 1: `11/11` positives, `0/30` explicit negatives activated
  - Reader 2: `11/11` positives, `0/30` explicit negatives activated
  - Both readers applicable: `11/11` positives

## External development positive assignments (`32` total)

| Visibility stratum | Assignments | V2 recall | Candidate recall |
| --- | ---: | ---: | ---: |
| code_supported | 9 | 2/9 (22.2%) | 1/9 (11.1%) |
| disputed_applicable | 2 | 0/2 (0.0%) | 0/2 (0.0%) |
| insufficient_or_external_only | 4 | 1/4 (25.0%) | 0/4 (0.0%) |
| code_not_applicable | 17 | 0/17 (0.0%) | 2/17 (11.8%) |

## Per-assignment breakdown

- D01 / F01 (X103, WellCommerce_WishlistBundle) `cleanup-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=False | Cand=False
- D02 / F02 (X112, WellCommerce_WishlistBundle) `cleanup-auditor` -> `insufficient_or_external_only` | R1=insufficient_evidence | R2=insufficient_evidence | V2=False | Cand=False
- D03 / F03 (X117, openlayers_openlayers) `cleanup-auditor` -> `insufficient_or_external_only` | R1=insufficient_evidence | R2=insufficient_evidence | V2=False | Cand=False
- D04 / F04 (X072, tensorflow_probability) `cleanup-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D06 / F06 (X051, FFmpeg) `security-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D08 / F08 (X057, FFmpeg) `security-auditor` -> `disputed_applicable` | R1=not_applicable | R2=applicable | V2=False | Cand=False
- D09 / F09 (X058, FFmpeg) `security-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D11 / F11 (X036, fasterxml/jackson-databind) `logic-integrity-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=True | Cand=False
- D12 / F12 (X088, grpc/grpc-go) `temporal-resilience-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=True | Cand=True
- D13 / F13 (X089, grpc/grpc-go) `data-integrity-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D14 / F14 (X025, mui/material-ui) `ui-race-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D15 / F15 (X027, mui/material-ui) `data-integrity-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D16 / F16 (X086, mui/material-ui) `ui-race-auditor` -> `insufficient_or_external_only` | R1=insufficient_evidence | R2=insufficient_evidence | V2=True | Cand=False
- D17 / F17 (X009, astropy/astropy) `distributed-flow-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D17 / F17 (X009, astropy/astropy) `logic-integrity-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=False | Cand=False
- D18 / F18 (X024, astropy/astropy) `logic-integrity-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=False | Cand=False
- D19 / F19 (X079, astropy/astropy) `data-integrity-auditor` -> `disputed_applicable` | R1=applicable | R2=not_applicable | V2=False | Cand=False
- D20 / F20 (X001, django/django) `security-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=False | Cand=False
- D20 / F20 (X001, django/django) `data-integrity-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D20 / F20 (X001, django/django) `distributed-flow-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=True
- D20 / F20 (X001, django/django) `logic-integrity-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=False | Cand=False
- D21 / F21 (X005, django/django) `data-integrity-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D21 / F21 (X005, django/django) `distributed-flow-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D22 / F22 (X074, django/django) `data-integrity-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=False | Cand=False
- D23 / F23 (X011, matplotlib/matplotlib) `ui-race-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D23 / F23 (X011, matplotlib/matplotlib) `distributed-flow-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D24 / F24 (X013, psf/requests) `distributed-flow-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=True
- D24 / F24 (X013, psf/requests) `logic-integrity-auditor` -> `code_supported` | R1=applicable | R2=applicable | V2=False | Cand=False
- D25 / F25 (X080, psf/requests) `resource-lifecycle-auditor` -> `insufficient_or_external_only` | R1=insufficient_evidence | R2=insufficient_evidence | V2=False | Cand=False
- D26 / F26 (X085, scikit-learn/scikit-learn) `data-integrity-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D27 / F27 (X022, sympy/sympy) `data-integrity-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
- D27 / F27 (X022, sympy/sympy) `distributed-flow-auditor` -> `code_not_applicable` | R1=not_applicable | R2=not_applicable | V2=False | Cand=False
