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

# Venue Questions and Probes

What to do when IBKR's documentation does not answer the question your design depends on.

This is the most common failure mode in a mature IBKR integration, and it does not look like a bug. It
looks like a decision: someone needed to know how the venue behaves, the documentation was silent or
ambiguous, a plausible answer was adopted, and the system was built on it. The answer was never wrong in
a way anyone could see, because nothing ever tested it. It surfaces later as an incident, or as a
mitigation built for a hazard that could not occur, or as a mitigation removed for a hazard that could.

The remedy is not more reading. It is a discipline about what counts as an answer.

## The evidence ladder

Rank every claim about venue behaviour by how it was obtained. Record the rank next to the claim. The
ladder has **six ranks**, unchanged from the vendor-neutral `broker-vocabulary` skill applied
here to IBKR.

| Rank | Source | Admissible as? |
|---|---|---|
| 1 | **Your own probe against a live or paper gateway**, with the transcript kept | Proof, for the shapes you probed |
| 2 | **A direct read of an IBKR documentation page**, quoted verbatim with its URL | Proof, if the sentence actually says it |
| 3 | **IBKR support or a ticket response**, in writing | Strong, but support contradicts itself across tickets |
| 4 | **The client library's source code** | Proof about the *library*, never about the venue |
| 5 | **Community claims**: forum posts, Stack Overflow, blogs | Hypothesis. Never a basis for a design decision |
| 6 | **A search-engine summary or an AI answer** | **Not evidence at any strength.** See below |

**Rank 6 is a trap with a specific failure mode**, and it has burned real integrations: a search result
summarises a page as containing a claim, the page is opened, and the claim is not there. The summary
synthesised it from surrounding context. A claim that cannot be located as a quoted sentence on the page
it is attributed to **does not exist**. Open the page. If the sentence is not in it, the question is
still open.

**Silence is a finding.** "The official bracket-order documentation says nothing about partial parent
fills" is a measured result worth recording, not a failed search. Record it with the date and the URL
checked, so the next person does not repeat the search and reach a different conclusion by luck.

## Provenance tags

Tag every venue-behaviour claim in your own repository. Three tags are enough:

- **`MEASURED`**: a probe transcript exists. Note which shapes were probed; a result measured on a STP
  order says nothing about a LMT order.
- **`DOCUMENTED`**: a verbatim quote and URL exist, with the date they were checked.
- **`ASSUMED`**: neither. This is not a defect; unmeasured assumptions are unavoidable. Hiding them is
  the defect. Every `ASSUMED` tag on a path that can move money is a queue item.

A decision record that cites an `ASSUMED` claim as its justification is a decision record that expires
the moment anyone measures.

## The probe instruments

### `whatIf=True`: the venue's verdict with no market risk

Setting `Order.whatIf = True` sends the order for a credit check instead of to a destination. The
estimated post-trade margin comes back on the `OrderState` in the `openOrder` callback. Equivalent to
TWS's "Preview" and its Margin Impact panel. In `ib_async`, use `whatIfOrderAsync(contract, order)`:
it registers the response future and returns the `OrderState`, whereas on the plain `placeOrder` path
the library discards the what-if response entirely and the `Trade` never sees a verdict.

It is also the fastest way to learn whether the venue will accept an order *shape*: attributes, contract
type, TIF combinations, price conformance. A refusal comes back as an error code without anything ever
resting on the book.

**IBKR publishes a courtesy budget for it, and it is tight.** Verbatim from the documentation:

- "keep the ratio: 10 order submissions: 1 what-if request"
- "do not overuse the what-if request (> 1 what-if request per minute)"
- "cancel the what-if order after margin review"

A probe harness that fires dozens of shapes in a loop violates all three. Space them, cache the results,
and treat the transcript as an artifact worth keeping so nobody re-probes what is already known.

Two limits to know before trusting a `whatIf` result:

- **A `whatIf` pass is not a guarantee of acceptance.** It is a credit check. Rejections that depend on
  the state of the book, on the terminal's own presets, or on timing can still refuse the real order.
