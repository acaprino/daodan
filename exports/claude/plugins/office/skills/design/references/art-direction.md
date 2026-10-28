<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
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

# Taste art direction inside Office

`office:design` owns this boundary. Use the required
`taste-skill:design-taste-frontend` skill for art direction when the operation
creates a new look. Resolve its actual registered identity and complete installed
skill folder on the active host; record the observed Taste v2 version, path and
consulted references in the existing DEPENDENCIES brief. Load the skill once in
this context and only the type/color/layout/imagery references needed for the
decision. Designers receive the resulting Office brief, not another full load.
An existing reviewer with an art-direction assignment reads the provider's
`references/critique.md` through that verified binding and applies the review
contract below. No separate Taste workflow or reviewer is started.

## Input and output

| Input from Office | Output back to Office |
|---|---|
| Settled operation, subject, purpose/audience, requested formats and autonomy | Two or three subject-specific visual directions, with distinct compositional ideas rather than recolors of one arrangement |
| Exact CONTENT project/revision, complete units, sources, claims and locks | Complete unselected `office/design/v1` payloads: `direction`, `palette`, `typography`, `spacing`, `imagery`, `data`, `components` and requested `adaptations` |
| Binding brand/template or inherited look, available assets, fonts and native/image capabilities | Candidate identities and asset requests using the existing image contract, with required resources and buildability gaps stated |
| Exact saved-native renders, candidate bindings and the same creative brief | Visible observations, concrete revisions and remaining uncertainty in the existing format review report |

Reuse the settled intake and editorial work. Taste does not change wording,
claims, sequence, depth, transformation permissions, selection authority or native
geometry. The Office contract bounds the loaded knowledge: do not run upstream
intake, copy/argument rewriting, direction-dealer/preset routing, web scripts,
servers, app mode or motion. Web house-style bans, image quotas and numeric beauty
scores are not Office gates. Binding brand and Office accessibility, source and
native requirements prevail; treat upstream aesthetic prescriptions as contextual
design hypotheses. An aesthetic reference is optional. Do not replace missing
Taste with an unrelated provider or claim a contribution that was not loaded.

## Native proposal and review contract

For new-look work the coordinator uses the existing declared format designers
and reviewers in `proposal` mode, then `final` mode after selection. Direct design
or theme work resolves the `/daodan:theme` entry's bindings; document/presentation
work uses its own entry or `/daodan:start`. This continues the same task.

In `proposal` mode, supply exact candidate IDs, design revisions/hashes,
unselected payloads, editorial working revision and representative unit/claim IDs.
Load the actual working content and validate each proposal with
`validate_design(..., require_selected=False)`. Verify content/source/projection
structure and identities without inventing a selected record or final binding.
For PPTX, copy the existing plan per candidate, fill its actual display values
and recompute the working canonical plan binding. Preserve claims, order and
editorial revision. These proof copies do not freeze final CONTENT.md.

Each requested format proves an opening and its actual hardest reading,
evidence/table/process job, within the one-to-three representative slots in
`records.md`. A cover alone cannot prove a content-heavy design. Designers return
their existing native specifications and image requests; the coordinator resolves
authorized assets, builds separate native specimens and renders the saved files.
Generated compositions and authored HTML can guide design but cannot replace
native proof or required editable content.

The existing format reviewer inspects every assigned candidate/frame. Check the
subject-specific idea, focal hierarchy, useful type/color/form/imagery, coherence,
compositional distinctness and difficult-content treatment against the brief.
Anonymous composition or ignored visual requirements is a creative failure even
when the file is readable. Name visible evidence, the failed intention and a
concrete fix; personal preference alone is advisory. Missing proof or visual
access is `blocked`. Repair failed proposals before the v2 gallery and selection;
do not ask the user to choose among failed directions. Bytes and metadata do not
prove artistic quality, render derivation, source fidelity or native editability.

`final` mode for newly planned composition requires selected DESIGN.md and finalized content/plan bindings,
then the normal full composition, saved-native review and preservation checks.
Review the actual delivered result as well as the proposal so translation does
not discard its identity. An inherited content-only change uses `records.md`'s
rebind procedure without new proposals. Narrow edits and read-only work do not
load a new direction or reopen intake; legacy source review needs no invented
retrospective records. An expressly requested art review may use
bounded critique without authorizing redesign. A quiet memo has no image quota.

## Missing provider

First satisfy the active host's required-package activation prerequisite. A
disabled required provider can block Office entry before any phase; follow the
host's actual recovery and keep its disabled-provider guard. Skipping creative
knowledge does not waive this activation prerequisite or make Taste optional.

After activation, unavailable Taste art-direction knowledge blocks only the
dependent art-direction assignment. Continue independent authorized work and report actual host recovery.
Claude and Codex have upstream native marketplace packages: register
`Leonxlnx/taste-skill`, then install `taste-skill@taste-skill` using the active
host's plugin mechanism. Other hosts require observed complete-folder provisioning
and registry resolution, not a claim that Claude installation commands work there:

| Host | Standalone skill location to verify |
|---|---|
| Copilot | `~/.copilot/skills/design-taste-frontend/` or project `.agents/skills/design-taste-frontend/` |
| Pi | `~/.agents/skills/design-taste-frontend/` or project `.agents/skills/design-taste-frontend/` |
| OpenCode | `skills/design-taste-frontend/` of the config directory the host reads (`OPENCODE_CONFIG_DIR` when set, otherwise `~/.config/opencode`) or project `.agents/skills/design-taste-frontend/`; verify the actual supported V2 registry |

Provision the complete upstream `skills/taste-skill/` folder, retaining its
references beside SKILL.md, under the host's actual installation authority.
Resource presence is not installed-host execution evidence. Do not install a
runtime or execute bundled scripts to read this art-direction knowledge.
