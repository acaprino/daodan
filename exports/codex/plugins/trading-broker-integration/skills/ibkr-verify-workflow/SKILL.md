---
name: ibkr-verify-workflow
description: 'Answer a question about IBKR behaviour with evidence instead of a guess. TRIGGER WHEN: the user asks whether IBKR supports something, why an order was refused, what a code means, or wants a claim about venue behaviour verified against a real gateway. DO NOT TRIGGER WHEN: auditing a whole codebase (use /trading-broker-integration:ibkr-audit), or designing a system from scratch (use the ibkr-architect agent).'
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.
> Arguments: `[question, code, or contract]`. Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

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

<!-- Generated by the Daodan compiler for codex. Edit the kernel, never this file. -->

# IBKR Behaviour Verification

Resolve a question about how Interactive Brokers behaves, and report the answer with its provenance.

Load the `ibkr` skill, then follow the ladder below **in order**, stopping at the first rung
that produces a real answer. Say which rung you stopped at. Never skip a cheaper rung to reach for a
more impressive one.

## Rung 0: is it a code?

If the question is about a message code, answer immediately, with no gateway:

```bash
python "<plugin-root>/skills/ibkr/scripts/ibkr_probe.py" codes <code> [<code> ...]
```

Report the grade `ib_async` assigns it, and the consequence. The tool grades by ib_async's rule, not
by table membership: a code absent from the published table is still warning-grade if it sits in the
blanket range `[2100, 2200)` (2127 is the canonical example) or in `warningCodes` (492, 10167). For a
genuinely undocumented fatal code, say so explicitly: `ib_async` will mark a working order `Cancelled`
locally without telling the venue, so the order may still be live.

Then read `error-codes-and-verdicts.md` for which of the three layers refused: venue, terminal, or
client library.

## Rung 1: read the capability list

Most "does IBKR support X" questions are answered by `ContractDetails.orderTypes` for the contract in
question. This is free and definitive in the negative direction.

```bash
python "<plugin-root>/skills/ibkr/scripts/ibkr_probe.py" capabilities --stock AAPL
```

Requires a running paper Gateway (see Rung 3 setup). Report:

- whether the token is present in `orderTypes`
- the market rule bands, if the question touches prices
- the size semantics, if the question touches quantities

**If an order-type token is absent, stop.** The answer is no for that contract on that exchange, and
no probe will change it. An absent TIF token proves nothing: the list under-reports TIFs (EUR.USD CFD
declares no `IOC` yet accepts it at what-if, measured 2026-08-13) and `FOK` never appears in it at
all, so a TIF question continues down the ladder. A refusal is the venue declining an unsupported
attribute, not a precaution to bypass.

## Rung 2: read the documentation, and quote it

Fetch the page and **quote the sentence** that answers the question, with its URL.

IBKR's documentation serves clean Markdown: append `.md` to any page URL. The index is
`https://ibkrcampus.com/docs/llms.txt`, with per-section indexes such as
`https://ibkrcampus.com/docs/tws-api/llms.txt`. The rendered HTML site returns 403 to naive fetchers,
which is bot detection and not evidence of absence; use the `.md` form, or drive a browser.

Three rules:

- **A claim you cannot locate as a sentence on the page does not exist.** If a search result asserts
  something the page does not contain, the search result is wrong and the question is still open.
- **Silence is a result.** Report "the page says nothing about this, checked today at this URL" rather
  than filling the gap with a plausible answer.
- **Never cite a forum post or an AI summary as the basis for a design decision.** They are hypotheses.

## Rung 3: probe it

When the documentation is silent or the token is present but the order is still refused, measure it.

Set up a disposable paper Gateway if one is not running:

```bash
S=<plugin-root>/skills/ibkr/scripts
python $S/ibkr_gateway.py doctor
python $S/ibkr_gateway.py install
python $S/ibkr_gateway.py configure --user <paper-username>   # export IB_PASSWORD first
python $S/ibkr_gateway.py start
```

Then pick the probe that matches the question:

| Question is about | Probe |
|---|---|
| Whether a shape is accepted | `ibkr_probe.py shape --stock AAPL --type STP --tif GTC --attr allOrNone` |
| Which combinations work | `ibkr_probe.py matrix --stock AAPL --types LMT,STP --tifs DAY,GTC,IOC` |
| Lifecycle, states, attachment, TIF rewriting | `ibkr_probe.py bracket --stock AAPL --parent-tif DAY --child-tif GTC` |
| Prices, increments, size rules | `ibkr_probe.py capabilities --stock AAPL` |

(Substitute the contract selector for the instrument in question: `--stock`, `--forex`, `--cfd`,
`--future`, `--option`, `--crypto`, `--index`.)

Constraints to respect and to state in the report:

- **The what-if budget is IBKR's, not ours**: at most one per minute, roughly one per ten real
  submissions. The scripts enforce the spacing; do not pass `--no-budget` without saying why.
- **Paper only.** Live ports are refused and the account prefix is re-checked after connecting. If the
  user asks to probe a live account, decline and explain that a read-only capability dump against
  their production terminal is the closest safe equivalent.
- **A `REFUSED` verdict is trustworthy for that shape. An `ACCEPTED` verdict is a credit check
  passing**, not a promise: presets and book state can still refuse the real order.

## Rung 4: report as unresolved

If none of the above settles it, say so. A clear "unresolved, and here is the measurement that would
settle it" is a better deliverable than a confident guess.

## Output

Report in this shape:

1. **Answer**, in one sentence.
2. **Provenance**: `MEASURED` (probe transcript), `DOCUMENTED` (quoted sentence and URL), or
   `UNRESOLVED`.
3. **Scope**: which contract, which order type, which account entity the answer covers. An answer
   measured on a `STP` parent says nothing about a `LMT` parent, and this must be stated, not implied.
4. **Evidence**: the quote, or the probe output, or both.
5. **What follows**: which decisions in the user's system depend on this, and whether any of them now
   rest on a premise that just changed.
6. **Residual unknowns**, if the answer is partial, each with its cheapest settling experiment.

If the verification contradicts something the user already shipped, say that plainly and first. A
decision built on a premise that has now been measured false is the most valuable output this command
can produce.
