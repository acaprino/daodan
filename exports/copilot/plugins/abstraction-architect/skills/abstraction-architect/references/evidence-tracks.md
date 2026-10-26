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

# Evidence Tracks

Two kinds of evidence support a structural finding, and they are not interchangeable. Getting the wrong one produces either a noisy report or an empty one.

**The track determines the nature of the evidence. The dimension determines the gate.**

Track membership does not by itself impose a count. This is the single most common misreading, and it is worth stating twice: being on track A does not mean "three or more occurrences". Only D5 uses the Rule of Three as a strict gate.

| Track | Question it answers | Failure it guards against |
|---|---|---|
| A, form | Does the same *mechanism* recur, and would unifying it pay? | Extracting a shape from a sample of two and getting the wrong abstraction |
| B, knowledge | Does the same *fact* have more than one authoritative representation? | Two owners of one truth drifting apart, where waiting for a third is meaningless |

## Why the Rule of Three does not cover both

The Rule of Three protects against one specific risk: extracting a shape too early, with a sample of two, and producing an abstraction whose shape is anchored to a coincidence. It says nothing about the opposite risk, which is knowledge with two authoritative representations.

`references/theory.md` states the underlying reason: DRY targets duplicated *knowledge*, not duplicated lines. Two competing authorities over the same fact is already the defect. There is no third occurrence to wait for, and waiting produces exactly the drift the principle exists to prevent.

The Rule of Three therefore returns to its original meaning here: a gate that justifies **creating a new unification**, not a universal filter for the form family.

## Track A: form

Applies to D5 missed unification, D6 prior art available, D7 abstraction fitness.

```
A1  Same structural responsibility?
A2  Same lifecycle and boundary?
A3  Occurrences per the dimension's own rule
    D5: three or more independent occurrences (Rule of Three)
    D6: one canonical implementation plus at least one reimplementation or bypass
    D7: no count at all; friction inside a single abstraction is the evidence
A4  Would one shared abstraction reduce change cost?
A5  Is the divergence unlikely to be intentional?
```

Gate A3 is where the per-dimension rule enters. A D7 candidate that fails A3 because it has only one occurrence has been judged against the wrong rule: a wrong abstraction is a single object, and counting copies of it is a category error.

L3, bounded context, is an important lens on track A but not an absolute gate. Two contextually separate implementations may still legitimately share an infrastructural mechanism such as a retry policy or a logging facade.

## Track B: knowledge

Applies to D1 duplicated domain knowledge, D2 competing sources of truth, D3 redundant representation, D4 duplicated or derivable state.

Two representations are sufficient evidence. In exchange, the semantic proof is much stricter than a count.

```
K1  Same semantic fact?
K2  Same domain meaning?
K3  Same lifecycle?
K4  Same authority scope?
K5  If the fact changes, are both expected to remain consistent?
K6  Is there no legitimate bounded-context reason for divergence?
```

K6 is a **hard gate** on this track. A candidate that cannot demonstrate K6 is not reported. A candidate whose context membership could not be determined stays in Gaps with `Bounded-context exception: unverified`; it cannot be promoted until K6 is proven.

Failing to demonstrate any of K1 through K6 means no finding. Silence is the correct output when the proof is not there.

## The discriminating question

Every track B candidate resolves to one question, and it is the fastest route to the answer:

> **Can these representations legitimately disagree?**

If yes, this is not duplicated knowledge, whatever the surface similarity. If no, and they must stay consistent, two representations are enough.

Worked contrast:

```
Billing.REFUND_DAYS = 30            Shipping.Status: PENDING/COMPLETE/FAILED
Support.refundAllowed = age <= 30   Payment.Status:  PENDING/COMPLETE/FAILED

Can they legitimately disagree?     Can they legitimately disagree?
No. One policy, two owners.         Yes. Same shape, different knowledge.
FINDING (D1 or D2).                 NO FINDING.
```

The left column has no textual similarity and is a finding. The right column is textually identical and is not. A detector that matches on shape gets both backwards, which is precisely why this file exists.

## What the report must show

Every finding carries the track it was judged on and the gate results, so a reader can see why it was admitted:

```
Evidence track: KNOWLEDGE            Evidence track: FORM
Semantic identity: proven            Occurrences: 4
Occurrences: 2                       Independent implementations: yes
Must remain consistent: yes          Shared lifecycle: yes
Bounded-context exception: none      Rule of Three: satisfied
Canonical owner: ambiguous           Index-seeded: no
Index-seeded: <yes|no>
```
