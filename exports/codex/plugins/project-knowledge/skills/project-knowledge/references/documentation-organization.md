<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Organize Daodan documentation

Use this profile for the user's requested Daodan per-plugin structure. It
explicitly supplies the common file/audience plan; generic guidance against
inventing a numbered package does not cancel this requested layout. Other
projects retain their approved documentation framework.

Receive an owned run, input snapshot, plugin inventory, scope, authorization and
readers. Reuse `preparation.md`, `documentation-audit.md` and `apply-method.md`.
The legacy rules below override the general fallback of moving uncertain
material with a pointer. The coordinator dispatches
`project-knowledge:documentation-organizer` in isolation and owns questions,
writer assignments, delivery accounting and final reporting.

## Required plugin dossier

Use one folder per plugin: `docs/plugins/<plugin>/`. Every registered plugin uses this
entry structure; additional pages serve evidenced reader needs.

| Path | Reader contract |
|---|---|
| `README.md` | Index, purpose, main functions, first useful path and links to every section |
| `functional-spec.md` | Observable functions, actors, inputs/outputs, constraints, errors and acceptance criteria |
| `technical-spec.md` | Kernel structure, owners, interfaces, data/flow contracts, configuration, host and integration limits |
| `use-cases.md` | Use cases and guided tutorials: actor, preconditions, trigger, concrete request, steps, expected observable result and failure handling |
| `research/README.md` | Studies and linked papers, reference projects, supported decisions, counterevidence and limits |
| `validation.md` | Local tests, benchmark protocols/results, revisions, corpus, baselines, reproduction and gaps |
| `dependencies.md` | Required/conditional providers/tools, purpose, capabilities, availability/recovery and provenance links |
| `intakes.md` | Adoption/update records: source, scope, decisions, dates and both local/upstream versions |
| `licenses.md` | Credits, original project links, license/notice evidence and distribution boundaries |

Reuse and split existing content through a retention ledger. Do not replace
substance with boilerplate or drop manual text after a generated block.
Missing content is a named gap with inspected sources, never a fabricated
complete specification, paper, benchmark or use case. Label illustrative
examples unexecuted. Separate implemented behavior, approved intent and proposals.

Teach the main functions through guided tutorials with setup, complete example
inputs, ordered steps, expected output and recovery from a meaningful failure.
Link longer tutorials as subpages from the dossier index and use-case page.
Record whether each tutorial was actually exercised and on which revision.

Research attribution records identify title, authors, year, primary URL/DOI, source type,
reading status, supported claim/design choice, applicability and limits.
Abstract or snippet reading is not a full-paper reading. Reconcile conflicting
citations with primary sources before calling them verified; unread sources
retain uncertainty. Do not invent a bibliography quota. Shared research retains
one canonical owner with links from every relevant dossier.

An approved path migration updates generators/catalogs and maintained inbound
references together. Filename changes do not prove content improvement. Keep
historical citations revision-qualified instead of rewriting their evidence.

## Dependency and intake provenance

Inventory copied/adapted content and source, delegated runtime engines, tools,
executables, services, models/weights, parsers/grammars, fonts and assets. No copied files
does not mean no dependency/intake record. Office's Craft engines, Worktrunk
for task worktrees, and EmbeddingGemma and tree-sitter for Codebase Map require
their applicable records. Verify the local consumer and actual requirement;
do not make a conditional parser mandatory or optionalize a required plugin.

Each contribution has a canonical intake record linked from dependencies and
licenses, with these fields:

