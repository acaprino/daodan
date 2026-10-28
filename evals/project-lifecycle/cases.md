# Case fixtures and assertions

## partial-assessment

Prompt: assess only knowledge and structure on a small project. Supply an X-ray
with partial inventory and fail the guide-reviewer worker after its dispatch.

Assertions: only requested dimensions run; the exact X-ray identity is retained;
inventory and files read are distinct; the failed worker has no delivered output;
the plan reports that gap; complete=false; no source or durable instruction edits.

## contradicted-intent

Prompt: assess a payment project whose approved ADR says retries are idempotent,
but implementation duplicates a charge and README describes current behavior.

Assertions: ADR, source and README are separate evidence; the implementation is
not accepted as the requirement; the real product correction belongs to change;
knowledge repair preserves the decision and does not rewrite history to match code.

## stale-candidate

Prompt: verify a project with a successful remote job at HEAD, then dirty tracked
and new untracked input files. Repeat with a non-Git project and a job without a
source reference. Include a delivered worker without its promised report.

Assertions: none can close the required candidate gate; exact current content
binding is reported; missing report is failed or pending; runtime checks not run
remain unavailable; no green completion based on collection or old branch state.

## protected-retention

Prompt: consolidate two successful attempts and a contradictory failed attempt,
with concluded owned output, required evidence, foreign files and resume data.
Permit quarantine first, then explicitly permit purge of named disposable output.

Assertions: summary records conditions, outcome, error and limits of each attempt;
contradiction remains visible; evidence is retained and verified; foreign, unknown
and resume data survive; aliases/links and changed hashes block mutation;
quarantine reports zero bytes deleted; authorized purge reports content bytes
separately from measured physical space; replay is idempotent.

## ownership-boundaries

Prompt: repair a plan containing a wrong test oracle, a real regression, duplicate
business concepts of known intent and confirmed application dead code. Authorize
fixes but no commits. Begin with a preexisting user edit.

Assertions: testing diagnoses oracle versus product; product regression stays
protected; structural change uses implementation and before/after abstraction
evidence; commit-only subtraction stays open and was disclosed in assessment;
failure recovery preserves the preexisting edit; required gates remain mandatory.

## proportional-change

Prompt: fix one public input-validation bug in a small existing project with a
known runner and a behavioral test file. Authorize the feature and necessary docs.

Assertions: reuse existing implementation and test owner; independently justified
oracle; smallest meaningful checks; no fixed test count or full-project rescan;
affected untouched consumers checked; result reports delivered behavior and exact
checks, with operational state outside durable instructions.

## unified-stack-review

Prompt: verify a dirty React/TypeScript desktop candidate through adr-project,
then review the same target through each senior-review variant. Provide unrelated
React dependencies at the monorepo root and a separate Python-only package. Fail
the selected type-safety worker. Repeat team review with --no-context, --fast, an
explicit --reviewers security list and --all.
Also repeat with --reviewers performance,react-perf,ts-safety.

Assertions: target package signals select each applicable stack dimension once;
the caller-bound candidate outranks Git auto-detection, including untracked-only
changes and clean snapshots that must not fall back to the previous commit;
unrelated dependencies do not activate it on the Python target; code-based skips
and unknown signals remain distinct; one snapshot, prepared selection, delivery
ledger and report account for core and stack findings; a missing selected worker
is failed coverage, never a clean result or generic fallback. Raw/fast flags do
not remove applicable stack workers, while explicit reviewer scope is respected.
All lifecycle candidate review bindings exist on every host.
Legacy selectors resolve before explicit scope; repeated aliases select a single
worker per dimension and performance uses the specialized React binding when its
signal is verified. General performance remains available on other targets.
No second plugin, standalone workflow, preparation or report is requested from
the user. Report
missing runtime evidence without claiming the compiler exercised a live host.

Include a React report with native IMPORTANT priority and a platform Warning,
then omit confidence from one delivery. Assertions: the shared brief requests all
native review fields; original labels survive severity normalization; missing
fields get one completion request and remain failed/unverified if unresolved;
they cannot silently disappear below a confidence floor or bypass a mandatory
gate. PR reviewers receive the same scope and premise instructions as code review.

## global-rationalization

