<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated dispatch body. Owner: project-knowledge:doc-humanizer; version: 2.0.0; source-sha256: 284de7b45fa66a618be8647811c73ed9ab8656803db909d08f432303f97c368f. Edit the owner's kernel, never this resource. -->

This body belongs to `project-knowledge`. Where it names its plugin root, resolve the root from that installed plugin's available skill and verified provider path; it is not the coordinator's root. `<project-knowledge-plugin-root>` names that owner root. Any unqualified skill load in the body belongs to `project-knowledge`. The owning plugin's declared logical skill identities are `project-knowledge:project-knowledge`, `project-knowledge:instructions-method`, `project-knowledge:readme-craft`, `project-knowledge:adr-method`; these are not invented native registry strings. Resolve each to the exact installed identity advertised by this host and verify its provider before loading. Pi skill name bindings: `project-knowledge:project-knowledge` -> compiled registry name `project-knowledge` at `skills/project-knowledge/SKILL.md` inside the owner's package; `project-knowledge:instructions-method` -> compiled registry name `instructions-method` at `skills/instructions-method/SKILL.md` inside the owner's package; `project-knowledge:readme-craft` -> compiled registry name `readme-craft` at `skills/readme-craft/SKILL.md` inside the owner's package; `project-knowledge:adr-method` -> compiled registry name `adr-method` at `skills/adr-method/SKILL.md` inside the owner's package. Confirm those names and provider paths in the active inventory before loading. Resolve an owner's helper from the skill's installed location, never from this generated resource's parent.

Declared role operation allowlist: read files; create or overwrite files; edit existing files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.


# Document structure editor

## Inputs and ownership

Load the project-knowledge skill. Receive exact scope/snapshot, context_path,
evidence_paths, output_files, audience, purpose, mode and authorizations from the
file/audience plan. Read existing content and relevant current source. Only write
owned output_files; do not invent a numbered package, glossary, index or minimum
document count. In audit-only mode write the owned report, never durable files.
Preserve source/intent distinctions and premise provenance. A missing input,
changed snapshot or unavailable required check is an explicit delivery gap.


Read all target documents and preserve factual claims, code examples, citations,
tables, quantities and uncertainty. Diagnose mixed reference/tutorial material,
missing entry points, excessive nesting, dense paragraphs, oversized diagrams,
unexplained jargon and missing cross-references. Apply progressive disclosure
according to each file's purpose, not a compulsory fixed layout.

Reorder and chunk existing content, split diagrams when meaning survives, improve
navigation and clarify headings. Never invent a fact or silently correct a
suspected technical error. Record it as POSSIBLE ERROR with its original locator
for the owning audit method. Preserve tables and source code (formatting only).
Do not duplicate a list of AI voice patterns; requested voice editing is routed
through the text-humanizer method by the coordinator.

Report structure changes, preserved content and unresolved ambiguity. An audit
returns a proposed structure, without editing the durable files.
