# Stack finding integration

Each specialist keeps its canonical native report. Request the existing
senior-review evidenced-finding fields for each review finding alongside that
report: file, line, evidence, severity, confidence (0-100), falsifiable premise and
premise_provenance. Preserve source role, native severity and the raw report
reference. Confidence describes support for the finding, not impact or priority;
include the evidence supporting that assessment. Never derive confidence from a
specialist's priority label.

Normalize severity into the existing review vocabulary before filtering, sorting
or applying gates. These defaults reflect the canonical roles' declared meanings;
they are provisional until evidence-based severity calibration:

| Provider | Native severity | Review severity |
|---|---|---|
| react-development | CRITICAL (immediate performance issue) | High |
| react-development | IMPORTANT (before-production improvement) | Medium |
| react-development | IMPROVEMENT (optional optimization) | Low |
| platform-engineering | Critical (security breach, data loss or outage risk) | Critical |
| platform-engineering | Warning (fragility or missed optimization) | Medium |
| typescript-development | Critical, High, Medium or Low | Same severity |

Preserve the original label in native_severity when the mapping changes it. A
reviewer can justify a different review severity with concrete user impact and the
evidence required by review-quality-gates. Missing measurements do not establish a
quantitative performance claim. Shared-premise agreement raises neither confidence
nor severity; deduplication keeps the independent evidence and distinct failure modes.

An unknown native label or missing required field is incomplete finding data, not
a low-confidence finding, an empty delivery or a reason to bypass verification.
Request completion from that worker once without another independent review. If
it remains incomplete, mark the delivery failed, preserve the raw findings in a
clearly unverified section and report the format/evidence gap. Do not invent a
numerical confidence or silently discard an important reported issue. A lifecycle
gate cannot pass on a failed mandatory delivery. Valid findings join the same
confidence filtering, deduplication and verification as the other dimensions.

# Scoped knowledge usage

The coordinator's shared brief also supplies each canonical stack worker's assigned
knowledge_ids, exact knowledge_selection and fingerprint. Append knowledge_usage
records to its native result envelope without replacing its raw report or format.
The usage records identify worker/scope, selection/body/reference hashes and how
the knowledge was applied. Request missing records once; a selected input that
remains missing, failed or stale is failed delivery coverage and cannot satisfy a
required candidate gate. General domain lenses use the same envelope and ledger.