| Field group | Required provenance |
|---|---|
| Identity | Record ID, local plugin/owner, contribution type, original project URL and original paths/artifact identity |
| Decision and scope | Adopted/delegated/adapted/original-inspiration/evaluated/excluded status; what is brought in and excluded, reasons, local destinations/consumers, authorization and evidence |
| Actual intake event | Last actual intake/adoption or update date, backed by a dated receipt, commit or explicit evidence; evaluation/check date kept separately |
| Daodan side | Daodan marketplace version and local plugin version at that intake; local revision when available |
| Upstream side | Release/version and commit, model or grammar revision actually adopted; hashes when relevant |
| Terms and credit | Original credits, license identifier, complete license/notice paths and inspected revision; asset/font rights and secondary lineage |
| Verification | Compatibility/probe/test evidence, local adaptations, known gaps, recovery and permitted update path |

Unknown dates and versions remain explicitly unknown with the missing evidence.
Never infer the last intake date from filesystem mtime, the current upstream
release, a general Git touch or this audit's date. A candidate never adopted
has no invented adoption date: trace the event rather than the file age.

Distinguish adopted/pinned revisions, supported versions, versions discovered
or installed during a dated run, and the currently available upstream release.
Do not claim they are the same or make transient installation state universal
durable truth. Dependency updates and documentation checks are different events.
Use existing intake/sync owners: organization grants no copying, installation,
policy waiver or automatic upstream update.

## Legacy decisions and forbidden output

Never write new files or in-place edits under `docs/superpowers/`.
This includes specifications, plans, research, index generation,
link repairs, normalization, temporary files and staging. New operational notes
belong in the owned run; durable documents use their approved canonical owner.
Keep historical references intact while deciding their disposition.

For each existing specification, plan, research document or other artifact there
that would be moved, merged, archived, retired or deleted:

1. Inventory its exact path and source snapshot/hash, purpose, owner evidence,
   links and attached files. Propose a precise destination and retained content.
2. Return a separate question for that document asking **whether to keep it and
   where to move it**. The coordinator records `ask` before asking the user and
   records `answer` in the user's exact words through `work-controller:work-record`.
3. Require an explicit human answer resolving retention and destination for
   that identified document before dependent work. Grouped presentation must
   still expose and record a decision for each named artifact.
4. Bind the answer to source identity, intended disposition and destination.
   Changed source bytes, ambiguity or a conflicting destination reopen the
   decision instead of inheriting an unrelated grant.
5. Only then perform an authorized preserving relocation or disposition.
   Verify retained content/links before removing the exact approved source.
   Do not create a redirect, replacement or new artifact in the forbidden root.

Global reorganization authorization, batch grants for unnamed documents,
silence, timeout, elapsed time, assumed approval and another worker's verdict are
not substitutes for those human answers. Temporary moves, archive and merge
are also dispositions; moving with a pointer cannot bypass this rule.
Permanent purge retains its separate scoped authorization and protections.

Preserve unanswered source bytes. While a decision is unanswered, do not move,
merge, archive, retire or delete it. Continue independent authorized work.
These future migration decisions are not prerequisites for creating the
organizer itself. Component creation never automatically migrates this directory.

## Execution and verification

Produce an owned inventory and file/audience/source-to-destination plan before
edits. Reuse existing authorization for unambiguous bounded changes and Work
Controller questions for mandatory legacy decisions. The organizer changes only
assigned files; existing writers/reviewers keep their responsibilities. Bind the
active host's actual dispatch and tools rather than inventing host primitives.

Before each move/merge, check current source bytes, destination confinement,
exclusive path ownership, retention mapping and human answers. Preserve foreign
and preexisting edits. Resolve missing ownership/evidence rather than silently
choosing a competing root. Shipped runtime resources and license notices stay
with their kernel owner even when documentation moves.

Verify meaningful dossier content, original-project links, intake fields,
retention ledger, source claims, anchors and generator parity. Deep reading,
static checks, experiments and installed-host probes remain separate. Unread
citations, missing dates and unexecuted tests remain visible gaps.

Deliver paths, hashes, applied/retained/open findings, decisions and checks in
the owned report. The coordinator verifies every delivery and completion gate.
Registration or an ended worker turn does not prove migration success,
scientific validity or mechanical tool confinement. This is an agent method,
not a new filesystem enforcement runtime.
