> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

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

<!-- Adapted from marcmarti9/agentit, skills/editorial-design/SKILL.md,
revision fc38111622ac459ccf843234863bd0b8fcb6ebfd (Apache-2.0).
Modified for Office native formats, production ownership and harness image tools.
See agentit-upstream.md for attribution, licenses and sync boundaries. -->

# Visual hierarchy for Office

This adapted reference owns visual hierarchy and reading furniture under the
assigned proposal or accepted `DESIGN.md`. `office:content` owns the reading job, claim relationships
and logical sequence; format designers own page flow or slide composition.
Use `typography.md` for type roles. Keep one existing brief and assigned format
design report, with explicit content/design revisions.
The creative input/output and proposal/final modes live in `art-direction.md`.

## Apply the accepted identity

1. Distinguish title, standfirst, headings, body, captions, callouts, notes,
   source lines and navigation through a small coherent hierarchy.
2. Provide entry and re-entry cues appropriate to the length and reading context.
   Keep source associations and figure/caption links visible; avoid ceremonial
   navigation in short work.
3. Give each figure a visual role consistent with its supplied communication
   purpose. Specify crop, emphasis and nearby explanation without changing facts
   or accepted wording. Native data remains editable when required.
4. Use whitespace, scale and image treatment to serve the accepted content.
   The DOCX/PPTX layout references supply native recipes and growth/geometry;
   do not repair overflow by silently rewriting or shrinking text.
5. Compare representative real content under each assigned candidate or selected theme and inspect
   actual saved-file renders for hierarchy, captions, contrast and navigation.
   The v2 gallery displays retained native renders; its metadata is not proof
   of their derivation or native properties. The v1 sampler is limited design intent.

## Production boundaries

DOCX uses flowing paragraphs, native headings, sections, lists, captions and
tables. PPTX uses a fixed canvas and explicit editable objects under
`${PLUGIN_ROOT}/skills/pptx/references/pptx-compatibility.md`.
A browser layout or reference image does not certify either native result.
Reusable templates need representative real content and proved engine support.

For imagery, return intent, references, crop, placement and alternative text to
the production coordinator under
`${PLUGIN_ROOT}/skills/pptx/references/image-tools.md`.
This method adds no image provider, worker or production engine.

For ordinary printing inspect the actual paginated export. Commercial press
claims also need the printer's process/profile, stock, trim, bleed, safety,
binding, ink limits and proof specification; absent those, label the concept
provisional. Record observed renders and unavailable checks separately.
