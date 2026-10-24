<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Agentit source and retained notices

`editorial-design` and `typography-and-layout` are modified source adaptations
from [marcmarti9/agentit](https://github.com/marcmarti9/agentit), pinned to
`fc38111622ac459ccf843234863bd0b8fcb6ebfd` (2026-10-23).
The original source paths are `skills/design/references/editorial-design.md (formerly skills/editorial-design/SKILL.md` and
`skills/design/references/typography.md (formerly skills/typography-and-layout/SKILL.md`. Agentit's Apache-2.0 terms are retained
in `LICENSE-APACHE-2.0.txt`. Office's own MIT license does not replace these terms.

| Original file | SHA-256 of source before adaptation |
|---|---|
| editorial-design/SKILL.md | `baef89d48234b609ecdd855ca8a898fad8ad67bb6479b5f96309ef0347bd4586` |
| typography-and-layout/SKILL.md | `7ba81bead11659a4efa946460553f32e5ae2b42a2968fb395bc5c14f750a959a` |

## Retained upstream lineage

Agentit's `THIRD_PARTY_NOTICES.md` and `skills/ADAPTATION_SOURCES.json` identify
source-informed MIT adaptations affecting this pair. Retain the following
notices with any redistribution of these adapted guides:

- **RampStack Co.**, Copyright (c) 2026 RampStack Co., MIT.
  Source: [rampstackco/claude-skills](https://github.com/rampstackco/claude-skills),
  revision `3d4510a94a76ead80122c691b5c480f92f3fbe40`.
  Agentit identifies brand-identity, design-system, creative-direction and
  art-direction material as inputs to its editorial adaptation.
  Exact retained terms: `LICENSE-rampstackco-MIT.txt`, copied from Agentit's
  `vendor/adaptation-licenses/rampstackco--claude-skills/LICENSE`.
- **Peter Bamuhigire**, Copyright (c) 2026 Peter Bamuhigire, MIT.
  Source: [peterbamuhigire/design-system-skills](https://github.com/peterbamuhigire/design-system-skills),
  revision `c9b334d770c449db7401730db29c9b70953e62f1`.
  Agentit identifies typography, font, editorial-layout, deck-system and related
  production guidance as inputs affecting both guides.
  Exact retained terms: `LICENSE-peterbamuhigire-MIT.txt`, copied from Agentit's
  `vendor/adaptation-licenses/peterbamuhigire--design-system-skills/LICENSE`.

These notices cover the imported scope. They do not import Agentit's wider
harness, its other skills, installers, execution policies or dependencies.

## Office modifications and sync boundaries

Modified descriptions, internal skill identities and production handoffs for
Office. Narrowed web-responsive guidance to native DOCX flow and fixed-canvas
PPTX objects. Added installed-font checks, source preservation, saved-candidate
render evidence, Office theme selection and the harness image-tool contract.
Reused existing briefs, designer/reviewer roles and production engines.
No upstream agent, browser workflow or artifact generator is required.

Track upstream changes as copied-source updates. Compare each original file at
the pinned revision with its new upstream version, then merge relevant guidance
into the local adaptation. Preserve these intentional boundaries, modification
notices, source attribution and all applicable license texts. Review upstream
lineage notices for new obligations before advancing the pin. Do not overwrite
the local files with raw upstream instructions or infer runtime verification
from a successful source merge.
