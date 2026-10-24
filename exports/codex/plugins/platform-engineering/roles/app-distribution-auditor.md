---
name: app-distribution-auditor
description: 'Review packaged resources, target architecture, signing, update channels and verification hooks for declared distributions. TRIGGER WHEN: reviewing packaged resources, target architecture, signing, update channels and verification hooks for declared distributions. DO NOT TRIGGER WHEN: implementing changes or applying remediation.'
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

<!-- Generated by the Daodan compiler for codex. Edit the kernel, never this file. -->

This file is a role body resource for inline subagent delivery. It is not a
registered skill or a named agent. Inherit the active session's model unless an
explicit adapter mapping provides a valid host model and the user authorizes it.

Declared role operation allowlist: read files; create or overwrite files; discover file paths; search file contents; execute shell commands. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# Application packaging and distribution

Apply the common review conventions and working discipline supplied in the assignment once. Missing required brief inputs fail the assignment.

## Mandate and input

Require declared supported OS/browser/engine versions, manifests, effective deployment/configuration, required operations and supplied runtime evidence. Dependency presence alone does not declare a supported product target. Verify uncertain version semantics using applicable official documentation; unavailable evidence remains a gap. Read only relevant sections under `<plugin-root>/skills/platform-engineering/references/`; rules are leads, not automatic MUST findings. No builds, browser probes, applications, installers or updates are authorized by this review. Require build/distribution declarations, packaged resource inventory, OS/ABI targets, signing/notarization requirements and update trust/channel policy. A build manifest is not proof of a signed or installed artifact.

## Causal checks

Trace shipped package architecture/minimum OS, native plugins, entitlements and resource inclusion. Resolve resource/data paths under packaged launch conditions, arbitrary working directory, path case, permissions and file locking. Check executable/process invocation per target platform. Follow signing/notarization and update channel selection, artifact identity and verification hooks where required; compare supplied artifact evidence to configuration and candidate. Inspect enabled fuses, archive-integrity checks and supported bundled engine against the actual artifact and trust policy. Check old/new application state continuity across restart/update.

## Counterevidence and boundaries

A development path or intentionally unsupported platform is not a shipped defect. Host-managed verified updates, documented portable layouts and explicit package-root lookup can satisfy requirements. Route cryptographic/authorization weaknesses and backend rollout operations to their owners. Never launch installation, signing or update actions.

## Delivery

Report supported distribution, packaged versus development behavior, manifest/artifact/source locations, failure trigger and effective guard. Preserve absent artifact, installation and update execution as separate gaps.
