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

The reviewer catalog is `plugin.toml`: `[components].roles` are the identities,
`[reviewers.compositions]` the members. `scripts/composition.py catalog` writes
it as `CATALOG.json`; include it in the context supplied to `review_roster.py`.
A composition expands to its leaf roles; a method binding, when a host supplies
one, also retains its audit-only method task. An identity absent from the
catalog, a missing role file, unknown applicability or an unmet prerequisite
remains an explicit failure or gap.

Satisfy the expanded members' prerequisites before binding jobs. The former
testing provider is not part of the new two-owner base; if a testing member is
requested and no adapted host equivalent exists, record the missing preparation
and leave the coverage gap explicit. Reuse settled D1/D9 evidence once; record
missing inputs and stale/unmeasured metrics. This prepares inputs without another
reviewer, standalone workflow or repeated settled checks.

Build one `BINDINGS.json` from verified values:

- `candidate`: the exact roster grounding candidate; a different value is an error.
- `knowledge_selection`: fingerprint of the once-prepared selection, `""` for an
  explicit empty selection. Changes invalidate the job; do not select again per member.
- `output_dir`: job report directory inside the owned run; `input_mode` (default
  `independent`).
- Optional `scopes`, keyed by `scope_id`, each with its own `input_mode`,
  `permissions` and `output_dir`. Modes and grants must agree with the member
  brief. Independent modes never share a job.

The helper makes one job per roster identity (support roles are not jobs),
expands compositions to leaf role files, adds one job per required specialist
not already covered on its scope (light folds them into its single job), and
records for each job `job_id`, `role`, `specialist_ids`, `scope_id`,
`input_mode`, `permissions`, `candidate`, `knowledge_selection`,
`source_bindings` (role file and SHA-256 per member), `body_sha256` (members'
digests plus `reviewer-common.md`), `output_path` and `status`. Role prose is
never copied: a worker receives the files the bindings name. Session
permissions and the read-only review contract still govern every operation.

With `SENIOR_ROOT` the verified installed senior-review provider:

```text
python "${SENIOR_ROOT}/skills/review-preparation/scripts/composition.py" catalog --out CATALOG.json
python "${SENIOR_ROOT}/skills/review-preparation/scripts/composition.py" bind --roster ROSTER.json --bindings BINDINGS.json --out PREPARED-REVIEW.json
```

An `unbound` job (identity or role file missing) leaves the exit status non-zero
and its gap in `gaps`; do not dispatch such a plan.

The result preserves the roster and adds `jobs`, `common` and `catalog_sha256`. Validate before
dispatch and append that complete review to the run's immutable `reviews`; an
empty raw `jobs` list from the roster is not an executable plan. Record pending
deliveries with the review ID, job ID, role and assigned path. Keep one canonical
body artifact; plans, selection tables and logs reference its binding. Historical
records retain their original contract. Continuing a stale/unprepared review
requires a fresh prepared entry, never mutation of the immutable old entry.

## Execute and account

Each job carries its role, canonical `specialist_ids`, scope, input mode,
candidate, knowledge and source fingerprints, body digest and output path.
Dispatch the host's isolated-worker binding through the consuming workflow's
declared isolated inline binding with the complete actual worker role and exact
job body supplied once through the active host mechanism, plus the native variant's
prepared inputs. If the host supplies no isolated binding, declare the job
unavailable instead of running it in a shared context. Supply body-free job metadata for accounting; do not make a worker
reload a task body already injected in its initial prompt. Bind the worker role's
verified provider/root separately from each member's provider/root. A job ID is a
delivery identity, never an invented agent type.
Do not load a role as a skill. Qualified named presets and single specialists
remain invocable through their registered host bindings.

Learned facts: before dispatch, run `brief` on the prepared review and append its
facts to the dispatch prompt of each discovery job, never to the composed body, blind
derivation, a lens or the critic. After the checks close, run `record` once.
review-consolidation's `references/learned-facts.md` holds the commands, the facts
block, the decline rule and the `Learned facts` report section. A review without a
ledger, a bound target or a project home runs as before and reports the facts unavailable.

Discovery jobs with compatible scope, mode and permissions may unite members;
the same member on different scopes remains distinct. Premise derivation,
verification lenses and critic keep independent contexts, inputs, delivery IDs
and output files. A discovery delivery cannot also satisfy a verification check.

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
blind/critic/verification requirements through the host isolation/run-record
mechanism. Lens results have separate files, candidate bindings and evidence.
Required checks survive fast/no-context options. Consolidation retains finding
provenance and every coverage limitation; the existing final writer alone
publishes the report.
