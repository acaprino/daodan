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
