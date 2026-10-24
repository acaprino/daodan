# Specialized reviewer smoke evaluation

Run date: 2026-10-22. Three fresh isolated workers each received one canonical
specialist body, its shared conventions, an assigned fixture, output path and a
static content-review brief. They received neither `oracle.md` nor peer findings.
The parent compared their persisted deliveries with the oracle after delivery.

| Reviewer | Expected defect | Protected alternative | Result |
|---|---|---|---|
| Accessibility | Click-only custom consent button lacks keyboard activation | Native button | Defect found; no finding on alternative |
| Performance | N+1 queries violate explicit round-trip budget | Single joined query | Defect found; no finding on alternative |
| Operability | Rename removes a column still read during rolling deployment | Expansion preserving old column under a no-write contract | Defect found; no finding on alternative |

Deliveries: [accessibility](accessibility/result.md),
[performance](performance/result.md), [operability](operability/result.md).
The reports preserve the inspected sources, requirement, trigger,
counterevidence, coverage and static-evidence limitations. All three expected
defects were found and all three negative controls remained unflagged.

Initial deliveries used qualitative confidence labels. The shared conventions
were clarified to require numeric confidence from 0 to 100 with evidence-based
rationale. Each worker then repaired only its delivery format in one follow-up;
no oracle or additional defect hint was supplied. The coordinator also normalized
`counterevidence_checked` from one paragraph to a one-item list, preserving every
word, to match the existing finding contract. These are completed deliveries
after a format repair, not evidence of first-attempt format compliance.

This is a small hand-authored smoke set, with explicit requirements and complete
paths. It does not measure general recall, precision across real repositories,
comparative effectiveness against the previous roles, model-token cost or
execution in installed Claude/Codex/Copilot/Pi/OpenCode packages. No browser,
database, deployment or application execution was performed. Source-derived
behavior is not presented as reproduced runtime evidence.

`fingerprints.json` identifies the reviewed role/common bodies, fixtures and
delivered reports. `instruction-size.json` records the separate source-word
comparison for the changed operational Markdown, including the new bodies and
shared reference. Word counts are not model-token measurements.
