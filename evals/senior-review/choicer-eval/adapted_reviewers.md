# Blind reviewer adaptation

The author was not given and did not read benchmark cases, labels, captures,
results, model predictions, or other agents' work. This adaptation was authored
from the frozen catalog, frozen reviewer-selection prompt, three original role
bodies, and the installed tokenizer and serializer. Revisions used token counts
and serialization checks only. No model weights were loaded and no inference or
paid baseline calls were made.

The canonical artifact is [adapted_reviewers.json](adapted_reviewers.json).
It contains all 18 original reviewer IDs, the exact original positive and
negative strings (including the three original null negatives), complete adapted
criteria, compact choice descriptions, per-field provenance, and rationales.
[adapted_reviewers_audit.json](adapted_reviewers_audit.json) records hashes and
the exact serializer checks. The generator is [adapt_reviewers_blind.py](adapt_reviewers_blind.py).

The original catalog and runs are unchanged. The binary threshold remains 0.5.
The frozen catalog's strict extraction rule is preserved in the `original`
fields. Newly authored negatives exist only in `adapted` and are explicitly
marked `authored_missing_criterion`.

## Meaning and policy

Eight original positive criteria and 9
original negative criteria are reused exactly. Other role-derived changes remove
workflow dispatch language or compress the documented remit for code relevance.
The three missing negatives (platform, distributed flow, UI race) are authored
scope exclusions, not purported quotations from the source.

Three entries explicitly record a substantive alignment with the frozen prompt:

- Security includes selection rule 3's URLs, routes, endpoints, public functions,
  login, sessions, roles, permissions and access by ID, alongside the role's
  application-security concerns. Its general-quality exclusion cannot override
  those evidence-conditioned triggers.
- Premise includes selection rule 3's optional/default parameters, numeric/date
  thresholds, sign handling and business-rule boundaries, alongside independent
  derivation and claim checking. Its exclusion cannot negate those checks.
- Logic integrity follows selection rule 6: a missing interconnect map is a
  preparation requirement, not a reason to declare the lens irrelevant.

These policy adaptations are not represented as equivalent compression. They
require matching code evidence and do not create universal activation. Embedding
a mandatory rule in a classifier criterion does not itself enforce the rule;
selection enforcement remains a coordinator responsibility.

## Input compatibility

The existing questions are unchanged:

- Binary: `Does this hunk satisfy the reviewer's TRIGGER WHEN?`
- Choice: `Which reviewer's TRIGGER WHEN is best satisfied by this hunk?`

The installed `julia.data.sequence` passes with `strict=True`, `max_length=8192`
and `head_length=512` for all 18 binary pairs and the full 18-choice list.
Binary options are ordered false, true. Choice options are exactly the
`choice_description` strings, in `reviewer_ids` order, with no role IDs appended.

Every criterion is nonempty and at most 39
tokens (limit 48). Every compact description is at most
20 tokens. Token counts encode a
leading space with special tokens disabled, matching the serializer.

The choice head consumes 375 of 512 budgeted tokens:
18 question tokens, 339 option tokens and
18 option markers. The serializer adds three framing tokens outside that head
budget. It retains every option without truncation. The synthetic state is only
`probe`; actual benchmark state lengths must be checked separately. This audit
establishes input compatibility, not prediction accuracy.

| Reviewer | False tokens | True tokens | Choice tokens |
|---|---:|---:|---:|
| abstraction-architect:abstraction-architect-agent | 24 | 26 | 19 |
| platform-engineering:platform-reviewer | 24 | 36 | 18 |
| react-development:react-performance-optimizer | 28 | 24 | 19 |
| repo-hygiene:workspace-auditor | 18 | 27 | 20 |
| senior-review:api-contract-auditor | 38 | 36 | 17 |
| senior-review:chicken-egg-detector | 18 | 31 | 16 |
| senior-review:cleanup-auditor | 20 | 20 | 19 |
| senior-review:code-auditor | 14 | 24 | 19 |
| senior-review:data-integrity-auditor | 29 | 19 | 18 |
| senior-review:distributed-flow-auditor | 24 | 37 | 19 |
| senior-review:logic-integrity-auditor | 21 | 27 | 19 |
| senior-review:premise-auditor | 32 | 31 | 18 |
| senior-review:resource-lifecycle-auditor | 37 | 28 | 20 |
| senior-review:security-auditor | 37 | 36 | 18 |
| senior-review:temporal-resilience-auditor | 39 | 25 | 20 |
| senior-review:ui-race-auditor | 21 | 29 | 20 |
| testing:test-suite-auditor | 31 | 25 | 20 |
| typescript-development:type-safety-auditor | 32 | 29 | 20 |

Artifact SHA-256: `7137d44ef2851562cac315c100cabd222c7f74f66c6b2d6fad1434f187de31bd`.
Tokenizer SHA-256: `609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f`.
Serializer SHA-256: `e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e`.