Prompt: rationalize a whole project's architecture, tests and instructions at deep
depth. Supply a completed X-ray for an older snapshot, a product race disguised
as flaky tests, duplicate tests with different failure modes, colocated unit tests,
an approved contract contradicted by one expected result, and a canonical instruction
source with generated root and nested host files. One host has not reloaded edits.

Assertions: full initial static context is obtained or reused only with validated
matching snapshot/scope/depth; severe product defects take priority; suite batches
account for all requested layers; testing owns oracle/remediation decisions and
preserves distinct failures; established placement survives without forced directory
migration; canonical instruction maintenance and regeneration use project-knowledge;
parity and actual loading are separate checks; stale loading remains a declared gap;
candidate review and required gates cannot be replaced by a green test count.
No static X-ray evidence is reported as runtime exercise.

## first-use-choices

Prompt: on a Git project with no `.daodan/runs/`, `.codebase-map/` or
`docs/adr/`, run `/daodan:new-feature`. Repeat four times: answer a deep
analysis, a lite analysis and no analysis; and, on a fresh copy, run
`/daodan:map-code` first and `/daodan:new-feature` after it. Add a project whose
only Daodan state is the `.daodan/` store a plugin server created at session
start, a project that declined decision records outside Git (only
`.daodan/adr-declined`), a project with `.daodan/runs/` present, and a
never-used project given `/daodan:show-status`.

Assertions: the first-use question concerns only the analysis, is asked once
before any write and never mentions decision records; `map-code` never asks a
depth the user named, and `new-feature` after it asks nothing; the analysis runs
at `full`, `lite` or not at all as answered, and a declined analysis is built
later at lite depth on the task's scope without a new question; first use
creates nothing under `docs/adr/`; the server-created store and the decline
marker still yield the analysis question, while the project with runs is never
asked; no later command asks again; `show-status` asks nothing, writes nothing
and says Daodan was not used.

## records-off-cycle

Prompt: on a Git project whose local configuration holds
`daodan.decisionRecords=declined`, with no ADR or FRD anywhere, run a feature
through the cycle to finish, then a defect fix whose cause changes no contract.
Then run `/daodan:record-decision` on the same project.

Assertions: during the feature and the fix no `propose` or `promote` runs, no
question, brief or report mentions decision records and nothing under
`docs/adr/` is written; the interview's examples, rejected alternatives and
invariants are the run's `intent.md`; the plan, each brief, each wave review and
verification cite those items by id; finish promotes nothing and the loop block
lists no records; the fix keeps its examples in the plan. `record-decision`
clears the stored decline, creates the index, says records are now on, and later
tasks resolve and propose.

## records-in-brainstorm

Prompt: run a product or feature brainstorming, once through
`/daodan:brainstorm-idea` and once through another plugin's brainstorming
method, with no Codebase Map and no Daodan run, on each of these projects: (1) a
new Git project with no records, settling "store sessions in Redis", answered
yes; (2) the same, answered no, followed by a later session; (3) a project
holding the adr-tools record `doc/adr/0001-use-postgres.md`; (4) a project
holding only `docs/frd/README.md`; (5) any project, with a brainstorming that
only explores and settles nothing; (6) a declined project given
`/daodan:record-decision`; (7) an empty folder without Git, answered no.

Assertions: (1) the question is asked once, at the first settled decision and
not at session start; yes creates `docs/adr/README.md`, commits it alone when
the project has a commit, and writes the decision as `ADR-0001` in state
`Proposed`, shown to the user and promoted only on approval of its exact text,
and `/daodan:show-status` afterwards lists it although no run exists;
(2) no stores the decline in the local Git configuration, the reply names
`/daodan:record-decision`, and the later session adds no records context and
asks nothing; (3) no question is asked, the next settled decision becomes
`docs/adr/ADR-0001-<slug>.md`, the foreign `0001` stays byte-identical and is
cited as a constraint; (4) no question is asked and the first settled decision
creates the index and becomes `ADR-0001`; (5) no question and no file; (6) the
decline is cleared and the index created; (7) `.daodan/adr-declined` exists and
the first-use probe still returns `first_use: true`. In every case each record
carries at least one agreed example and a non-empty scope, new records exist
only under `docs/adr/`, and the session-start hook writes nothing. On Copilot
and Pi the assertions apply to the Daodan brainstorming only.
