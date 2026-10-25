<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Integrity rules

`office_verify.py` applies these static rules. Each finding has a severity and a
fix class. Rules read the saved package only; nothing is rendered, recalculated or
validated against the OOXML schema.

| Severity | Meaning |
|---|---|
| `error` | The file is broken or shows a wrong result: blocks delivery |
| `warning` | A defect a reader or later editor will meet: fix or justify |
| `info` | Worth a look; often intentional |

| Fix class | What `fix` may do |
|---|---|
| `safe` | Apply mechanically through the engine; the content's meaning cannot change |
| `content` | Write new content that only describes what is already there (alternative text, a slide title taken from the slide's own heading) |
| `review` | Report with a proposed change; apply only when the user's request authorizes that specific change |
| `none` | Report only |

## All formats

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `package.invalid` | error | none | Unreadable, unsafe or structurally broken package (inspector errors) |
| `package.external-link` | warning | review | Content that depends on a target outside the file (hyperlinks excluded) |
| `package.macros` | info | none | Macros present; never run |
| `package.schema` | error | review | OpenXML schema validation failed (OfficeCLI `validate`, when installed; `.docx`, `.pptx`, `.xlsx` and macro variants only) |
| `package.schema-unavailable` | info | none | OfficeCLI was found but its validation did not run (unsupported type or tool error); the schema check stays unverified |

## Word

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `docx.broken-anchor` | error | review | Internal link to a bookmark that does not exist |
| `docx.alt-text-missing` | warning | content | Image without alternative text and not marked decorative |
| `docx.heading-skip` | warning | review | Heading level that skips a level (2 after none, 4 after 2) |
| `docx.tracked-changes` | warning | review | Unresolved tracked changes in a story |
| `docx.comments` | info | review | Comments left in the document |
| `docx.empty-paragraph-spacing` | info | review | Three or more consecutive empty body paragraphs used as spacing |

## PowerPoint

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `pptx.alt-text-missing` | warning | content | Picture without alternative text and not marked decorative |
| `pptx.empty-placeholder` | warning | safe | Placeholder with no content, which shows prompt text while editing |
| `pptx.off-slide` | warning | review | Top-level object extending beyond the slide canvas |
| `pptx.title-missing` | info | content | Slide without a titled title placeholder (outline and screen readers) |
| `pptx.hidden-slide` | info | review | Slide hidden in the show |

## Excel

| Rule | Severity | Fix | Detects |
|---|---|---|---|
| `xlsx.cached-error` | error | review | Formula whose stored result is an error (`#REF!`, `#DIV/0!` and the rest) |
| `xlsx.ref-error-in-formula` | error | review | Formula text that refers to a deleted range |
| `xlsx.broken-name` | error | review | Defined name that refers to a deleted range |
| `xlsx.inconsistent-formula` | warning | review | Formula that differs from identical formulas on both sides, compared in relative form |
| `xlsx.not-calculated` | warning | safe | Stored results the writer never calculated (`fullCalcOnLoad`, missing caches) |
| `xlsx.literal-error` | warning | review | Error value typed as a constant |
| `xlsx.hardcoded-constant` | info | review | Number other than 0 or 1 next to an arithmetic operator inside a formula |

## OfficeCLI as an independent checker

When [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) is installed (found as
`officecli` on `PATH`, through `OFFICECLI`, or given with `--officecli PATH`),
the verifier also runs its OpenXML schema validation and its issue scan, and
reports the issues as `officecli.<code>` findings (`review`). The report's
`checkers.officecli` names the binary used and `not_checked` drops "OOXML
schema validity" only when the validation actually ran. `--no-officecli` keeps
the run static. OfficeCLI reads `.docx`, `.pptx`, `.xlsx` and their macro
variants, not templates; on a `.potx`, `.dotx` or `.xltx` the schema check
stays unverified. Measured on 2026-10-25: it failed a deck of its own making on
`sldIdLst` order and passed DeckCraft's, so it is independent of the writer.

## Outside these rules

Text overflow, overlapping objects, pagination, font substitution, formula
correctness and circular references need an engine or a renderer; schema
validity needs OfficeCLI. The report names them under `not_checked`; the
workflow covers them with the engine and the format's reviewer, or reports
them as unverified.

## Provenance

The Excel categories follow the checks listed by the `audit-xls` skill in
[anthropics/financial-services](https://github.com/anthropics/financial-services)
(Apache-2.0), and the overflow and alternative-text categories follow the issue
types of [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI)'s `view issues`
(Apache-2.0). Rules, wording and code here are original; nothing is copied.
