---
name: dependency-audit
description: >
  Knowledge base for the evidence-first method: the per-ecosystem tool matrix, the obligations analysis model, and the verifiable signal catalog.
  TRIGGER WHEN: auditing dependencies for vulnerabilities, license obligations, outdated packages, or supply-chain risk in any ecosystem; loaded by the /dependency-audit:deps-audit command.
  DO NOT TRIGGER WHEN: dead-code or unused-dependency cleanup (use senior-review:code-review or typescript-development:knip), Python-only lint/type audits (use python-development:python-audit), or code-level security review (use senior-review:security-auditor).
---

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

# Dependency Audit Knowledge Base

Method for auditing third-party dependencies without inventing facts. The `/dependency-audit:deps-audit` command orchestrates; this skill holds the depth, split into references loaded on demand.

## Core principles

1. **Tool-first.** The audit runs the ecosystem's own tooling and reads registries and advisory databases (OSV, GitHub Advisories, RustSec, PyPA). It never re-implements a scanner in pseudo-code and never guesses what a tool would have said.
2. **Evidence tiers.** Every reported fact is `TOOL-REPORTED`, `INFERRED` (with the derivation stated), or `UNKNOWN` (with what would resolve it). Fabricated quantities of any kind are forbidden: no estimated hours, no invented percentages, no dollar figures.
3. **Non-destructive remediation.** Never `--force`, never unapproved major-version upgrades, never lockfile regeneration, never dependency replacement without first presenting the proposed change, its compatibility risk, and a test/rollback plan.
4. **Licenses are obligations, not a matrix.** License analysis asks what obligations a dependency's license imposes given how the project combines and distributes it. Binary "X is incompatible with Y" tables are wrong often enough to be banned.
5. **Honest coverage.** Missing tools and unreachable registries are reported as gaps, with install commands, instead of being papered over.

## References

| File | Load when |
|---|---|
| `references/ecosystems.md` | Selecting or running audit / outdated / license tooling for any ecosystem, or parsing its output |
| `references/license-analysis.md` | Writing any license finding, classifying an SPDX identifier, or answering a copyleft question |
| `references/supply-chain.md` | Evaluating supply-chain risk signals or reviewing a dependency diff for tampering |
