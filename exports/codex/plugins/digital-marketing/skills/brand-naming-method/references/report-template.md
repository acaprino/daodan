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

# Brand Naming Report Template

Fill this template for the final report of Step 8. Keep every heading, the section order and the table shapes. Replace each `{placeholder}`. Leave no field blank: write `unverified` when nothing supports a value and `not screened` when a register did not answer. Write the report in the language of the brief. Add no sections and no decoration, and keep prose to the sentence counts the placeholders give.

Scores are whole numbers from 1 to 5 (5 excellent, 4 good, 3 acceptable, 2 weak, 1 poor or disqualifying). Overall is the weighted average from Step 7, one decimal, between 1.0 and 5.0.

---

# Brand Naming Report: {project or brief in a few words}

**Brief:** {one sentence}
**Languages checked:** {list} | **TLDs requested:** {list} | **Date:** {YYYY-MM-DD}

## 1. Summary

**Recommended name: {Name}** (Overall {x.x} / 5)

{Two sentences: why this name ranks first, and the one thing to verify before committing to it.}

| Rank | Name | Overall | Verdict |
|---|---|---|---|
| 1 | {Name} | {x.x} | Recommended |
| 2 | {Name} | {x.x} | {Strong alternative, or the reason it ranks lower} |
| 3 | {Name} | {x.x} | {Strong alternative, or the reason it ranks lower} |
| 4 | {Name} | {x.x} | {One-line reason} |
| 5 | {Name} | {x.x} | {One-line reason} |

## 2. Scorecard

| Criterion | Weight | {Name 1} | {Name 2} | {Name 3} | {Name 4} | {Name 5} |
|---|---|---|---|---|---|---|
| Memorability | 15% | {n} | {n} | {n} | {n} | {n} |
| Distinctiveness | 15% | {n} | {n} | {n} | {n} | {n} |
| Market Saturation | 15% | {n} | {n} | {n} | {n} | {n} |
| Simplicity/Pronunciation | 10% | {n} | {n} | {n} | {n} | {n} |
| Relevance | 10% | {n} | {n} | {n} | {n} | {n} |
| SEO Potential | 10% | {n} | {n} | {n} | {n} | {n} |
| Domain Availability | 10% | {n} | {n} | {n} | {n} | {n} |
| Trademark Risk | 5% | {n} | {n} | {n} | {n} | {n} |
| Emotional Impact | 5% | {n} | {n} | {n} | {n} | {n} |
| Cultural Adaptability | 5% | {n} | {n} | {n} | {n} | {n} |
| **Overall** | 100% | **{x.x}** | **{x.x}** | **{x.x}** | **{x.x}** | **{x.x}** |

A cell that rests on no evidence reads `3 (unverified)`. A trademark cell for a name no register screened reads `3 (not screened)`.

## 3. Top 3 names

Repeat this block once per name, in rank order.

### {Rank}. {Name} (Overall {x.x} / 5)

**Description.** {Two or three sentences: etymology, meaning, how it sounds, and why it fits this brand.}

**Why it scores this way**

| Criterion | Score | Motivation |
|---|---|---|
| Memorability | {n} | {One sentence citing the evidence} |
| Distinctiveness | {n} | {One sentence citing the evidence} |
| Market Saturation | {n} | {One sentence citing the evidence} |
| Simplicity/Pronunciation | {n} | {One sentence citing the evidence} |
| Relevance | {n} | {One sentence citing the evidence} |
| SEO Potential | {n} | {One sentence citing the evidence} |
| Domain Availability | {n} | {One sentence citing the evidence} |
| Trademark Risk | {n} | {One sentence citing the evidence} |
| Emotional Impact | {n} | {One sentence citing the evidence} |
| Cultural Adaptability | {n} | {One sentence citing the evidence} |

**Availability**

| Check | Result |
|---|---|
| {.tld} | {AVAILABLE, TAKEN, or unverified (no RDAP service)} |
| {Social handles} | {Platform: free or taken, one entry per platform checked} |

**Trademark.** {Rating LOW, MEDIUM, HIGH or NOT SCREENED.} {Registers that answered, registers that did not and why, and what to run before committing.}

**Market.** {Saturation level and the closest existing uses of the name, in one or two sentences.}

**Brand expression.** Wordmark: {font style and case}. Tagline: {tagline}.

**Main risk.** {One sentence.}

## 4. Runners-up

| Rank | Name | Overall | Description | Weakest criterion and why |
|---|---|---|---|---|
| 4 | {Name} | {x.x} | {One sentence} | {Criterion: reason} |
| 5 | {Name} | {x.x} | {One sentence} | {Criterion: reason} |

## 5. Names removed

| Name | Removed at | Reason |
|---|---|---|
| {Name} | {Step 1b, 3, 3b, 5 or 6} | {One-line reason} |

## 6. Before you commit

- [ ] {Each unscreened register, unverified TLD or unverified criterion, with the exact action the user should take}

## 7. Evidence

| Source | Status |
|---|---|
| Domain registries (RDAP) | {TLDs read, and TLDs not read because they publish no RDAP} |
| EUIPO TMview | {answered, or NOT SCREENED with the page's own words} |
| EUIPO eSearch plus | {answered (EU trade marks only), or not used} |
| USPTO Trademark Search | {answered, or NOT SCREENED with the page's own words} |
| WIPO Global Brand Database | {answered, or NOT SCREENED with the page's own words} |
