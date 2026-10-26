---
description: 'Drafts a ready-to-post answer, with brand, tone, language, and sector flags. TRIGGER WHEN: the user pastes a customer review (Airbnb, Booking, Tripadvisor, Amazon, Trustpilot, App Store, Google) and asks for a reply or response. DO NOT TRIGGER WHEN: writing general marketing copy (use content-marketer).'
argument-hint: '\"<review text>\" [--brand <name>] [--tone formal|friendly|casual] [--lang <code>] [--sector hospitality|ecommerce|auto]'
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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

# Reply to Customer Review

## Invocation

Invoke the `review-reply-method` skill and follow its full workflow.

## Arguments

- `<review text>`: The customer review to respond to (paste inline or provide after invocation)
- `--brand "Name"`: Business name to use in the response sign-off
- `--tone`: Response tone -- `formal`, `friendly`, or `casual` (default: professional-empathetic, mapped to `friendly`)
- `--lang`: Force output language using ISO code (default: same language as the review)
- `--sector`: Force sector specialization -- `hospitality`, `ecommerce`, or `auto` for auto-detection (default: auto)

If invoked without arguments, prompts the user to paste a review.

## Examples

```
/digital-marketing:reply-to-customer-review "Camera sporca e personale scortese. Mai piu." --brand "Villa Serena" --tone friendly
/digital-marketing:reply-to-customer-review The app crashes every time I try to checkout. Uninstalling.
/digital-marketing:reply-to-customer-review --lang en "Prodotto arrivato rotto, assistenza inesistente"
/digital-marketing:reply-to-customer-review "Amazing stay! The view was breathtaking and the host was incredibly welcoming." --brand "Casa Luna"
```

## What it does

1. Analyzes the review: language, sentiment, severity, key points, sector
2. Generates an adaptive response calibrated to the review's tone and content
3. Outputs the response (ready to copy), analysis summary, and operational suggestions
4. Accepts follow-up refinements: "more formal", "shorter", "in English", etc.
