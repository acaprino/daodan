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

If the user asks for an HTML report, render this same template as a responsive page: the same headings, section order and table shapes, readable on a phone (tables may stack their cells) and in a light or dark theme. Interaction is allowed only where it works on the template's own content: editable weights that recompute the Overall row, collapsible name blocks, a filter on the Names removed table and tickable checkboxes in Before you commit. It adds no section, no chart and no text the Markdown version would not carry.

Trademark risk is a class from A (lowest risk) to D (highest) for three territories: the reference country, Europe and the world. NS means not screened and is never shown as A.

Scores are whole numbers from 1 to 5 (5 excellent, 4 good, 3 acceptable, 2 weak, 1 poor or disqualifying). Overall is the weighted average from Step 7, one decimal, between 1.0 and 5.0.

---

# Brand Naming Report: {project or brief in a few words}

**Brief:** {one sentence}
**Reference country:** {country} | **Nice classes assumed:** {list}
**Languages checked:** {list} | **TLDs requested:** {list} | **Date:** {YYYY-MM-DD}

## 1. Summary

**Recommended name: {Name}** (Overall {x.x} / 5)

{Two sentences: why this name ranks first, and the one thing to verify before committing to it.}

| Rank | Name | Overall | Trademark class ({country} / Europe / World) | Verdict |
|---|---|---|---|---|
| 1 | {Name} | {x.x} | {A-D or NS} / {A-D or NS} / {A-D or NS} | Recommended |
| 2 | {Name} | {x.x} | {A-D or NS} / {A-D or NS} / {A-D or NS} | {Strong alternative, or the reason it ranks lower} |
| 3 | {Name} | {x.x} | {A-D or NS} / {A-D or NS} / {A-D or NS} | {Strong alternative, or the reason it ranks lower} |
| 4 | {Name} | {x.x} | {A-D or NS} / {A-D or NS} / {A-D or NS} | {One-line reason} |
| 5 | {Name} | {x.x} | {A-D or NS} / {A-D or NS} / {A-D or NS} | {One-line reason} |

Class key: **A** no identical or similar mark found. **B** similar marks only in unrelated classes. **C** a similar mark in the product's class, or an identical mark in a related class. **D** an identical or near-identical mark in the product's class. **NS** a register did not answer.

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

A cell that rests on thin evidence reads `3 (unverified)`. A criterion whose check could not run at all reads `not scored` in every column and in its "Why it scores this way" row, and the Overall is divided by the weights of the scored criteria only. A trademark cell whose reference country is NS reads `3 (not screened)`.

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
| Domain {.tld} | {free, taken (active or parked), or not checked} |
| Online presence | {in use, free or not checked, one entry per kind checked: company or site, app, social account} |

**Trademark** (Nice classes {list})

| Territory | Class | Checked | Finding |
|---|---|---|---|
| Reference country ({country}) | {A, B, C, D or NS} | {national register: answered or not screened} | {Closest marks found, each as registered, pending or similar with its classes, or "none"; the page's own words if not screened} |
| Europe | {A, B, C, D or NS} | {EU register: answered or not screened (EU trade marks only)} | {Closest marks found, each as registered, pending or similar with its classes, or "none"; the page's own words if not screened} |
| World | {A, B, C, D or NS} | {international and US registers: answered or not screened} | {Closest marks found, each as registered, pending or similar with its classes, or "none"; the page's own words if not screened} |

The register names belong in section 7 (Evidence) only.

{One sentence: what to run before committing.}

**Market.** {Saturation level and the closest existing uses of the name, in one or two sentences.}

**Brand expression.** Wordmark: {font style and case}. Tagline: {tagline}.

**Main risk.** {One sentence.}

## 4. Runners-up

| Rank | Name | Overall | Description | Weakest criterion and why |
|---|---|---|---|---|
| 4 | {Name} | {x.x} | {One sentence} | {Criterion: reason} |
| 5 | {Name} | {x.x} | {One sentence} | {Criterion: reason} |

## 5. Names removed

Every name that does not reach the Scorecard is listed here, including names the user supplied that were dropped at a ranking step. A silent drop is an error.

| Name | Removed at | Reason |
|---|---|---|
| {Name} | {Step 1b, 3, 3b, 5 or 6} | {One-line reason} |

## 6. Before you commit

- [ ] {Each unscreened register, unverified TLD or unverified criterion, with the exact action the user should take}

## 7. Evidence

| Source | Status |
|---|---|
| Domain registries (RDAP) | {TLDs read, and TLDs not read because they publish no RDAP} |
| National register of the reference country ({register name}) | {answered, or NOT SCREENED with the page's own words} |
| EUIPO TMview | {answered, or NOT SCREENED with the page's own words} |
| EUIPO eSearch plus | {answered (EU trade marks only), or not used} |
| USPTO Trademark Search | {answered, or NOT SCREENED with the page's own words} |
| WIPO Global Brand Database | {answered, or NOT SCREENED with the page's own words} |
