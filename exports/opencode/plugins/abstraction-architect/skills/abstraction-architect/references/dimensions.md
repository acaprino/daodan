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

# Dimensions and Lenses

A **dimension** is a category a finding can belong to. Each one has its own proof rule. A **lens** is a criterion applied to every candidate of every dimension, reported as a field of the finding. A lens never becomes a category of its own.

Load `references/evidence-tracks.md` for the gates cited below.

## The seven dimensions

| | Dimension | Track | Proof rule |
|---|---|---|---|
| D1 | Duplicated domain knowledge | B | same policy, formula or invariant; two or more representations; they must stay consistent |
| D2 | Competing sources of truth | B | same fact; two or more authoritative writers or definitions; canonical owner absent or ambiguous |
| D3 | Redundant representation | B | same concept; parallel representations; real mapping or synchronization cost |
| D4 | Duplicated or derivable state | B | derivable but maintained separately, plus sync, invalidation or repair code |
| D5 | Missed unification | A | mechanism independently repeated three or more times; Rule of Three |
| D6 | Prior art available | A | a clearly canonical implementation exists and something else reimplements or bypasses it |
| D7 | Abstraction fitness | A | proven internal friction: flags, per-caller exceptions, caller bypass, leakage |

### D1. Duplicated domain knowledge

The same rule expressed more than once, usually without textual similarity.

```
OrderService:        if total > 1000 -> requiresApproval
CheckoutController:  if cartValue > 1000 -> managerApproval
InvoiceWorkflow:     highValue = amount > 1000
```

**Proof:** same concept, plus same decision, invariant or formula, plus different implementation sites. A grep finds candidates. The finding exists only after reading each context and demonstrating that they encode the same policy. Gates K1 to K6 apply.

### D2. Competing sources of truth

The same fact has more than one authority. This is more serious than duplication, and the question is not "are these similar" but "which one actually decides".

```
config/defaults.py     -> refund_days = 30
database.settings         refund_window
RefundPolicy.DEFAULT_DAYS = 30
```

**Proof:** same fact, plus two or more independent authoritative writers or definitions, plus no single canonical owner. Two is sufficient.

### D3. Redundant representation

The same concept modelled in parallel, with a real cost to keep the models aligned.

```
UserStatus enum   <->   AccountState enum   <->   CRMStatus mapping
```

Four types named after one concept are **not** automatically a finding. `CustomerDTO`, `CustomerEntity`, `CustomerResponse` and `CustomerEvent` may have entirely different boundaries and lifecycles, and usually do.

**Proof:** same fields, plus same semantics, plus same lifecycle, plus a continuous one-to-one mapping, plus no boundary-specific reason, plus changes that routinely propagate across all of them. Anything less is a legitimate boundary and reporting it is a false positive.

### D4. Duplicated or derivable state

Information that could be derived is instead stored, and the codebase carries the burden of keeping the copies aligned.

`cart.items` and `cart.total` is not by itself a defect. Materializing a total is often correct.

**Proof:** derivable, plus persisted separately, plus **evidence of the synchronization burden**:

```
recalculate_total()   update_total()   sync_total()   repair_cart_total()
```

plus more than one writer. The presence of repair code is the strongest signal, because repair code exists only where drift has already happened. A field being derivable is not evidence on its own.

### D5. Missed unification

A mechanism recurs and the codebase is asking for an abstraction that does not exist yet.

**Proof:** three or more independent occurrences encoding the same concern, gate A3 in its Rule of Three form. Consult `references/unification-patterns.md` for canonical shapes, remembering that the catalog is not an admission gate.

### D6. Prior art available

The abstraction already exists and part of the codebase does not use it.

```
CanonicalMoneyParser.parse()        exists, is clearly the owner
parse_money_again(...)              reimplements it elsewhere
```

**Proof:** one canonical implementation plus at least one reimplementation or bypass. No third occurrence is required, and demanding one is the misreading gate A3 exists to prevent. The strong evidence is not frequency, it is that an owner already exists.

