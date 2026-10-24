# Performance review

```yaml
dimension: performance
reviewer: senior-review:performance-auditor
status: delivered
output_path: evals/senior-review/specialist-smoke/performance/result.md
knowledge_usage: []
gaps: []
findings:
  - file: evals/senior-review/specialist-smoke/performance/access.py
    line: 4
    severity: Medium
    confidence: 100
    confidence_rationale: The authoritative requirements explicitly define one network query per db.query call, rule out hidden batching or caching, and identify these functions as complete access paths. The source directly establishes one initial query plus one query per returned order, so the round-trip budget violation follows deterministically for N >= 2 without relying on timing estimates.
    premise: Each db.query executes one network round trip; complete page access must use at most two round trips and may return 1000 orders.
    premise_provenance: independent
    trigger: page_a returns at least two orders.
    evidence_class: derived
    evidence: page_a loads orders once at line 2 and performs one customer query per order at lines 4-5. For N orders it issues 1 + N round trips, exceeding the two-trip requirement when N >= 2 and reaching 1001 at N = 1000.
    counterevidence_checked:
      - requirements.md lines 3-8 establish valid customers, complete access paths, supporting indexes and no implicit caching, eager loading or batching. The 1000-order cap bounds amplification but still permits the violation. Supporting indexes do not remove round trips. page_b lines 9-11 already obtains the required fields through one joined query.
    consequence: A permitted full page requires 1001 network queries against the explicit budget of at most two, adding avoidable per-order database and network work.
    fix_direction: Use the existing page_b join approach for page_a, preserving the required order IDs and customer names with one query.
```

Scope: content audit of the current on-disk `requirements.md` and `access.py` in this fixture; both read completely. Requirements are authoritative. Checked both complete access paths, query count versus page size, effective bounds, caching/batching counterevidence and the existing join alternative. `page_b` meets the round-trip budget with one query; no performance finding retained for it.

Limitations: static inspection only; no database, application, probe or other runtime execution. Counts are source-derived, not measured. No timings or query plans were supplied, so latency, throughput and database execution cost are unmeasured. This is not a changeset review; introduction history was not assessed.