- **A `whatIf` refusal is a real refusal of that shape**, and that is the direction of inference you
  can rely on.

### A paper order placed and cancelled

The used-in-anger path. Some behaviours only exist on a real submission: terminal preset interference,
staged bracket transmission, the transient states, the actual verdict window. Use a limit price far
from the market so nothing fills, place, read every channel, cancel, and confirm the cancel landed.

This is the only instrument that answers questions about *lifecycle*, as opposed to *acceptance*.

### `reqContractDetails` and `reqMarketRule`

Read-only, cheap, and the answer to every "what does this instrument actually allow" question:
permitted order types, permitted TIFs, valid exchanges, minimum increments per price band. Run it
before assuming an attribute is unsupported. If the contract details permit what your order was refused
for, the rejector is not the venue.

### A reversible terminal config change

The discriminator between "the venue refuses this" and "this terminal refuses this". Change one setting,
re-probe, change it back. Record the result. **Do not ship a dependency on the changed setting**: a
behaviour that only works with a checkbox ticked on one machine is not a property of your system.

## Writing an open question

Keep a register. One entry per unknown, deleted when answered rather than annotated, with the answer
moving into the durable reference. Each entry states three things:

1. **What is unknown**, precisely enough that a probe could settle it.
2. **What breaks while it stays unknown.** If nothing does, it is curiosity; deprioritise it honestly.
3. **The cheapest experiment that settles it**, named concretely.

The third item is what makes the register useful. An unknown without a proposed measurement is a
complaint.

Two rules keep the register honest:

- **A question answered for one shape is not answered.** "Refused on STP orders, CFD and spot alike" is
  a measured result about STP orders. Whether a LMT parent behaves the same is a separate entry until
  separately measured.
- **A decision already shipped on an unmeasured premise is a defect in the register, not just in the
  code.** Record which decisions depend on the entry, so the answer propagates when it arrives.

## Questions the documentation does not answer

These recur in every non-trivial IBKR integration. As of 2026-08-13 the reference documentation
settles none of them; the first now has a support-stated answer, recorded below. Each is listed with
the measurement that settles it, so you can answer it for your account and instruments rather than
inheriting someone's guess.

**Do bracket children activate on a partial parent fill?**
The bracket and API reference pages say nothing; checked directly, and that silence is real. The
answer now has documentation-grade support from outside the reference: an IBKR staff reply on the
Campus "Placing Complex Orders" lesson (2023-10-11) states children are held "until its parent fills"
and activate "once the parent order is completely filled". Grade it DOCUMENTED (support-stated) rather
than settled: verify for your account by logging `filled`/`remaining` on every fill event and reading
the children's state against the next real partial.

**Does TWS resize bracket children to the parent's cumulative fill?**
Same silence, same measurement. Note that `ocaType` values 2 and 3 ("proportionately reduced in size")
are **not** this mechanism: they act on OCA siblings when one of them fills, and the OCA documentation
never mentions `parentId`. If TWS does not resize, the client must, on the fill path, with a race
between the fill and the correction.

**What does `cancelOrder` guarantee?**
It is a socket write with no acknowledgement; the usual client-side transition is `PendingCancel`
(ib_async marks a staged `transmit=False` leg `Cancelled` directly instead). Unknown: what TWS does
with a cancel received while disconnected or mid-fill, and whether `PendingCancel` can persist without
reaching a terminal state. Settle it by killing the gateway mid-cancel on paper and reading the order's
state on reconnect. Note two documented constraints: the EClient API's `cancelOrder` takes an
`OrderCancel` object (ib_async wraps it: `cancelOrder(order)`), and **an API client cannot cancel an
order placed by a different client ID**; only `reqGlobalCancel` reaches those, and it cancels
everything.

