# Office creative-flow repair

User authorization: the Office plugin itself must autonomously create attractive,
distinctive designs with images, color and form. The user rejected the theme
sampler and subsequent neutral native demonstration, rejected having to supply
one preferred reference, and explicitly stopped manual example beautification.
Implement the reusable skill/role/helper flow. Do not create another manual deck
or image set for the user in this repair.

## Cause and chosen owners

The current comparison helper gives every candidate the same reading frame and
only a few CSS recipes. Selection precedes actual format composition and asset
resolution. Technical validity and legibility can therefore pass without a
meaningful visual idea. More palette presets or a polished isolated example do
not repair those boundaries.

Keep Office's shared content/design owners, five roles, native producers,
inspectors, palette/font tools, optional templates and licenses. Office's shared
design method owns subject-specific art direction and its creative acceptance
criteria. `frontend-design:frontend-design` can supply one targeted creative
contribution when available and useful, declared as the optional external provider
`frontend-design@claude-plugins-official`. Its source inspection establishes useful
principles, not demonstrated Office effectiveness; it is not a mandatory dependency
or the art director. Load no competing creative instruction stack. Copy no upstream
text or executable. Office retains native geometry, source/claim fidelity, image
authority, candidate identity, selection and all production. Web frameworks, responsive geometry,
motion and website copywriting do not become Office obligations. Binding brand
and inherited scope remain authoritative; upstream examples are not universal
palette/font bans or image quotas.

Admission evidence: `creative-provider-admission.json` in the parent run. Official
source pin `58267944f92187b7d6a1c822165c96c81c864806`; Apache-2.0; repository active;
installed Codex skill/manifest/license have identical UTF-8 text after line-ending
normalization. No runtime/code dependency or install is introduced. Installed-host
execution outside the current host remains distinct from compiler support.

## Ordered reusable flow

1. Intake/content resolve actual subject, purpose, audience, requested formats,
   sources/locks, brand, operation, runtime/font/image availability and existing
   autonomy. An aesthetic reference is optional. Complete editorial working data
   and stable IDs precede visual work; the PPTX display binding remains derived.
2. Shared design applies its own concise art-direction method for new-look work,
   optionally loading the one selected creative contribution above, and authors
   two or three complete unselected DESIGN payloads. Each has a subject-specific
   idea, a memorable formal choice, typography/color/form/imagery relationships
   and real-content rationale. Recoloring or changing font on the same arrangement
   is one direction's variation. Resolve useful supplied/searched/generated assets
   through the existing harness contract. No default palette/pairing, decorative
   image quota or invented factual image is substituted for art direction.
3. Existing format designers run one bounded `proposal` assignment per requested
   format, covering the candidates together. They consume exact candidate IDs,
   hashes, unselected design payloads and editorial working revision. They return
   the existing native object/page specification and asset requests for a small
   representative set. Opening plus the actual hardest reading/evidence/table/
   process job must be represented; a content-heavy job cannot pass on its cover.
4. The coordinator resolves/inspects authorized assets, builds separate native
   specimens with WordCraft/DeckCraft and renders saved files. Candidate-specific
   copies of the existing PPTX plan receive that candidate's display fields and
   canonical binding. These are working proof bindings, not selected final CONTENT
   or permission to alter editorial decisions. No fake selection is added.
5. Existing reviewers run `proposal` review over all candidates/frames for their
   format. They apply Office's creative acceptance criteria under the actual brief, inspect
   distinctness, subject specificity, useful imagery/form/type, dense content and
   buildability, as well as fidelity/legibility/native checks. Missing character
   or ignored visual requirements is a creative failure even when files are valid.
   Personal preference alone is not a universal rule. Repair rejected proposals
   before the gallery; do not force a choice among failed candidates.
6. The helper presents exact native renders in a fixed safe gallery. User answer
   or existing autonomous authority separately selects a candidate. Combinations
   remain new authored candidates with parent IDs, higher revision and fresh proof.
   Freeze selected DESIGN and derived final CONTENT/plan bindings, then use the
   same format designers/producers for remaining composition and full native review.

Narrow/read-only/inherited operations retain their scope. A content-only revision
uses the existing inherited-design rebinding procedure, without a creative loop.
Missing required runtime/image capability blocks only dependent work with actual
host recovery, never a silent substitute. An absent optional creative provider does
not block Office's own method; an explicitly requested unavailable contribution is
reported as unfulfilled. Theme creation must declare the same
existing format designers/reviewers; it cannot bypass the proposal flow.

## Executable comparison contract

Extend `design_compare.py`, not a second renderer or layout DSL. Keep v1 behavior
and security as an explicitly limited theme sampler; it cannot satisfy complete
creative comparison. Add `office/design-candidates/v2` under the same CLI:

```text
design_compare.py INPUT --out COMPARE.html
design_compare.py INPUT --select ID --authority user|autonomous --source TEXT --out DESIGN.md
```

V2 keeps project/formats, two or three candidates and full real sample data.
Required top-level fields: `schema`, `project_id`, `formats`, `sample`, `sources`,
`representatives`, `candidates`. Reject unknown keys in the new wrapper/preview
contract; DESIGN itself retains its existing schema and extensibility.

