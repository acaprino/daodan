<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Word document types

A Word document is chosen by type, not by deck mode: a document is read alone,
at the reader's pace, and its structure is the argument. Choose one type in
the editorial projection from the reader and purpose settled at intake,
record it in CONTENT.md, and build and review against it. `office:content` owns
logical sequence; the catalog supplies document conventions. A
document derived from an existing one keeps the source's type unless the brief
changes its purpose. The `/daodan:presentation` argument modes (pyramid,
narrative, instructional, showcase, briefing) belong to decks and are not
mapped onto documents.

Each type names its reader and purpose, the section order, what the opening
must deliver, how headings are phrased, the usual length, and the native
construction that carries it. Lengths are bands for the brief, not caps: a
longer document of the same type keeps the same sequence and adds depth.

## Catalogue

| Type | Reader and purpose | Sequence | Opening | Headings | Usual length |
|---|---|---|---|---|---|
| **Decision memo** | An executive, board or client who must approve or reject one recommendation | Recommendation; the two to four arguments that carry it, each with its evidence; alternatives considered; risks; the decision requested and its deadline | The recommendation and its arguments in the first paragraph, so the title and first paragraph alone give the decision (the pyramid principle) | Each argument as a full sentence that states the point | 1 to 4 pages |
| **Briefing note** | A decision-maker or stakeholder who needs the state of a matter, for information or for decision | Issue in one sentence; background; current situation; considerations or options; recommendation or next steps; contact | A labelled `For information` or `For decision` line and the issue sentence | Fixed labels in a stable order (`Issue`, `Background`, `Considerations`, `Recommendation`), identical across editions | 1 to 2 pages |
| **Proposal** | A client or sponsor deciding whether to buy, fund or authorize | The reader's situation and need; the complication that makes action necessary; the proposed approach; deliverables and scope; schedule; team; commercial terms; acceptance and next step | Situation, complication and the one-sentence promise before any method (SCQA) | Reader-facing: what they get, not what the author does | 4 to 20 pages |
| **Report** | A reader who must understand findings and trust how they were reached | Executive summary; purpose and scope; method; findings in order of importance; discussion and limitations; conclusions; recommendations; appendices and references | An executive summary that stands alone and states the main findings and recommendations | Findings as statements of fact; method and discussion as topic labels | 6 to 40 pages |
| **White paper** | A professional reader weighing a problem and an approach, before any purchase | Problem and why it matters now; context and current approaches; the proposed approach and its evidence; implications; conclusion; references | Problem statement that names the reader's stakes | Argumentative, one claim per section | 6 to 15 pages |
| **Procedure (SOP)** | A person performing a task who needs to do it right every time | Purpose; scope; roles and responsibilities; prerequisites; numbered steps with expected results; exceptions and escalation; records; review and version control | Purpose and scope in two sentences, then who performs it | Imperative step labels, numbered; one action per step | 2 to 10 pages |
| **Handbook** | A reader who looks things up repeatedly, rarely reading cover to cover | Orientation and how to use the handbook; stable numbered topics, each self-contained; examples; troubleshooting; glossary; index or contents | A short orientation and a navigation device (contents, numbering) | Topic labels, stable across editions, numbered for citation | 20 pages and up |
| **Tutorial or guide** | A learner who follows along to reach one concrete result (Diátaxis: tutorial for the newcomer, how-to for the practitioner) | Goal and prerequisites; steps in order with what the reader sees after each; the completed result; where to go next | The goal and what the reader will have at the end | Step labels for how-to; lesson labels for a tutorial | 2 to 12 pages |
| **Policy** | Everyone bound by a rule, and the auditor who checks it | Purpose; scope and applicability; policy statements; roles; compliance and exceptions; related documents; definitions; approval and review history | Purpose and scope, then the statements; no narrative | Normative statements (`must`, `may`, `must not`), numbered for reference | 2 to 8 pages |
| **Minutes** | Participants and absentees who need what was decided and who owns what | Meeting identity (date, attendees, chair); agenda items in order, each with discussion summary, decision and actions; action register with owner and due date; next meeting | The meeting identity block and the decisions list | The agenda items as given | 1 to 4 pages |
| **Letter** | One named reader, external, for a formal purpose (offer, notice, cover, reference) | Sender and recipient blocks; date; subject; purpose in the first sentence; body; the request or next step; closing and signature | The purpose in the first sentence | None beyond the subject line; paragraphs carry the structure | 1 to 2 pages |
| **Image-led dossier** | A reader who evaluates work or evidence visually (portfolio, site survey, product dossier) | Short introduction; captioned plates in a deliberate order; interpretation where it adds to the plate; index | The introduction and the first plate on the same spread | Short plate titles; captions carry the content | 6 to 30 pages |

## Choosing between neighbours

- **Decision memo or briefing note**: a memo argues for one recommendation and
  closes with a decision request; a briefing note informs or presents options,
  and its labels never change between editions.
- **Report or white paper**: a report answers a question the reader asked
  (method, findings, limitations); a white paper argues a position the reader
  did not ask for and must be persuaded of.
- **Procedure or tutorial**: a procedure is performed by someone who already
  knows the system and must not deviate; a tutorial teaches, shows the result of
  each step and tolerates exploration. A reference handbook describes; it does
  not instruct.
- **Proposal or letter**: a proposal of one or two pages for a known client is
  still a proposal when it carries scope and terms; it becomes a letter when it
  only announces or requests.

## What the type decides and what it leaves open

The type fixes the section sequence, the opening and the heading voice above.
`layout-patterns.md` supplies the composition for it: opening pattern, page
types, table and figure treatment, template handoff. `office:design` supplies
direction, palette and pairing, shared with a deck made from the same brief.
Point sizes, line length, margins and page flow remain this format's choices
under `document-quality.md`.

For the design report, the designer records: type, the reader, the sequence
as it will appear in the document (with any section the brief drops or adds,
and why), the opening pattern, the heading voice, and the expected length band.
The reviewer verifies the delivered document against that record: a type whose
opening does not deliver what the table requires (a memo whose recommendation
is not in the first paragraph, a procedure whose steps are not numbered, a
policy with narrative in place of statements) is a blocking defect.

## Provenance

Original Office guidance. The decision memo follows Barbara Minto's pyramid
principle; the proposal opening follows the situation, complication, question,
answer pattern; tutorial, how-to, reference and explanation distinctions follow
the Diátaxis framework (Daniele Procida). Section orders for memo, briefing
note, report, procedure, policy and minutes follow common professional practice
and are not copied from any single source.