D5 and D6 are adjacent and distinct, and the distinction changes the remediation:

```
D5 = the codebase is asking for an abstraction.        Remediation: design or consolidate.
D6 = the abstraction exists and is being bypassed.     Remediation: reuse, migrate to canonical.
```

### D7. Abstraction fitness

An existing layer is fighting its callers.

**Proof:** friction inside one abstraction. Flags accumulating on the signature, per-caller exceptions, callers bypassing it, vendor or implementation detail leaking through the public surface, parallel concrete implementations that route around it. No count of copies is involved. Consult `references/anti-patterns.md`.

**Boundary with `senior-review:code-auditor`.** A god function or a one-implementation interface that is fully visible inside the file under review belongs to that agent's Abstraction Inspector. D7 is the cross-file case: friction proven by external callers bypassing the layer, or by exceptions added for callers that live elsewhere. Do not re-flag what one file shows on its own.

## The four lenses

A lens is applied to every candidate and reported as a field. It never opens a finding by itself.

**L1 Change amplification.** If this concept changes, how many places must change together? This is the primary yardstick, and `references/theory.md` develops it as the single rule of thumb. Reported as the count and the list.

**L2 Indirection cost, Locality of Behaviour.** Would consolidating actually reduce cognitive cost, or only add another hop? This lens exists to stop the plugin proposing false remedies. A suggested direction that fails L2 is reported as a finding with an explicit note that the obvious unification is not the answer.

**L3 Bounded context.** A hard gate on track B, per gate K6. An important lens on track A but not an absolute gate, because two contextually separate call sites may still legitimately share an infrastructural mechanism.

**L4 Option price, Tidy First.** Does the benefit justify the abstraction today, or is deliberate duplication cheaper right now? This lens is what keeps the audit from being refactor-happy. A finding whose L4 verdict is "duplication is currently cheaper" is still reported, with that verdict stated, because the user may be waiting for a third occurrence deliberately.

## Occurrences are evidence, never severity

There is no mapping of the form two equals Low, three equals Medium, four equals High. Two independent authoritative permission policies can be High on two occurrences. Four duplicated formatting constants can be Low on four.

Severity follows consequence, calibrated in `references/decision-frame.md`. Occurrence count is reported as evidence strength and nothing else.

## Single primary classification

One defect gets one primary dimension.

A refund window duplicated in three places, one of which looks canonical, could be read simultaneously as D1, D2, D5 and D6. Four findings for one defect is a report bug, and it is the failure mode that makes conventional DRY tooling tiring to read.

Orienting precedence, applied as a principle and not as a rigid universal ordering:

```
D2 competing authority
  D4 duplicated state
    D3 redundant representation
      D1 duplicated knowledge
        D6 existing prior art
          D5 missed unification
            D7 abstraction fitness
```

The rule: **report the deepest architectural reason**, and record the others as supporting evidence or lens values rather than duplicate findings.

Worked example. Three implementations of a refund policy exist because three modules each consider themselves authoritative.

- Classified as D5, the finding says "we could extract a helper". True and shallow.
- Classified as D2, the finding says "nobody owns this policy". True and actionable.

D2 is deeper on the precedence, so D2 is the finding and the D5 observation becomes a line of supporting evidence. Extracting a helper without settling ownership would produce a fourth authority.

## The catalogs are not admission gates

The original defect this plugin was rebuilt to fix was not that its twelve unification patterns were infrastructural. It was that a catalog consulted as a matching step silently became the boundary of what could be found. Adding domain patterns fixes the coverage and reproduces the mechanism at a larger size unless the mechanism itself is addressed.

A candidate that passes its dimension's gate is a finding whether or not it matches a catalogued pattern. When it matches, cite the pattern. When it does not, name the concern in your own words and set the finding's `Pattern` field to `uncatalogued`.