- `sample` has existing title/lead/body/source_note and optional supplied image,
  plus `content={project_id,revision,unit_ids,claim_ids}` and
  `evidence=[{id,text,source_refs:[{source_id,locator}]}]`. `table` retains headers/
  rows; `table:null` and empty evidence are allowed only with a nonempty matching
  reason in `not_applicable`. Do not invent a table for a brief without that job.
  Present roles are title/lead/body/source_note plus evidence/table when applicable.
  In v2 a supplied image is exactly `{path,alt,sha256}`. Verify the raw-byte image
  digest before rendering or selection, and include it in the canonical sample
  hash. Replacing image bytes at an unchanged path invalidates existing proof.
  V1 retains its existing image shape and behavior.
- `sources=[{id,sha256,provenance}]` identifies raw-byte source lineage, inert text;
  source references must resolve. No helper network fetch or claimed source audit.
- `representatives` has exactly requested format keys, each an ordered 1–3 list
  of `{slot_id,roles}`. Slots cover every present sample role for each format;
  no geometry, pattern or page/slide equivalence is prescribed.
- Each candidate has existing id/design/optional parent_ids and `previews` with
  exactly requested formats. V2 proposals must have no selection. No v1 CSS recipe
  enum applies to v2 authored designs. Each format contains `binding`, `frames`,
  and `assets` (0–20 lineage entries `{id,sha256,provenance}`).
- `binding={candidate_id,design_revision,design_sha256,content:{project_id,revision},
  sample_sha256,format}` matches the actual candidate/sample. Canonical hashes use
  the existing UTF-8, sorted-key, compact `canonical-json-v1` convention.
- `frames` matches the representative slots exactly in order. Each frame is
  `{slot_id,path,sha256,alt,provenance}`. Provenance is
  `{kind:"native-render",source,source_sha256,locator,tool,tool_version,capture_id}`.
  `source` is a confined relative path to the retained `.docx`/`.pptx` specimen
  for that format. Verify its actual raw-byte SHA-256, with a 64 MiB source bound.
  The helper does not infer validity/editability/render derivation from a suffix,
  hash or metadata. Coordinator/reviewer evidence owns those facts. Imagegen
  mockups and authored HTML may be creative references/assets, never native proof.

Reuse current confined path rules, parser, image container checks, escaping/CSP,
keyboard anchors, exact-byte data images and atomic no-overwrite publication.
Native source files are streamed for their digest, not executed or unpacked.
Source/image paths must remain under the input directory; reject absolute/drive/
UNC/ADS/traversal/link escapes and all input/preview/source output aliases. Keep
4 MiB/16-million-pixel limits per image, add 16 MiB total image bytes and at most
18 frames overall. Read each image once for validation/hash/embedding. Exact
duplicate frame-digest vectors for one format across candidates fail as reused
output; nonidentical bytes do not prove creativity. Preserve actual aspect ratios;
do not crop/recolor/apply fonts to preview pixels. Render the common readable
sample once and label proofs/provenance without implying verified artistic quality.

V2 selection adds optional `selection.preview={comparison_sha256,
hash_mode:"canonical-json-v1",sample_sha256,design_sha256,frames}`; frames maps the
original requested formats to `{slot_id,sha256}` lists. Validate this block's shape
and supported format keys in `office_records.py` when present. These are original
choice fingerprints, not promises of current render derivation. Inherited design
rebinding preserves them unchanged, including original format keys/revision hashes;
new content/format composition still gets its scoped native checks. Legacy DESIGN
records remain valid. Fresh v2 selection must match every input proof binding.

## Exact ownership and verification sequence

Test author first: new v2 gallery/selection/security tests and optional-record
provenance tests; preserve the frozen original49 record/23 comparison tests. Then
Python specialist changes only the two owning helpers and their references. Then
one source writer changes Office design/intake/format/producer methods, five roles,
native preview references, theme dispatch sidecar and thin entries. No sixth role,
new engine, preset catalog or copied upstream instruction library. Remove obsolete
selected-before-proof/no-external-provider clauses, keep final selected-only gates.

Update affected operational assertions, preserving independent source/coverage/
font/license/native/candidate/isolation/dispatch/atomic-write protections. Execute
the emitted v2 helper/selection/record/plan path on all five real published packages,
including optional-provider absence and required-runtime/isolation/dispatch failure
cases. Reuse actual
registry/compiler fixtures. Add stale design/sample/image/native-source hashes,
missing/reordered slots/formats, omitted real-content roles, malformed source/asset/
provenance, duplicate output, aggregate bounds, nested image/path/link/alias failures
and no-publication-on-error. Validate caller obligations separately from metadata.

The user stopped manual demo creation. Use fixture/native evidence already retained
for executable seam tests and a source-bound replay of the rejected proposal through
the updated proposal-review method; create no new manual deck/image set. A beauty
guarantee or full live creative production on every host is not claimed by these
tests. Actual future creative runs must obtain the required reviewer evidence.

Update Office README/license-provider index, Office guides and affected original
docs under docs/plugins/office; fix their two invalid neutral command aliases.
Bump Office minor to3.3.0 and Daodan patch for theme dispatch; increment current
marketplace metadata, regenerate docs and all five exports. Do not hand-edit them.

Independent source/operational review must trace every entry, phase/mode, role,
nested reference, helper and generated resource. Preserve current3.2 baseline red
results (2616 tests,32 failing subcases,14 skipped); fix task-related Office oracles
and report independently established catalog/budget/protected-test/environment
failures without raising caps, deleting tests or changing foreign work. Run full
Office plus affected compiler/record tests, all required linters/parity/build checks
and report any remaining repository-release blocker. No commit/push grant exists.
