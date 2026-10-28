<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# License analysis: obligations, not a matrix

The wrong model is a compatibility table ("MIT: compatible with BSD, Apache-2.0; GPL-3.0: incompatible"). It is wrong in both directions: MIT/Expat code can legally live inside a GPL combined work (MIT is GPL-compatible), and two licenses a table calls "compatible" can still create unmet obligations in a specific distribution model. The canonical trap: GPL-2.0-only and GPL-3.0 are NOT intercompatible even though a naive table groups them as "GPL family"; only "GPL-2.0-or-later" bridges them.

The right model asks three questions per dependency, in order.

## Step 0: Establish the project's posture first

Before judging any dependency, record:

1. **Project license** (its own LICENSE file, not an assumption).
2. **Distribution model**: shipped binary or installable app; library published for reuse; SaaS / network service; internal-only tooling. Obligations hinge on this more than on the license pair.
3. **Linking/combination model** where relevant: static vs dynamic linking, separate process, build-time-only tool. Weak-copyleft obligations often turn on this.

If any of the three is unknown, the license section reports its findings conditionally ("if distributed as ...") and lists the missing posture facts as UNKNOWN.

## Obligation categories

Classify each dependency's SPDX identifier into a category; the category, not a verdict, is what the finding states.

| Category | Examples | Obligation sketch | Typical trigger |
|---|---|---|---|
| Permissive | MIT, ISC, BSD-2/3-Clause, Apache-2.0, Zlib | Preserve notices; Apache-2.0 adds a patent grant and NOTICE-file handling | Distribution |
| Weak copyleft | LGPL-2.1/3.0, MPL-2.0, EPL-2.0 | Source obligations scoped to the covered files/library; combination mechanics matter (linking, file-level) | Distribution |
| Strong copyleft | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0 | Combined work distributed under the GPL; full corresponding source on distribution | Distribution |
| Network copyleft | AGPL-3.0 | GPL obligations extended to users interacting over a network | Network use (SaaS counts) |
| Source-available / restricted | BUSL-1.1, SSPL, Elastic-2.0, Commons-Clause riders, "proprietary" | Read the actual grant; usage limits (competition clauses, production limits) may bind regardless of distribution | Varies; often use itself |
| Public-domain-like | CC0-1.0, Unlicense, 0BSD | Effectively no obligations | - |
| Unknown / custom | missing, "SEE LICENSE IN ...", nonstandard text | Cannot be classified mechanically | - |

## Finding format

Per dependency with a non-permissive category (or permissive with unusual mechanics, e.g. Apache-2.0 NOTICE files present):

```
<package> <version>: <SPDX id as reported> (<category>)
Obligation: <one sentence, e.g. "distributing a combined work triggers GPL-3.0 source obligations for the whole work">
Trigger: <distribution | network use | production use per grant | none in current posture>
Question for the owner: <the concrete decision, e.g. "is copyleft acceptable for the shipped CLI, or should this dependency be replaced?">
```

Wording rules, binding:

- Copyleft findings say "potential copyleft obligation: inspect combination/distribution model". They never say "incompatible with <project license>".
- A dependency whose obligations do not trigger under the recorded posture (e.g. GPL dependency in an internal-only tool, AGPL absent network exposure) is reported as informational with its trigger condition spelled out, not as a violation.
- Dual-licensed packages ("MIT OR Apache-2.0", "GPL-2.0 OR commercial") report both options; the project may choose either.
- Unknown/custom licenses go to a **requires legal review** list with the raw license string and the package's repository URL. No automatic verdict, ever.

## Tool caveats

- Manifest `license` fields are declarations, not guarantees. When a finding matters (copyleft, restricted, unknown), open the package's actual LICENSE file before reporting; note when declaration and file disagree.
- License inventory tools report the top-level declaration and can miss vendored code, dual licensing, or per-file exceptions ("GPL with classpath exception"). Treat tool output as TOOL-REPORTED for the declaration only; the obligation classification is INFERRED and says so.
- This analysis is engineering triage, not legal advice; the "requires legal review" list exists precisely because the final call on restricted and unknown licenses belongs to a human with legal context.