**What does `avgCost` actually contain, per asset class?**
IBKR returns `avgCost` on `position` and `averageCost` on `updatePortfolio` without defining their
units anywhere: whether a future's is per underlying unit or contract notional, whether an option's
incorporates the multiplier, and whether either includes commissions. Every position-sizing and PnL
calculation downstream depends on the answer. Settle it by buying two lots at different prices with
non-zero commissions on a stock, an option with a known multiplier and a future, then comparing the
reported value against both the price-weighted and multiplier-adjusted computations, with the Flex
cost-basis field as the tiebreak. The same experiment answers the currency question: which currency the
PnL fields report in, and how a non-base-currency instrument is translated.

**Which order modifications amend in place, and which cost queue priority?**
IBKR documents *what* to modify (price, size, TIF) but never says, field by field, whether the venue
sees an amend or a cancel-and-replace. For a strategy that reprices while queued, that difference is
the strategy. Settle it by placing a displayed limit order in the book, modifying one field at a time
against an untouched control order, and comparing status sequences, exchange-side identity where it is
exposed, and fill priority. Modifying a **partially filled** order is a separate entry: IBKR's
modification page carries no warning about it, which is not the same as it being safe.

**Is callback ordering guaranteed across `openOrder`, `orderStatus`, `execDetails` and
`commissionReport`?**
IBKR documents that duplicate `orderStatus` messages are common and that a market order's execution may
not produce a `Filled` status at all, but publishes no ordering or completeness guarantee across the
four channels. Anything that reduces them into state must therefore be idempotent and key-based rather
than order-dependent. Settle the actual behaviour for your account by stamping arrival sequence and
time on all four during partial-fill bursts, cancel-versus-fill races and reconnects.

**Is there an order-rate limit distinct from the 50-requests-per-second message rate?**
The documented pacing page counts *requests for data*; no retrieved IBKR source states an
orders-per-second cap, a duplicate-order guard, or the semantics of a "potential duplicate order"
warning. Settle it by isolating order placement, modification and cancellation bursts from data
requests and recording where acknowledgement latency, warnings or a session termination appear. Note
the documented cost of getting it wrong in reject mode: three pacing breaches end the API session.

**Does a terminal-simulated stop survive its terminal?**
Simulated order types are held by TWS/Gateway or IBKR rather than resting at the venue. Undocumented:
whether a simulated stop re-arms after a hard terminal crash, or simply does not exist until the
process returns. Settle it on paper: place a simulated stop and, where the venue offers one, a native
stop, kill the terminal, drive the price through the trigger, restart, and read both orders' states.
While unmeasured, treat a dead Gateway holding simulated stops as an unprotected position
(`reconnection-resilience.md`).

**What does GTC do at a session boundary?**
On venues where GTC is simulated, IB deactivates the order at session close and re-arms it at the next
open, described as transparent to the client. Unobserved: what the order reports as while deactivated,
and whether a reconciliation snapshot taken in that window sees it as working. Settle it by leaving a
far-from-market GTC order on paper across a session close and reading its status either side.

**Is an order attribute refused universally or only for certain shapes?**
Attribute refusals are frequently order-type-specific and contract-specific. The wording "may not be
specified for **this** order" is a hint that the refusal is scoped. Probe the attribute against each
order type you actually use before concluding it is unavailable. Note that IBKR's published table does
document AON constraints (10236 "Child has to be AON if parent order is AON", 10237 "All or None ticket
can route entire unfilled size only"), which is evidence the attribute exists on brackets under
conditions, and that a refusal is about the shape rather than about support.

**What is the real minimum increment at my price level?**
`ContractDetails.minTick` is documented as "the smallest possible minimum increment encountered on any
exchange or price". It is a floor across everything, not the increment in force for your contract on
your exchange at your price. See `contracts-and-instruments.md`.

## Related

- `error-codes-and-verdicts.md` - grading a code you have never seen
- `contracts-and-instruments.md` - market rules, increments, per-class contract construction
- `gateway-verification.md` - the tooling that runs these probes against a disposable paper gateway
- `order-lifecycle-contracts.md` - the verdict window, and what `placeOrder` returning proves
