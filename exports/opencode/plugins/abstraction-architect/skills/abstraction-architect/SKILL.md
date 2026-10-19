---
name: abstraction-architect
description: >
  Structural entropy knowledge base: canonical ownership, duplicated domain rules, redundant models and abstraction fitness.
  TRIGGER WHEN: deciding whether to extract, centralize or inline; asking who owns a rule or state; auditing duplicated knowledge or competing sources of truth under the audit method (references/audit.md, run by /daodan:check-health) or the reviews of /daodan:review-changes and /daodan:review-branch.
  DO NOT TRIGGER WHEN: formatting (use clean-code:readability-method), Python refactoring (use python-development:python-refactor-method), dead code (use senior-review:application-cleanup-method), security (use senior-review:security-auditor), or contract drift (use senior-review:api-contract-auditor).
---

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

# Abstraction Architect Knowledge Base

The question this knowledge base answers:

> Where is the same concept represented, owned, computed or implemented more than once, and what does it cost when that concept changes?

Structural entropy accumulates in ways that look locally reasonable. A support team implements an eligibility check because the domain one was hard to reach. A config value is added next to the code that reads it. A DTO is copied because the original had a field the new caller did not want. Each decision is defensible; the sum is a codebase where a single conceptual change touches nine files and misses two.

## The two evidence tracks

Everything here rests on one distinction, developed in `references/theory.md` section 9 and operationalized in `references/evidence-tracks.md`.

**The track determines the nature of the evidence. The dimension determines the gate.**

- **Form** is the same mechanism written more than once. The risk is premature extraction, the instrument is the count, and the Rule of Three is the gate for D5.
- **Knowledge** is the same fact holding more than one authoritative representation. The risk is drift between owners, the count is the wrong instrument, and two representations are sufficient behind a much stricter semantic proof.

The discriminating question for the knowledge track: **can these representations legitimately disagree?** If yes, there is no finding, whatever the surface similarity. If no, two is enough.

## When to use this skill

Load it when:

- Deciding whether to extract, centralize or inline
- Asking who canonically owns a fact, a policy, a threshold or a piece of state
- Auditing for duplicated knowledge, competing authorities, redundant models, or stored state that is derivable
- Evaluating whether an existing abstraction is paying for itself
- Running the audit method in `references/audit.md` (the structure dimension of `/daodan:check-health`), which spawns the auditor agent that loads this skill

Do not load it for the concerns listed in `references/scope-boundaries.md`, which names the owner of each.

## Reference index

Load on demand, not all up front.

| File | Read it when |
|---|---|
| `references/audit.md` | Coordinating the audit for a caller (the coordinator reads it; the auditor starts at `dimensions.md`): target forms, mode, scope, focus and index decisions, Codebase Map acquisition, concept index state, auditor dispatch and output location. |
| `references/dimensions.md` | Classifying a candidate. D1 to D7 with proof rules, lenses L1 to L4, the single-primary-classification precedence. **Start here.** |
| `references/evidence-tracks.md` | Deciding whether a candidate has enough evidence. Tracks A and B, gates `A1` to `A5` and `K1` to `K6`. |
| `references/concept-census.md` | Running a global audit. Seed map, concept extraction, the four search families, the Concept Evidence Index. |
| `references/concept-index-protocol.md` | Reading or writing `.abstraction-architect/concept-index.json`. Schema, freshness states, the script contract. |
| `references/decision-frame.md` | Promoting a candidate, calibrating severity, framing the remediation. |
| `references/unification-patterns.md` | Matching a form candidate. P1 to P12 infrastructural, P13 to P18 domain-facing. Not an admission gate. |
| `references/anti-patterns.md` | Judging D7. Twelve wrong-abstraction shapes, cited as `anti-pattern A1` to `A12`. Not an admission gate. |
| `references/scope-boundaries.md` | Deciding whether a concern belongs here at all. The five exclusions and their owners. |
| `references/theory.md` | Arguing a position, or when the user asks why this matters. Nine principles plus the single rule of thumb. |
| `references/further-reading.md` | Citing a source. Verified URLs. |

## The single rule of thumb

When this concern changes, where do you have to touch?

- If N grows linearly with features, the concern is a unification candidate.
- If every new requirement adds a flag, branch or parameter to a shared layer, that layer is a wrong abstraction.
- If N is greater than one and the sites must agree but nothing makes them agree, you have found a competing authority, and that is the more serious finding.

## Two rules that are easy to lose

> Structural simplification is the desired outcome of the audit, not a finding category.

> Patterns are discovery aids and classification examples, never an exhaustive catalog or a prerequisite for a finding.
