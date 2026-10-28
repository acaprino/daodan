<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

# Evidence and Probes

What to do when the vendor's documentation does not answer the question your design depends on.

This is the most common failure mode in a mature broker integration, and it does not look like a bug.
It looks like a decision: someone needed to know how the broker or the venue behaves, the documentation
was silent or ambiguous, a plausible answer was adopted, and the system was built on it. The answer was
never wrong in a way anyone could see, because nothing ever tested it. It surfaces later as an
incident, or as a mitigation built for a hazard that cannot occur, or as a mitigation removed for a
hazard that can.

The remedy is not more reading. It is a discipline about what counts as an answer.

## The evidence ladder

Rank every claim about broker or venue behaviour by how it was obtained. Record the rank next to the
claim. The ladder has **six ranks**.

| Rank | Source | Admissible as? |
|---|---|---|
| 1 | **Your own probe against the broker's own environment**, with the transcript kept | Proof, for the shapes you probed |
| 2 | **A direct read of a vendor documentation page**, quoted verbatim with its URL | Proof, if the sentence actually says it |
| 3 | **Vendor support or a ticket response**, in writing | Strong, but support contradicts itself across tickets |
| 4 | **The client library's source code** | Proof about the *library*, never about the broker |
| 5 | **Community claims**: forum posts, Stack Overflow, blogs | Hypothesis. Never a basis for a design decision |
| 6 | **A search-engine summary or an AI answer** | **Not evidence at any strength.** See below |

**Rank 6 is a trap with a specific failure mode**, and it has burned real integrations: a search result
summarises a page as containing a claim, the page is opened, and the claim is not there. The summary
synthesised it from surrounding context. A claim that cannot be located as a quoted sentence on the
page it is attributed to **does not exist**. Open the page. If the sentence is not in it, the question
is still open.

**Rank 4 is the one that feels stronger than it is.** Reading the client library is a genuinely good
way to learn what your program will do, and it settles questions about grading, retries, defaults and
which callback fires. It settles nothing about the broker. A library that classifies a code as fatal is
evidence that your process will treat it as fatal, and no evidence at all about whether the order is
still live at the venue. Keep the two questions separate in your notes, because the answers diverge
exactly when it matters.

**Silence is a finding.** "The documentation for this order attribute says nothing about how it behaves
on a partial fill" is a measured result worth recording, not a failed search. Record it with the date
and the URL checked, so the next person does not repeat the search and reach a different conclusion by
luck.

## Provenance tags

Tag every claim about broker behaviour in your own repository. Three tags are enough:

- **`MEASURED`**: a probe transcript exists. Note which shapes were probed. A result measured on one
  order type says nothing about another, and a result measured on one instrument class says nothing
  about another.
- **`DOCUMENTED`**: a verbatim quote and URL exist, with the date they were checked.
- **`ASSUMED`**: neither. This is not a defect; unmeasured assumptions are unavoidable. Hiding them is
  the defect. Every `ASSUMED` tag on a path that can move money is a queue item.

A decision record that cites an `ASSUMED` claim as its justification is a decision record that expires
the moment anyone measures.

## Designing a probe

A probe is an experiment, and the discipline is the same as any other experiment.

1. **State the claim so it can fail.** "Does this broker support attribute X" is not probeable. "An
   order of type T with attribute X on instrument I is accepted, or refused with code C" is.
2. **Use the cheapest instrument that can answer it.** Most acceptance questions are settled without
   risk by a validation-only or dry-run call, a capability query on the instrument, or a read-only
   metadata query. Reach for those first, and note that a capability list the broker publishes is often
   the answer for free.
3. **Escalate to a real order only for lifecycle questions.** Acceptance is what a shape is allowed to
   be; lifecycle is what actually happens over time, including staged transmission, transient states,
   the size of the verdict window and the interference of local configuration. Place it so it cannot
   trade, read every channel, cancel, and confirm the cancel landed.
4. **Change one variable at a time, and record the shape.** Instrument class, order type, time in
   force, attributes, account type, archetype, component version, client library version, broker, and
   account entity. A transcript that does not name its shape cannot be reused and cannot be reproduced.
   Broker and entity are the two that are easiest to leave out because they are easiest to take for
   granted. Broker is load-bearing whenever more than one broker can produce the transcript, which for
   an access path whose scope is `multi-broker-platform` is every time: a shape measured against one
   broker on that platform is not evidence about the next. Entity is load-bearing whenever the broker's
   own rules can differ by account entity or entitlement, which happens even on a `single-broker` path
   and is why naming the broker alone does not always finish the job.
5. **Identify the rejector when a local component is in the path.** Under `local-terminal` and
   `bridge`, re-run the probe with the component's configuration changed reversibly, then change it
   back. If the answer moves, the rejector is local rather than the broker. Never ship a dependency on
   the changed setting: behaviour that only works with a box ticked on one machine is not a property of
   your system.
6. **Respect the vendor's budget.** Validation and dry-run calls usually carry rate limits or courtesy
   limits, and probing is exactly the workload that violates them. A harness that fires shapes in a
   loop measures the throttle instead of the answer. Space the calls, cache the results, and treat the
   transcript as an artifact worth keeping so nobody re-probes what is already known.
7. **Keep the transcript in the repository.** A remembered result is rank 5 by the following week, and
   rank 6 by the time it is repeated to someone else.

Two asymmetries decide how much a probe result is worth:

- **A validation pass is not a guarantee of acceptance.** It is a check against the rules the broker
  can evaluate ahead of time. Refusals that depend on the state of the book, on local configuration or
  on timing can still refuse the real order.
- **A validation refusal is a real refusal of that shape**, and that is the direction of inference you
  can rely on.

## What a demo environment cannot settle

A demo, paper or simulated environment is the right place to run most probes, and it is worth being
precise about which questions it closes.

| It settles | Because |
|---|---|
| Protocol behaviour | Message shapes, event ordering and which channel carries what are the same code paths as live |
| Validation | The broker's pre-trade rules are applied by the same validator |
| Capability | What an instrument permits is read from the same reference data |
| Error codes | A refusal returns the real code with the real text, which is how you learn a code exists at all |

| It cannot settle | Because |
|---|---|
| Fills | The demo's matching is a simulation, and a simulated fill is the simulator's opinion of what would have happened |
| Latency | The path, the load and the hardware are all different, and none of them is the production one |
| Liquidity | There is no real book behind the quotes |
| Queue position | It follows from the real book, so it does not exist to be measured |

Everything that depends on those four inherits their status: partial-fill behaviour, slippage,
realistic stop triggering and any economics computed from them are all unsettled by a demo run,
regardless of how many times it worked.

One more asymmetry, and it runs opposite to the one above: **a demo environment can be more permissive
than live.** Entitlements, permissions, account type and available instruments frequently differ, so a
demo acceptance is weaker evidence than a demo refusal. A shape refused in demo is very likely refused
live. A shape accepted in demo still has to survive the account it will actually run under, and that
check belongs in the deployment plan rather than in the probe transcript.
