# FRD schema version 1

An FRD is one UTF-8 JSON object stored under `docs/frd/`. Version 1 uses
`FRD-NNNN-<slug>.json`; revision N uses `FRD-NNNN-vN-<slug>.json`. `FRD-NNNN`
identifies the document family, while `FRD-NNNN vN` pins one version. JSON is
rendered with sorted keys, two-space indentation and literal Unicode.

## Extraction input

`propose --data` and `merge --data` accept exactly three arrays:

```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "text": "A consultant can reopen a paused task.",
      "evidence": [
        {
          "path": "docs/workflow.md",
          "document_sha256": "64 lowercase hexadecimal characters",
          "start": 20,
          "end": 66,
          "excerpt": "A consultant can reopen a paused task."
        }
      ]
    }
  ],
  "entities": [
    {
      "id": "ENT-001",
      "entity_type": "PERSON",
      "name": "Alfio",
      "evidence": []
    }
  ],
  "relationships": [
    {
      "id": "REL-001",
      "source": "ENT-001",
      "target": "ENT-002",
      "type": "WORKS_FOR",
      "evidence": []
    }
  ]
}
```

The empty evidence arrays above only illustrate item shape. Every persisted
item requires at least one valid evidence object. Input `status` is optional
and defaults to `extracted`; an extraction cannot introduce another status.
Every array may be empty except `requirements`. Item ids are unique across all
three collections and match an uppercase prefix followed by at least three
digits, such as `REQ-001`, `ENT-001` and `REL-001`.

Entity `entity_type` is exactly `PERSON`, `ORGANIZATION` or `LOCATION`.
Relationship `source` and `target` name entities in the same FRD; `type` is a
non-empty relationship label. A requirement has non-empty `text`; an entity has
a non-empty `name`.

## Evidence and Unicode spans

Each evidence object has exactly these fields:

| Field | Contract |
|---|---|
| `path` | Normalized POSIX path relative to the project root. Absolute paths, backslashes, `.` and `..` segments are refused. Resolved symlinks must remain inside the project. |
| `document_sha256` | Lowercase SHA-256 of the source file's current bytes. |
| `start` | Inclusive Unicode code-point offset in the UTF-8 decoded document. |
| `end` | Exclusive Unicode code-point offset, with `0 <= start < end <= len(document)`. |
| `excerpt` | Exact value of `document[start:end]`, including whitespace and newlines. |

Offsets are not UTF-8 byte offsets and not UTF-16 code-unit offsets. Newlines
remain exactly as decoded, including CRLF when present. Active records revalidate current evidence. Superseded records retain structural
history despite changed sources. Stale Accepted records can be revised; new or
promoted versions require fresh evidence. Unrelated stale records do not block
revision.

## Stored record

In addition to the three extraction arrays, a record contains exactly:

| Field | Meaning |
|---|---|
| `schema_version` | Integer `1`. |
| `frd_id`, `version`, `title` | Family identity, positive revision number and non-empty title. |
| `status` | `Proposed`, `Accepted` or `Superseded`. |
| `author`, `created_from_task` | Proposer and originating run or task. |
| `proposed_on`, `proposed_at_sha` | Proposal date and repository commit binding. |
| `accepted_on`, `accepted_at_sha` | Set only by `promote`. |
| `last_verified_sha` | Set only by `verify`; null again on each newly Accepted revision. |
| `superseded_by` | Pinned later Accepted version on a Superseded record, otherwise null. |
| `conflicts` | Extraction disagreements and their resolution state. |

A family has contiguous versions from 1, at most one Proposed and at most one
Accepted version. A revision starts from the Accepted version. Promotion marks
that previous version Superseded in the same locked write set.

## Review states and merge

Each item has one `status`: `extracted` (unreviewed), `verified` (confirmed),
`corrected` (manual, never overwritten) or `rejected` (never restored).

`merge` accepts only Proposed. New ids are appended as `extracted`. Unchanged
items union deduplicated evidence and retain their status. Semantic fields are
`text` for requirements, `entity_type` and `name` for entities, and `source`,
`target` and `type` for relationships. Changed items open a conflict with both
versions; they never overwrite stored content. Existing conflicts stay open and
missing incoming items are not deleted.

A conflict has `id`, `item_id`, `existing`, `incoming`, `status` (`open` or
`resolved`) and `resolution`; open conflicts block `promote`. Use
`resolve --item ID --conflict CONFLICT-NNNN` with `--status verified` or
`rejected` to retain the stored item, `--status corrected` to accept the incoming
item, or `--status corrected --data item.json` to supply a complete correction.
Without `--conflict`, resolve applies the same states directly. Correction data
keeps the item id and requires valid evidence. Review states and semantic fields
survive later merges.

## Commands and optimistic writes

Existing-record mutations require `--expect-digest`, the current file's SHA-256.
A mismatch refuses the write. Writes hold `.frd-lock`, validate future records
and render `README.md` before atomically replacing files.

- `propose`: create FRD version 1, or revise Accepted with `--revise`, `--data`, `--task`, `--sha` and the Accepted digest.
- `validate`: validate active evidence; with `--frd`, return version digests and `evidence_freshness: not-checked` for revision workflows.
- `merge`: merge a fresh extraction into Proposed.
- `resolve`: verify, correct or reject an item and optionally close its named conflict.
- `promote`: after explicit user approval, accept Proposed unless conflicts remain; supersede the previous Accepted version.
- `verify`: record a reviewer's conformance commit in `last_verified_sha` on Accepted.
- `index`: regenerate `README.md` between `frd-index` markers, preserving prose outside them.

The helper checks structure and evidence, not requirement truth or code
conformance. Those judgments belong to the reviewer.
