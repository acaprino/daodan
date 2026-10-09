---
name: maintainer-method
description: >
  Coordinate the complete Senior Maintainer rationalization campaign.
  TRIGGER WHEN: running project-lifecycle maintain or leading its complete staged outcome.
  DO NOT TRIGGER WHEN: an intake dossier is sufficient (use handover-method), or an individual lifecycle operation covers the request.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

# Senior Maintainer

Lead the campaign; the user decides its scope, roadmap and outstanding product
choices. Read the complete campaign reference at
<plugin-root>/skills/maintainer-method/references/campaign.md before the
first stage. It is the canonical behavior; do not seek a runtime prompt in the
project's README or replace a specialist's method with that document.

## Resolve the request

Load project-protocol:project-protocol. Resolve the arguments and the user's
existing instructions into these settings:

| Setting | Default | Meaning |
|---|---|---|
| target | whole project | Project-relative path, module or feature, resolved to paths |
| exclusions | none supplied | User exclusions plus named forbidden inputs and tool output |
| focus | all | all, knowledge, structure, tests or artifacts |
| depth | deep | quick, standard or deep |
| authorization | dry-run | dry-run, fix or commit, restricted to recorded scope |
| pace | guided | guided or autonomous; never a specialist workflow flag |
| resume | none | Exact stage run IDs supplied through repeated --resume RUN_ID |
| handover | none | Exact assess run supplied through --from-handover RUN_ID |
| output root | protocol default | Project-contained alternative selected with --out |

Explicit current user authorization wins over defaults. Keep conflicting mode
flags as a clarification, never silently choose the broader grant. Read project
instructions and resolve the target from a cheap orientation before expensive
analysis. Name dimensions a narrower focus or depth leaves unexamined. Pass only
supported operation arguments to each owner; never forward --pace, --resume or
--from-handover as an invented lifecycle flag.

Before a helper takes any snapshot, inventory forbidden inputs by names only
and exclude their concrete project-relative paths. Use codebase-xray:xray-method's
forbidden-file rule without reading credential contents. The protocol hashes
directory inputs: a prohibition on quoting secrets does not prevent that read.
Also exclude .daodan/, .codebase-xray/, .team-review/, .repo-hygiene/ and every
other report root this campaign writes. Declare dependency/build exclusions that
are outside the intended scope. Scope exclusions are concrete paths, not globs.

An optional handover must identify project-lifecycle:handover in its request.json.
Validate its exact assess run and result with --current before reusing it, compare
scope and supplied evidence with this target, and read its limitations. Changed
inputs require fresh evidence. Historical observations may be attributed as such;
they are never a current correctness verdict. The dossier's work suggestions and
prior read-only authority grant no mutation acceptance to this campaign.

## Campaign state and transitions

Maintain is a campaign entry, not an additional operation in the project-protocol
helper. Never initialize operation maintain or run all stages inside one repair
record. Use the supported operations assess, change, repair, verify and consolidate
for their own stage objectives. The baseline team review retains senior-review's
own native run, schemas, preparation and delivery ledger.

Cheap orientation may use an owned assess run with objective campaign orientation,
scope identified from the request, no broad auditor dispatch and a brief as its
native report. It records checkpoint 1 and closes before the baseline review.
If checkpoint 1 changes the target, preserve that completed orientation as
historical evidence and create the next run with the approved scope. Do not rebind
an existing scope. Before a run exists, a waiting brief includes the full resolved
request and exact next entry so that a fresh session can reconstruct it.

Inside every active lifecycle run save campaign-request.json and campaign.json.
The request records original user text and native arguments, resolved settings,
intention/authorization sources and the canonical method/reference fingerprints.
The chain records this run's stage, exact earlier stage/run identities, X-ray run
binding, scope and snapshot references, accepted decisions with their scope,
next entry and interruption reason. It indexes native records; it never replaces
their work.json, results, checks or approval evidence. Save it before closing the
run. Carry a new copy forward into the next active run; never mutate a completed
record or its evidentiary reports.

Read the request and chain at every batch boundary, handoff, context loss and
resume. Resume only an explicitly named in-progress stage through the protocol
helper with identical authorizations and the recorded current candidate. For a
completed stage validate its historical result and prepare the recorded next
entry in a new run instead of reopening it. Inspect native review and X-ray runs
through their owners. A changed candidate, scope or authorization requires a new
run with the preserved prior evidence, not a guessed latest run.

## Canonical stage owners

The campaign's declared worker union supports method composition. Select only
what the active owner requires. Independent reviewers receive their own inputs
and no peer findings. Keep that owner's full preparation, phase barriers, native
contracts and exclusive final-report owner. Do not duplicate its scheduling graph
in the campaign or replace a missing role with another worker.

| Stage | Method to perform in the coordinator context |
|---|---|
| Baseline correctness and static context | senior-review:review-method, variant team-review; its method owns the codebase-xray analyze step |
| Coherence and roadmap | project-lifecycle:lifecycle-method, operation assess |
| Evidenced product corrections | project-lifecycle:lifecycle-method, operation change |
| Approved rationalization | project-lifecycle:lifecycle-method, operation repair |
| Exact final candidate | project-lifecycle:lifecycle-method, operation verify |
| Conclusions and retained evidence | project-lifecycle:lifecycle-method, operation consolidate |

The lifecycle method's operation references and canonical domain methods retain
all their gates. Perform one lifecycle operation, close or interrupt it, then
return here before preparing another. The campaign never recursively launches
one lifecycle workflow from inside another lifecycle operation. When entering a
native owner entry requires a user transition, record it and provide the exact
entry/resume request. Do not claim the compiler's TOML invoke can execute it.

Use clean-code:readability-method with clean-code:clean-code-agent only for an
approved readability batch at a method boundary and with behavior preserved.
If the active owner's inventory cannot dispatch it, finish that operation first
and offer the standalone clean-code pass as the campaign reference specifies.
Composed inventory availability grants no independent mutation authorization.

## Checkpoints and completion

With guided pace, checkpoint 1 approves the brief before expensive analysis and
checkpoint 2 approves findings and the roadmap before any project mutation. Record
the accepted items exactly. Generic approval does not accept unnamed removal,
test retirement or quarantine; honor each owner's acceptance procedure. Autonomous
pace removes those two waits and preserves every owner-required decision and gate.
Dry-run closes at the roadmap and explicitly reports the unexecuted maintenance
stages. It is an assessment delivery, not completion of the full campaign.

Follow the reference's risk ordering, batch boundaries, recovery and retry rule.
Existing edits and other sessions' files remain protected. Each stage returns its
native reports and protocol result with checks on that stage's own candidate.
Historical validation uses validate --result without --current. Final verify
uses validate --current --result against the actual present project. Read the
evidence as well as validating record correspondence.

Missing selected deliveries, mandatory checks or accepted decisions keep the
affected action open. The final campaign report names complete or stopped, paths,
real checks, three distinct coverage facts, remaining decisions and the exact
resume line. It refers to native stage results and never invents a new protocol
operation, an installed-host runtime probe or a blanket correctness certificate.
