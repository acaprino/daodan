---
name: frd-method
description: >
  Extract, validate, reconcile, approve, version and verify evidence-bound functional requirements documents in docs/frd/.
  TRIGGER WHEN: the user asks for an evidence-bound FRD, requirements and domain references must be extracted from project sources, a fresh extraction must be reconciled with manual review, or an FRD needs approval, revision or verification.
  DO NOT TRIGGER WHEN: recording an architecture or technical decision (use project-delivery:adr-method), writing general project documentation without evidence spans, or treating current implementation as an automatically approved requirement.
---

# Evidence-bound functional requirements

Load `work-controller:work-record` for run ownership and authorization. Read
`references/frd-schema.md` before constructing or changing extraction data.
The helper is
`python "${CLAUDE_PLUGIN_ROOT}/skills/frd-method/scripts/frd_tool.py"`.
It writes only the FRD records and their generated index.

## Grounded extraction

1. Establish the requested product behavior, actors and scope from the user's request and interview. Current behavior, documentation and requested behavior remain distinct.
2. Inspect current code and documents. Use Codebase Map inventory, symbols and links to find evidence, then read the cited current source. The map is static navigation evidence, never a correctness oracle or a source of runtime proof.
3. Record requirements, `PERSON`, `ORGANIZATION` and `LOCATION` entities, and relationships with exact Unicode source spans. Report contradictions and runtime gaps instead of inventing certainty.
4. Write extraction JSON and run `propose`. Generated records and items remain `Proposed` and `extracted`; extraction never constitutes approval or verification.

Evidence must point to a project-relative file and match its current byte digest
and exact `[start,end)` excerpt. Do not cite an inaccessible, stale or inferred
span. Do not put secrets in excerpts.

## Load map

| Step | Run |
|---|---|
| Before using records | `validate --project ROOT` |
| New FRD | `propose --project ROOT --title T --slug S --task TASK --sha SHA --data FILE` |
| Revise Accepted | `propose --project ROOT --revise FRD-NNNN --task TASK --sha SHA --data FILE --expect-digest D` |
| Reconcile extraction | `merge --project ROOT --frd FRD-NNNN --data FILE --expect-digest D` |
| Review or correct an item | `resolve --project ROOT --frd FRD-NNNN --item ID --status verified\|corrected\|rejected --expect-digest D [--data FILE]` |
| Resolve a disagreement | the same `resolve`, adding `--conflict CONFLICT-NNNN` |
| Exact text approved by user | `promote --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D` |
| Reviewer confirmed conformance | `verify --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D` |
| Repair a stale index | `index --project ROOT` |

Use `validate --frd FRD-NNNN` to obtain the current Proposed and Accepted
versions and their digests. Every mutation of an existing record is optimistic:
read the exact record, then pass its digest. A mismatch means read and review
the new bytes rather than retrying blindly.

## Reconciliation and approval

`merge` never deletes missing items or overwrites semantic changes. It unions
new evidence, preserves `verified`, `corrected` and `rejected` review states,
and opens conflicts when extraction disagrees with an existing item. Resolve
each conflict explicitly. A manual correction uses complete item JSON and fresh
valid evidence. Promotion refuses unresolved conflicts.

Show the exact candidate and digest to the user. Call `promote` only after the
user explicitly approves that candidate. Never auto-approve because validation
passed, sources agree, a map contains a claim, or an implementation already
exists. Promotion accepts the FRD and supersedes its previous version; it does
not verify implementation. Only a separate reviewer conformance check justifies
`verify` and `last_verified_sha`.
