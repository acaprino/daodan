# Office record representation

`scripts/office_records.py` is the executable structural contract. Use its
public `load_record(Path)`, `validate_content(record, pptx_plan=...)`,
`validate_design(record, require_selected=True)` and `write_record(record, Path)`
interfaces. Validators return error strings and never mutate their arguments.
No errors means structural consistency within the supplied data.

Records are UTF-8 JSON objects, either standalone or inside exactly one
`json` fence in Markdown. The loader rejects duplicate keys at every depth,
nonfinite numbers, malformed/non-object data and files above 4 MiB. The writer
validates before publishing a new Markdown artifact, preserves actual Unicode
data and refuses any existing output, including aliases and links. Publication
uses a temporary sibling and an atomic publication that refuses replacement
(Windows rename, hard link elsewhere). An unsupported filesystem fails safely.
Choose a new candidate path for revisions.

## CONTENT.md

The schema is `office/content/v1`. Required fields:

| Field | Representation |
|---|---|
| Identity | `project_id`: nonempty stable text; `revision`: positive integer |
| `brief` | Nonempty `operation`, `intent`, `goal`, `audience`, `market`, `channel`, `scope`, `depth`, `extent`, `density`, `tone`; unique requested `formats` (`docx`, `pptx`); `transformation` mode |
| `sources` | Nonempty list of `{id, path, sha256, role}`. IDs are unique; hashes describe original source bytes, never canonicalized text. Source roles identify information, binding brand/template, reference or existing artifact as appropriate. |
| `claims` | Nonempty list of `{id, text, priority, sources, locked, conditions, conflicts}`. `priority` is `core`, `supporting` or `optional`; `sources` is a nonempty list of `{source_id, locator}`. `locked` is boolean; conditions/conflicts are lists of text. |
| `units` | Nonempty list of `{id, message, text, claim_ids, relationship, detail, transformation}`. Claim references are nonempty and known. Each unit carries complete content, not a promise to write it later. |
| `sequence` | All unit IDs, each exactly once, in logical order |
| `projections` | Exactly the requested format keys, as below |
| `transformations` | List of `{unit_id, mode, source_ids, destination:{format,id}, reason}`. Each destination exists and places the named unit. |
| `gaps` | List of unresolved evidence or editorial gaps as text |
| `exclusions` | List of `{claim_id, format, reason, authority, source}`. Known claim, requested format, decision source and explicit `user` or authorized `autonomous` authority. |

Permitted transformation modes are `verbatim`, `copyedit`, `restructure`,
`rewrite`, `summarize`, `synthesize` and `expand`. Set permission per unit; the
brief's overall mode does not override local locks. A unit carrying a locked
claim uses verbatim mode and exactly that claim's text. Keep distinct locked
blocks in distinct units. A transformation entry cannot release a lock.
Its mode must agree with the named unit's transformation permission.
Every requested format covers every core claim through placed units, unless
an explicit authorized exclusion names the claim and format. Mapping alone
cannot prove that a free rewrite preserves meaning, conditions or uncertainty.

DOCX projection:

```json
{"content_revision":1,"structure":"technical brief","sections":[{"id":"D1","title":"Editorial authority","unit_ids":["U1"]}]}
```

PPTX projection:

```json
{"content_revision":1,"plan":{"path":"plan.json","hash_mode":"canonical-json-v1","sha256":"<64 hex digits>"},"placements":[{"slide_id":"S1","unit_ids":["U1"]}]}
```

Both projection revisions equal the content revision. The PPTX plan remains the
existing native plan, with stable slide `id` and `claims` plus a
`content_revision` binding. This record adds placements, never a competing
slide schema. Validate with the supplied plan to check its revision, unique
slide IDs, known claim IDs, placement destinations and exact agreement between
each slide's claims and placed unit claims. A slide with claims needs a placement;
slides without claims may remain outside the editorial mapping. Native pattern,
object and capacity validation remains with the PPTX tools.

The binding digest is SHA-256 of these bytes:

```python
json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

`hash_mode` must explicitly be `canonical-json-v1`. A whitespace change in the
original plan file leaves this binding unchanged. The CLI separately prints
`pptx_plan_file_sha256`, the hash of the supplied file's original bytes, as
input evidence. Do not substitute one hash for the other. Without a supplied
plan, serialization and validation check record structure and declared digest
shape only; they do not verify external plan content or source file bytes.

## DESIGN.md

The schema is `office/design/v1`. Design owns these decisions; the content helper
also validates their shared representation for its consumers.

| Field | Representation |
|---|---|
| Identity | `project_id`, positive `revision`; `content:{project_id,revision}` names the same project and positive content revision. The consumer compares it with the exact loaded content record. |
| `formats` | Unique, nonempty subset of `docx`, `pptx` |
| `direction` | `{name, idea, principles:[text,...]}` with all fields populated |
| `palette` | Existing helper roles `background`, `surface`, `ink`, `accent`, `muted` as `#RRGGBB`; nonempty `data` colour list; `provenance:{source,method}`; `proportions:{background,surface,ink,accent}` as finite fractions summing to one |
| `typography` | `heading`, `body`, `caption`, each `{family,fallbacks:[...],weight}`. Safe family names and explicit nonempty fallbacks; integer weight 1 through 1000. |
| `spacing` | `{unit,scale:[...],density}`. Finite positive unit/scale values, with increasing unique scale values; density is a safe style name. Units describe a scale; format methods choose native geometry. |
| `imagery` | `{treatment,source_policy}` as nonempty text |
| `data` | `{table,chart,source_notes}` as safe style names |
| `components` | `{title,callout,quote,navigation}` as safe style names |
| `adaptations` | Exactly the requested format keys, each `{reading,emphasis}` as nonempty text |
| `selection` | `{candidate_id,authority,source}`; nonempty exact candidate identity and decision source; authority `user` or authorized `autonomous`. Optional original-choice `preview` fingerprints are described below. |

Font/style names contain only Unicode word characters, spaces, periods and
hyphens. They contain no CSS declarations, functions, URLs or markup. Consumers
still escape displayed text and map style names through their own fixed
renderer; validation is not permission to interpolate arbitrary data into CSS.
Use the existing palette helper for contrast/distinctness mathematics. This
validator checks role/value completeness and does not recompute palette quality.

`validate_design(record, require_selected=False)` accepts a proposal without
selection, but rejects a malformed supplied selection. Final records require
selection. Neither browser highlighting nor validation implies approval.

Optional `selection.preview` has exactly `comparison_sha256`,
`hash_mode:"canonical-json-v1"`, `sample_sha256`, `design_sha256` and `frames`.
Digests are SHA-256 values. `frames` is a nonempty map of original `docx`/`pptx`
format keys, each with one to three `{slot_id,sha256}` entries and unique populated
slot IDs. Unknown preview/frame keys or malformed values fail, even when the
selected-record requirement is disabled. The comparison helper supplies these
fingerprints only after validating the exact original proof bindings and bytes.
They describe that historical choice, so this validator does not compare them
with current design/content hashes or require current format-key equality.
Inherited rebinding preserves the block unchanged; it cannot certify a new render.

The design consumer explicitly loads the record and compares content identity,
revision and requested formats before native production. Actual font availability,
source fidelity, accessibility and saved-file rendering need separate evidence.
