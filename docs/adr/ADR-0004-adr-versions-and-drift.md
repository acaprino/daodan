---
adr_id: ADR-0004
title: Version decision records in place and check what a change invalidates
status: Proposed
scope:
  paths:
    - plugins/project-knowledge/skills/adr-method/**
    - plugins/project-lifecycle/skills/lifecycle-method/references/interview.md
    - plugins/project-lifecycle/skills/lifecycle-method/references/finish.md
    - plugins/project-lifecycle/skills/lifecycle-method/references/status.md
    - plugins/project-lifecycle/skills/lifecycle-method/references/realign.md
    - plugins/project-lifecycle/skills/lifecycle-method/references/verify.md
    - plugins/senior-review/skills/review-preparation/**
    - plugins/work-controller/contracts/work.toml
    - plugins/work-controller/skills/work-record/SKILL.md
    - plugins/work-controller/skills/work-record/scripts/run_state.py
    - plugins/daodan/workflows/record-decision.*
    - docs/adr/**
    - docs/decision-records.md
  modules:
    - adr-method
  domains:
    - decision-records
governs_symbols:
created_from_task: session-674d0b20-ruflo-adr
proposed_at_sha: e95dba3e721029552983b011cfab35668f5ed64f
accepted_at_sha: null
last_verified_sha: null
supersedes:
superseded_by: null
---

# ADR-0004: Version decision records in place and check what a change invalidates

## Context and Problem Statement

A decision record is written once and read at every step of the task cycle:
the interview inherits it, every worker brief carries its examples and
invariants, every wave review receives them as the intent of the change. The
helper `plugins/project-knowledge/skills/adr-method/scripts/adr_tool.py` keeps
the directory consistent (`validate_all`, lines 300-340) and promotes records
atomically (`command_promote`, lines 508-536). Gaps surfaced while
comparing it with ruflo-adr on 2026-10-24 and while writing the human guide
`docs/decision-records.md`:

1. Changing one invariant of an `Accepted` record means a new record, with a
   new identity, that restates the whole decision: `supersedes` is the only
   relation (`check_chains`, lines 327-340). A `# ADR-0001` comment in code
   and the loop block of the durable instructions then point to a
   `Superseded` record, and the copy is made by hand, where an item not meant
   to change can be lost.
2. `status.md:15-17` and `realign.md:9-11` of `project-lifecycle`'s
   lifecycle-method promise a list of active records whose governed symbols
   changed. Nothing computes it: `command_validate` (lines 538-551) counts
   records, and `last_verified_sha` is written once, at promotion (line 527).
3. `adr-method/SKILL.md:57-58` says an abandoned `Proposed` record is retired
   by superseding it; `command_propose` (lines 493-495) and `command_promote`
   refuse a `supersedes` target that is not `Accepted`. A `Proposed` record
   can only stay `Proposed` forever.
4. Records depend on one another only in prose. `docs/adr/ADR-0003-usage-ledger.md:76`
   and `:185` say the run record's owner moves with ADR-0002; if ADR-0002
   changes, nothing names ADR-0003 as something to re-read.
5. The front matter carries no version, date or author, and a human reader
   skips YAML. The identity, state and provenance of a record are not visible
   under its title.
6. The current cycle keeps a record `Proposed` until the implementing change
   is merged. This conflates approval of a specification with its realization
   in code. Approval establishes the decision independently of implementation:
   it may precede any task or document a decision emerging from work in progress.
   Approving the record does not request or authorize implementation.

The question: how does a decision change without losing its identity, and what
does the helper tell the cycle when a change touches a record's code or its
dependents?

## Decision Drivers

- A cheap model reads records many times; it must receive one record per
  decision, never two to merge.
- Identities cited in code, in the loop block and in other records must
  survive a change of the decision.
- Two files that describe one fact drift; anything shown twice is generated
  from one source.
- The helper guarantees shape mechanically; judgment stays with reviewers.
- An approved specification governs implementation immediately; approval and
  evidence that the code conforms to it are separate facts.
- A decision may be recorded before, during or after implementation, and may
  remain approved without scheduling any implementation.
- Reuse the existing run for approval evidence and implementation state;
  introduce no parallel registry.
- A decision rests on what the user read; no write may replace bytes that
  changed since that read.

## Decision

A decision keeps its number for its whole life and changes by version.

- **Approval and implementation.** `Proposed` means awaiting explicit human
  approval. `Accepted` means that the user approved this specification; it
  becomes authoritative intent at that moment, regardless of whether code is
  absent, in progress or already present.
  `promote --adr ADR-NNNN --version N --sha SHA --approval REF` records that
  approval. `REF` identifies the user's approval from the originating run or
  session, bound to the exact record version and its pre-promotion file snapshot digest. The
  coordinator verifies that the approval covers that content; missing approval
  or a changed snapshot causes refusal without writes. `accepted_at_sha` is
  the Git context at approval, which may precede the code and need not contain
  an uncommitted approved record. It is not evidence of implementation.
  Acceptance leaves `last_verified_sha` null. If an implementation task exists,
  its progress, checks and integration remain in that task's run; a stopped or
  failed implementation does not withdraw the approved decision. Finish and
  realign record implementation evidence and never approve a specification implicitly.
- **Concurrent writes.** A decision rests on a read: the user approves the
  bytes they were shown, the helper writes later, and another session or a
  hand edit may write in between. Every helper write is therefore a
  compare-and-swap, the pattern of the run record's `--expected-revision`.
  `validate --adr` and `resolve` return each record's `digest` (SHA-256 of the
  file); the coordinator shows the user the record with that digest and passes
  it back as `--expect-digest` on `propose --revise`, `promote`, `verify` and
  `retire`. The helper takes an exclusive lock file under `docs/adr/` and
  refuses, naming the holder, when another process holds it. It reads every
  file it will replace (the record, any `supersedes` target, the index) and
  refuses without writes when the record's digest differs from the expected
  one. Immediately before replacing, it reads those files again and refuses
  without writes when any differs from its first read; after replacing, it
  reads them back and fails, naming the files, when they differ from what it
  wrote. The approval reference stores the same digest, so an approval never
  covers bytes the user did not read.
- **Origin and scheduling.** An ADR may originate in a decision-only
  conversation, planned work, an ongoing WIP or existing code. `created_from_task`
  keeps the originating run or session identity; it does not require an
  implementation task. The approval reference belongs to that originating
  record, which may be a decision-only run. Approval neither creates nor
  schedules implementation, and grants no authority to edit code, commit or
  merge. Existing operational authorizations keep their own scope; later work
  requires its own authorization. A decision-only run may close after recording
  the decision and completing its document checks, with no implementation task
  or code verification required. An accepted record without code evidence
  remains `unverified`; this is an evidence status, not an instruction to start
  work or a failed gate of a decision-only run. When an ADR is extracted from
  a WIP, recording and approving it preserve the existing code and do not
  certify it retroactively. Existing code evidence may be reused only when it
  covers the exact approved version and code snapshot.
- **Versions.** The front matter gains `version` (an integer from 1). A change
  to the decision is `propose --revise ADR-NNNN`, optionally with
  `--replace ITEM-ID "text"` for each item that changes: the helper copies the
  current `Accepted` version, applies the replacements, records them in
  `changes`, and writes `ADR-NNNN-v<version>-<slug>.md` as `Proposed`.
  On explicit approval, `promote` marks that version `Accepted` and the previous
  one `Superseded` in one transaction. `resolve` returns only the newest
  `Accepted` version of each decision as approved intent, whether or not it is
  implemented. Runs and worker briefs pin `{adr_id, version}` for that intent;
  any proven version implemented on the base is separately referenced with the
  existing code evidence. The base's version describes the starting code; the
  latest approved specification governs the task and its review. These are
  references to the canonical records, never copies of their text.
  `supersedes` stays for a
  different decision replacing another and is refused between versions of one
  decision. A citation `ADR-NNNN` means the active version; `ADR-NNNN v1`
  pins one.
- **Generated header.** Under the title the helper renders a table from the
  front matter: version, status, `proposed_on`, `accepted_on` with the SHA,
  `author`, `created_from_task`, `changes` and `approval_ref`. `author` defaults to the Git
  identity at `propose` and is overridden with `--author`; it names who
  decided, not the model that wrote. `propose`, `promote` and `retire` rewrite
  the block between `adr-header:start` and `adr-header:end`; `validate` fails
  a header that no longer matches the front matter.
- **Symbol drift.** `validate --sha SHA` computes, for each `Accepted` record,
  the files among its `scope.paths` and the files of its `governs_symbols`
  changed between a non-null `last_verified_sha` and `SHA`
  (`git diff --name-only`), and returns them as `drifted`, each with its changed
  files. An active version with no verification baseline appears in
  `unverified`; the helper never substitutes its approval SHA or reports it as
  verified without drift. `verify --adr ADR-NNNN --version N --sha SHA
  --evidence REF` sets that version's `last_verified_sha` only after a reviewer
  confirmed that the code at that SHA conforms to it, with retained evidence
  bound to that version and code snapshot. A historical `Superseded` version
  may retain or receive verification evidence for the base; this never verifies
  a newer version or changes decision status. Verification does not itself
  prove integration, which remains in the task's run.
  The lists promised by `status.md` and `realign.md` are this
  output, and the branch review receives the governing records of the diff's
  files (`resolve --paths <changed files>`) as a mandatory input.
- **Retirement.** `retire --adr ADR-NNNN --reason TEXT` moves a `Proposed`
  record to `Abandoned` with `retired_on` and the reason; the index lists it
  under its own heading; `resolve` ignores it; `promote` refuses it.
- **Dependencies.** The front matter gains `depends_on`, a list of `Accepted`
  record identities checked at `propose` and against the future state of
  `promote`. Each identity resolves to its active `Accepted` version; older
  versions being `Superseded` do not make the reference inconsistent. When
  `promote` accepts a version or a record that supersedes a target, its output
  lists the `Accepted` records
  that depend on the superseded one as `dependents_to_review`; the cycle
  records each as an open question of the run, never as an automatic blocker.
  The reviewer explicitly checks each dependent against the new decision and
  records both versions, the compatibility finding and its reason in the run.
  A confirmed semantic conflict follows the normal review findings process.
  If the dependency or the dependent's decision changes, the reviewer proposes
  and promotes a revision of the dependent. `propose --revise` accepts
  `--depends-on` to replace the complete dependency list (an empty list clears
  it); omitting the option preserves the current list. `changes` includes
  `depends_on` when that field changes. A replacement with a different decision
  number requires this explicit update or removal of the old reference; the
  helper never follows a supersession chain or rewrites a dependent for the
  reviewer.
  `validate` also returns `dependency_inconsistencies`: for every `Accepted`
  dependent whose target has no active `Accepted` version, its identity and
  version, the declared `dependency`, `target_status` (`missing` or the target's
  current state), and `superseded_by` when available. These warnings repeat
  until an explicit revision of the dependent is accepted; they do not remove
  it from `resolve`, invalidate the directory or block another record's
  promotion. A candidate's own missing, self or non-`Accepted` dependencies
  cause `propose` or `promote` to refuse it without writes. The helper checks
  references; the reviewer judges semantic compatibility.

## Verified Interview Examples

- **EX-001** (nominal case): Input: `ADR-0006 v1` is `Accepted`; `propose --revise ADR-0006 --replace INV-001 "validate_order() rejects qty <= 0 except from validate_draft()" --task T --sha S` -> Expected: `docs/adr/ADR-0006-v2-<slug>.md` written as `Proposed`, `version: 2`, every other `EX`, `RA` and `INV` item byte-identical to v1, `changes: ["INV-001"]`, the index listing `ADR-0006 v2 Proposed` beside `v1 Active`.
- **EX-002** (nominal case): Input: the user approves the exact v2 snapshot; `promote --adr ADR-0006 --version 2 --sha A --approval REF` before implementation -> Expected: v2 `Accepted` with `accepted_at_sha: A`, `approval_ref: REF` and `last_verified_sha: null`, v1 `Superseded`, `resolve --paths src/orders/api.py` returning only `ADR-0006 v2` as approved intent. The task and review use v2 while the run still records implementation as pending and may cite v1 as the base's implemented behavior.
- **EX-003** (boundary case): Input: `ADR-0006 v2` has code verification evidence at `S1`; `validate --sha S2` where `src/orders/validator.py` (listed in its `scope.paths`) changed between `S1` and `S2` -> Expected: `drifted: [{"adr_id": "ADR-0006", "version": 2, "files": ["src/orders/validator.py"]}]`; after `verify --adr ADR-0006 --version 2 --sha S2 --evidence REF` confirms code conformance, the same call returns `drifted: []`.
- **EX-004** (nominal case): Input: `ADR-0003 v1` is `Accepted` with `depends_on: [ADR-0002]`; `promote` of `ADR-0005`, which supersedes `ADR-0002` -> Expected: promotion succeeds, output carries `dependents_to_review: ["ADR-0003"]`, the new and superseded records are written, and `ADR-0003` stays byte-identical for explicit review.
- **EX-005** (nominal case): Input: `retire --adr ADR-0001 --reason "replaced by the conversational decision map"` on a `Proposed` record -> Expected: status `Abandoned`, `retired_on` set, the index showing it under `Abandoned`, `resolve` never returning it.
- **EX-006** (rejection case): Input: `propose --revise ADR-0006 --supersedes ADR-0006` -> Expected: refused, "a version never supersedes its own decision", nothing written.
- **EX-007** (rejection case): Input: `promote --adr ADR-0001 --sha M` on an `Abandoned` record -> Expected: refused, nothing written.
- **EX-008** (rejection case): Input: a record whose rendered header says `version 1` while the front matter says `version: 2` -> Expected: `validate` fails naming the file and the field.
- **EX-009** (boundary case): Input: after EX-004, call `validate` twice before accepting a revision of `ADR-0003` -> Expected: both calls carry `dependency_inconsistencies: [{"adr_id": "ADR-0003", "version": 1, "dependency": "ADR-0002", "target_status": "Superseded", "superseded_by": "ADR-0005"}]`, neither call writes files, and `resolve` still returns `ADR-0003` for its scope.
- **EX-010** (nominal case): Input: after reviewing the replacement in EX-004, `propose --revise ADR-0003 --depends-on ADR-0005`, then promote the resulting v2 -> Expected: the proposal records `changes: ["depends_on"]` and preserves every `EX`, `RA` and `INV`; the warning for `ADR-0003` remains until v2 is accepted, then disappears. A later promotion of `ADR-0005 v2` lists `ADR-0003` in `dependents_to_review`.
- **EX-011** (rejection case): Input: propose a dependent with a missing or non-`Accepted` target, or promote one whose target ceased being `Accepted` after proposal, including a candidate that itself supersedes that target -> Expected: the candidate is refused naming the dependency, with every file and the index unchanged; an existing warning on an unrelated record does not cause this refusal.
- **EX-012** (boundary case): Input: `ADR-0003` depends on `ADR-0002`; `ADR-0002 v2` is promoted while v1 becomes `Superseded` -> Expected: `ADR-0003` is listed in `dependents_to_review`, but has no `dependency_inconsistencies` entry because its target identity still has an active version. The reviewer records the compared versions and compatibility finding in the run; no dependency is rewritten automatically.
- **EX-013** (boundary case): Input: after EX-002 and before any code verification, `validate --sha A` -> Expected: `unverified` includes `ADR-0006 v2`; no diff uses the approval SHA as a verification baseline. The record is approved and its implementation is still unverified.
- **EX-014** (rejection case): Input: `promote` with no explicit human approval of that version, or with an approval reference whose file snapshot differs from the current proposal -> Expected: refused naming the missing or mismatched approval, with every file and the index unchanged. A completed implementation or merge alone does not satisfy approval.
- **EX-015** (boundary case): Input: v1 was verified at `S1`, v2 is approved, and the task later records successful code verification of v2 at `M` and its integration -> Expected: v2 stays `Accepted` throughout; before its verification it remains `unverified` despite v1's evidence, then `verify --adr ADR-0006 --version 2 --sha M --evidence REF` records `last_verified_sha: M`. Approval metadata stays unchanged; the run records integration separately.
- **EX-016** (boundary case): Input: an implementation task stops after its specification was accepted -> Expected: the run records incomplete implementation, while the specification remains `Accepted`. `retire` refuses that accepted record; changing the approved intent requires an explicitly approved revision or replacement.
- **EX-017** (nominal case): Input: the user approves an ADR in a decision-only conversation and defers implementation without scheduling it -> Expected: the record becomes `Accepted`, its approval reference points to the decision-only run or session, `last_verified_sha` remains null, and document checks permit closing the decision-only run. No implementation task is required or created, and no code edits, commits or merges are authorized by the approval.
- **EX-018** (boundary case): Input: during a WIP the user asks to capture an architectural decision from the existing changes -> Expected: `propose` records the WIP run or session in `created_from_task`; the ADR remains `Proposed` until the user approves its exact content, then becomes `Accepted` regardless of code progress. Recording and approval preserve WIP files, extend no operational authorization, and establish no code conformance without separate version-bound evidence.
- **EX-019** (rejection case): Input: the user approves `ADR-0006 v2` read with digest `D1`; another session then rewrites `INV-002` of that file (digest `D2`); `promote --adr ADR-0006 --version 2 --sha A --approval REF --expect-digest D1` -> Expected: refused, "ADR-0006 v2 changed since it was read: expected D1, found D2", every file and the index unchanged; the user is shown the current text and its digest before any new approval.
- **EX-020** (boundary case): Input: during `promote` of `ADR-0005`, which supersedes `ADR-0002`, another process rewrites `docs/adr/README.md` after the helper's first read -> Expected: the re-read before replacing differs, the promotion is refused without writes naming `docs/adr/README.md`, and the same call with the unchanged `--expect-digest` succeeds once the other write has finished.

## Rejected Alternatives

- **RA-001**: an `amends` relation, where a small record changes items of an `Accepted` one and `resolve` merges them; rejected because the model would read two active records for one decision, or trust a merge done by the helper, and a cap on amendments would be needed to stop chains.
- **RA-002**: dotted versions (`1.1`, `2.0`); rejected because nobody agrees on what a minor change is and the helper assigns the number anyway.
- **RA-003**: editing an `Accepted` record in place; rejected because the previous text disappears and `accepted_at_sha` no longer describes the content.
- **RA-004**: a hand-written header; rejected because it drifts from the front matter, the defect class the fact-anchor linter exists for.
- **RA-005**: superseding an abandoned `Proposed` record from a later one, as `SKILL.md:57` says; rejected because a chain ending in a record that never held makes `supersedes` mean two things.
- **RA-006**: a database of record relations outside the Markdown, as ruflo-adr's AgentDB; rejected as a second owner of facts the records already hold.
- **RA-007**: blocking a promotion while dependents are unreviewed; rejected because every supersede would stop on records that often still hold; a recorded open question keeps the review without the stop.
- **RA-008**: automatically following supersession chains or rewriting dependencies to a successor; rejected because a replacement does not establish compatibility with the dependent's decision. The reviewer updates the reference explicitly, and an unresolved reference stays visible as a warning.
- **RA-009**: accepting a specification only after its implementation is merged; rejected because approval establishes the authoritative decision independently of when code is written. Implementation progress and evidence belong to the task when one exists, and do not redefine whether its specification was approved.
- **RA-010**: requiring a fixed specification-then-implementation sequence or automatically starting work when an ADR is accepted; rejected because a decision may be deferred indefinitely or emerge from an existing WIP. Approval of the record and authorization of operational work are separate decisions.

## Enforceable Invariants

- **INV-001**: at most one version of a decision is `Accepted` at any time, and `resolve` returns at most one record per decision number.
- **INV-002**: a version other than the first is produced only by `propose --revise`, and every item it does not list in `changes` is identical to the previous version.
- **INV-003**: a `supersedes` entry names a different decision number; a candidate's `depends_on` names active `Accepted` identities at proposal time and in the future state of promotion, never the record itself. An inconsistent dependency of another existing `Accepted` record is a warning, not a global validation failure.
- **INV-004**: the rendered header is regenerated from the front matter by every helper write and `validate` fails when they differ.
- **INV-005**: `drifted` is computed only from `git diff --name-only <last_verified_sha> <sha>` against `scope.paths` and the files of `governs_symbols`; the helper never judges whether a record still holds.
- **INV-006**: `Abandoned` is reached only from `Proposed`, through `retire`, with a reason; no command leaves it.
- **INV-007**: every helper write stays atomic: the future state is validated before any file or the index is written.
- **INV-008**: replacing a dependency with a different decision number requires an explicit revision of the dependent; the helper never infers compatibility, redirects the reference or changes the dependent during the target's promotion.
- **INV-009**: `validate` reports every `Accepted` record whose declared dependency has no active `Accepted` version, on every call until an explicit revision resolves the reference. Historical versions alone never trigger the warning; the warning neither excludes the dependent from `resolve` nor blocks an unrelated promotion.
- **INV-010**: `Proposed` becomes `Accepted` only upon explicit human approval bound to its exact version and pre-promotion snapshot; merge is neither a prerequisite nor sufficient approval. `accepted_at_sha` records approval context, and implementation state remains in the run.
- **INV-011**: proposing or accepting a new version never copies or manufactures code verification evidence. Its `last_verified_sha` stays null until `verify` records evidence for that version and code snapshot; `validate` reports it as `unverified` in the meantime.
- **INV-012**: task and review inputs identify the approved intent by ADR identity and version; any version known to be implemented on the base has its own explicit reference and evidence. Approval alone never establishes code conformance or integration, and implementation failure never demotes an accepted specification.
- **INV-013**: recording or accepting an ADR neither requires, creates nor schedules an implementation task, and grants no authority to edit code, commit or merge. A decision-only run may complete its document scope while the accepted record has no code verification evidence.
- **INV-014**: an ADR may be captured before, during or after code work; `created_from_task` records its originating run or session without implying an implementation commitment. A WIP-originated record requires the same explicit approval and separate code evidence as any other record.
- **INV-015**: every helper write is a compare-and-swap under an exclusive lock: it refuses without writes when the record's current digest differs from `--expect-digest`, or when any file it replaces differs between its first read and the moment before replacement, and it confirms the written bytes by reading them back. No helper command rewrites an existing record without an expected digest.

## Consequences

- `adr_tool.py` gains `--revise`, `--replace`, `--author`, `--version`, `--depends-on`,
  `--approval`, `--evidence` and `--expect-digest`, a `digest` per record in
  `validate --adr` and `resolve`, the lock and the compare-and-swap writes,
  `verify`, `retire`, `--sha` on `validate`, `depends_on`,
  `approval_ref`, `unverified`, `dependents_to_review`, repeatable
  `dependency_inconsistencies` warnings,
  the header renderer and the `Abandoned` state;
  `references/adr-template.md` documents the new fields and the file name
  `ADR-NNNN-v<version>-<slug>.md`; v1 keeps its current file name.
- `adr-method/SKILL.md` describes acceptance at human approval, versions,
  retirement and code verification, and drops the supersede-a-Proposed rule.
  It supports both deferred decisions and records extracted from WIP.
  `lifecycle-method`'s `interview.md` records approval independently of code progress;
  `finish.md` and `realign.md` record implementation evidence rather than
  implicitly approving records at merge. `status.md`,
  `realign.md` and `verify.md` call `validate --sha` for the drift list and
  dependency warnings, retain explicit dependent-review outcomes in the run,
  and call `verify` after a reviewer confirms; `review-preparation` of `senior-review`
  feeds `resolve --paths` over the diff's files to the branch review.
- `work-controller`'s work contract, validator and method bind inherited and
  task-owned decision references to `{adr_id, version}` and retain explicit
  approval evidence in the existing run. Proven base implementation references
  use that run's existing baseline, check and integration evidence. Update
  consumers of the task's proposed-record field so an accepted specification
  remains its implementation target; preserve readers for historical runs.
- `daodan`'s `record-decision` entry supports decision-only and WIP origins,
  records explicit approval without waiting for implementation, and closes its
  document scope without creating code work or requiring code verification.
- `docs/decision-records.md` gains versions, the header, drift, retirement and
  dependencies; its "checked by nothing" section shrinks to partial change
  across decisions.
- The three existing `Proposed` records gain `version: 1`, a header and empty
  `depends_on`; ADR-0003 declares `depends_on: [ADR-0002]`.
- Versions bump `project-knowledge`, `project-lifecycle`, `work-controller`,
  `senior-review` and `daodan`, and the marketplace.

## Confirmation

- `tests/test_adr_tool.py` covers EX-001 to EX-020 and INV-001 to INV-015,
  including the atomic refusal (a failed `promote` leaves every file and the
  index unchanged) and a file changed between the read and the write. Helper tests cover dependency references, repeatable
  warnings and explicit updates; review evidence confirms the recorded
  compatibility finding in EX-012, which the helper cannot judge.
- Lifecycle and run-contract checks cover approval independently of implementation,
  version-bound review inputs, separate implementation/integration evidence,
  decision-only completion, WIP origins, absence of operational authority from
  approval alone, and continued reading of historical run references. A merge
  never supplies approval evidence by itself.
- `tests/test_daodan_host_rendering.py` or the registration linter confirms
  the rewritten references ship on every host.
- `python scripts/lint_fact_anchors.py` passes with an anchor between the
  template, the SKILL and the guide on the version and state rules.
