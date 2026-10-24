# Bind specialist jobs

This is the composition step of preparation, including light's distinct preparation; it
does not select another roster, run a worker or replace the native review method.

## Prepare once

Preserve the generalist's boundary floor through canonical members. To narrow a
computed family, preparation records `applicability` rows: `specialist_id`,
`scope_id`, exact `candidate`, `status: not-applicable`, and `evidence` entries
with a source `path` and concrete `reason`. The coordinator reads that evidence;
the helper validates its binding, not its truth. Missing, unknown, conflicting or
stale decisions retain the obligation. Explicit required/source obligations and
the core local checks cannot be removed this way. Preserve exclusions in the
grounding record rather than treating lexical silence as proof.

Turn an evidenced cross-provider handoff into a required receiving specialist
through existing source/configuration/requirement rows or `required_specialists`.
For example: direct React Server Actions require authorization at the action;
offline conflict policy requires transaction integrity; client-declared authority
requires authoritative authorization and any implicated domain invariant. A note
without the receiving obligation and its source/policy cannot close coverage.

Use the compiled `reviewer-catalog.json` from this installed skill and the
candidate-bound context supplied to `review_roster.py`. Include that catalog in
the context. Resolve every required member through the verified installed
provider inventory. Missing providers, changed files, unknown applicability or
unmet prerequisites remain explicit failures or gaps. A preset expands its
canonical members; a method binding also retains its audit-only method task.

Satisfy the expanded members' prerequisites before binding jobs. Testing members
reuse `testing:test-preparation` in audit mode with the assigned scope and run
permission, including light. Reuse settled D1/D9 evidence once; record missing
inputs and stale/unmeasured metrics. This prepares inputs without another reviewer,
standalone workflow or repeated settled checks.

Build one bindings object from verified values:

- `host`, `candidate`: the catalog host and exact roster grounding candidate.
- `knowledge_selection`: fingerprint of the once-prepared selection, including an
  explicit empty selection. Changes invalidate the job; do not select again per member.
- `common`: file and SHA-256 pairs for `reviewer-common.md` of
  `senior-review:review-quality-gates` and the brief's working discipline.
- `roles`: keyed by required canonical ID. Copy `provider`, `provider_version`,
  `source_hashes` and `host_binding.file` from the verified catalog entry; `root`
  is that installed provider's actual path. Method bindings also carry `skills`.
  Do not copy role prose into this object. Different content requires a new
  catalog binding, never a caller-supplied replacement digest.
- `scopes`: keyed by `scope_id`. Supply `input_mode`, the actual scoped
  `permissions` grant and `output_dir` relative to the owned run. Modes and grants
  must agree with the member brief. Independent modes never share a job.
- Optional `max_body_chars`: measured context limit, not permission to drop checks.

The helper reads the installed bodies, checks their fingerprints, preserves each
member's operation restrictions and supplies common instructions once per job.
Session permissions and the read-only review contract still govern every operation.

With `SENIOR_ROOT` the verified installed senior-review provider:

```text
python "${SENIOR_ROOT}/skills/review-preparation/scripts/composition.py" --roster ROSTER.json --catalog CATALOG.json --bindings BINDINGS.json --out PREPARED-REVIEW.json
```

The result preserves the roster and adds validated `jobs`. Validate before
dispatch and append that complete review to the run's immutable `reviews`; an
empty raw `jobs` list from the roster is not an executable plan. Record pending
deliveries with the review ID, job ID, role and assigned path. Keep one canonical
body artifact; plans, selection tables and logs reference its binding. Historical
records retain their original contract. Continuing a stale/unprepared review
requires a fresh prepared entry, never mutation of the immutable old entry.

## Execute and account

Each job carries its role, canonical `specialist_ids`, scope, input mode,
candidate, knowledge and source fingerprints, body digest and output path.
Dispatch `work-controller:isolated-worker` through the consuming workflow's
declared isolated inline binding with the complete actual worker role and exact
job body supplied once through the active host mechanism, plus the native variant's
prepared inputs. Supply body-free job metadata for accounting; do not make a worker
reload a task body already injected in its initial prompt. Bind the worker role's
verified provider/root separately from each member's provider/root. A job ID is a
delivery identity, never an invented agent type.
Do not load a role as a skill. Qualified named presets and single specialists
remain invocable through their registered host bindings.

Discovery jobs with compatible scope, mode and permissions may unite members;
the same member on different scopes remains distinct. Premise derivation,
verification lenses and critic keep independent contexts, inputs, delivery IDs
and output files. A discovery delivery cannot also satisfy a verification check.
Reusing same-candidate blind derivation is allowed only under its existing method
contract, without supplying peer conclusions to it.

Light requires exactly one discovery job. An insufficient budget fails or asks
the caller to use branch review; no silent member omission or hidden fan-out.
Budget splitting in branch review retains every obligation and its evidence.

At delivery, bind job ID, role, members, scope, candidate and body digest. Each
`member_results` row declares specialist ID, delivered/failed status,
complete/incomplete coverage, canonical finding IDs and gaps. Write a finding
once and reference it from all relevant members. A clean member still reports
completed checks; silence, an empty file or a worker stopping is not delivery.
Failed mandatory coverage prevents completion even when all workers have stopped.

The coordinator checks expected jobs and member outcomes, then the native
blind/critic/verification requirements through work-controller. Lens results
have separate files, candidate bindings and evidence. Required checks survive
fast/no-context options. Consolidation retains finding provenance and every
coverage limitation; the existing final writer alone publishes the report.
