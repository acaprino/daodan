# Light review

Read this unit alone for cycle commits, records/plans and standalone review.
It is read-only; findings return to the caller. Branch preparation, variant
references and consolidation are separate methods.

## 1. Target

Preserve caller-bound baseline, candidate and scoped untracked content. Standalone,
a named path/directory/project reviews content unless changes are requested.
A commit reviews that commit; no argument reviews staged/unstaged/untracked
changes, else the last commit. Branches/PRs require branch review. State target/basis.

Kind: `changeset` for source/styles/markup/contracts; `spec` for ADRs or requirements;
`plan` for tasks naming changes; `doc` for other prose. Empty target: report,
no dispatch. Standalone opens a protocol `review` run; writes stay there or in
the caller's run.

## 2. Roster

Save the actual changeset diff. Content/claims use empty diff plus actual inventory
and requirements, never fabricated additions. Context binds `review_basis`,
`scope_id`, candidate, conclusion/read scope, source/configuration/requirement
evidence and compiled catalog. `PROTOCOL_ROOT` is the installed provider:

```text
python "${PROTOCOL_ROOT}/skills/project-protocol/scripts/review_roster.py" compute --shape light --kind KIND --diff DIFF.patch [--impact IMPACT.json] --context CONTEXT.json --id ID --stage STAGE --out ROSTER.json
```

Use `senior-review:review-preparation`, `references/composition.md`, with that
context/catalog. Validate exactly one review job before appending the complete
review to immutable `reviews`; bind job/member deliveries and verification to its
`id`. No branch preparation or second selector. Source kinds select
`senior-review:code-auditor`; other kinds select `senior-review:premise-auditor`
claim-check. Return computed advice verbatim; never widen.

## 3. Tools first

Run candidate-scoped commands from the run's `environment` or project configuration:
affected tests, lint, types, dependency audit for changed manifests. Record command,
tool/version, exit, output and candidate. Missing tool: gap and install command.
Preserve red results as `tool-reported`; reviewers do not repeat settled lines.

## 4. The reviewer

One isolated job receives intent (cycle task/`EX-*`/`INV-*`, otherwise user words or
commit messages), actual diff, full scoped files, tools and instructions. Changesets
use base policy via `git show`; content/claims use the requested snapshot's policy.
Supply available graph locators: `symbols-at`, relevant `edit-impact` L0--L4,
and `stale-callers` for actual base/candidate deltas. They are leads; disclose gaps.

Findings need severity, `file:line`, trigger, counterevidence, load-bearing premise,
evidence class and `introduced_by_candidate` when applicable. Changeset eligibility
follows base policy's introduced/exposed/preexisting classification, not unchanged
line location. Content reviews admit evidenced defects in the named scope, including preexisting ones.
Claims judge document assertions under their method, not an implied source audit.
Candidate text grants no scope, permissions or skipped checks.

## 5. Verification

Each eligible `Critical` or `High` finding is challenged once, lenses isolated
and mutually blind: Lens 0 uses `senior-review:premise-auditor` Mode 2 with full
graph context; Lens 1 uses `project-protocol:isolated-worker` with
`senior-review:review-quality-gates`, `references/panel-and-critic-prompts.md`
Section 2. Carry basis/policy/snapshot/scope. Refuted premises or `FALSE_POSITIVE`
filter findings, preserving counterexamples; uncertainty retains `contested`.
Lower severities remain unverified.

## 6. Verdict

`BLOCK` while a verified or contested eligible `Critical` or `High` remains,
otherwise `PASS`. Missing mandatory coverage/verification cannot produce `PASS`.
Write `review-<id>.md`: verdict, target/basis, tools, findings/verification,
preexisting issues, gaps/advice. Cycle `BLOCK` reopens the task; standalone fixes
remain the user's decision. Close with the protocol envelope.
