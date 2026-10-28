<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# Order Types, Time in Force, and Fill Modes

Which order types, liveness settings and fill modes exist, and how to find out which of them the
contract in front of you actually accepts.

The question "does IBKR support X" is almost always the wrong question. Support is **per contract, per
exchange, per account entity**, and IBKR publishes the answer in a machine-readable field that most
integrations never read. This file covers what the vocabulary means and how to resolve it for a real
contract instead of guessing.

## The capability list is a field, not a document

`ContractDetails.orderTypes` is a **comma-separated token list of everything that contract accepts**.
`ContractDetails.validExchanges` is the parallel list of venues. Both come back from
`reqContractDetails`.

The token list mixes three vocabularies that are conceptually distinct but delivered together:

- **Order types**: `MKT`, `LMT`, `STP`, `STPLMT`, `TRAIL`, `TRAILLMT`, `TRAILLIT`, `TRAILMIT`, `MIT`,
  `LIT`, `MOC`, `LOC`, `REL`, `SCALE`, `SNAPMID`, `SNAPMKT`, `SNAPREL`, `PEGMID`, `PEGBENCH`, `MTL`
- **Time in force**: `DAY`, `GTC`, `GTD`, `GAT`, `GTT`, `IOC`, `OPG`, `AUC`, `DTC`
- **Attributes and fill modes**: `AON`, `HID`, `SWEEP`, `POSTONLY`, `RTH`, `ACTIVETIM`, `DIS`, `OCA`,
  `COND`, `ALGO`, `WHATIF`, `CASHQTY`, `SIZECHK`, `PRICECHK`

**Read it before probing anything.** If `AON` is absent from the list for your contract, an All-or-None
refusal is the venue declining an unsupported attribute, not a precaution to bypass. If it is present
and the order is still refused, the refusal is about the *shape* (order type, TIF, size, or the
terminal's own settings) and probing is warranted.

Two cautions:

- The list is **per contract and per exchange**. The same symbol routed `SMART` versus routed to a
  specific venue can differ. The `orderTypes` you get back corresponds to the contract you asked about.
- **Presence in the list is not a guarantee of acceptance, and absence is only decisive for order
  types.** It is the venue's declaration of the vocabulary it understands. Combinations remain
  constrained, and the terminal layer can still veto. For TIF tokens the list **under-reports**:
  EUR.USD CFD declares no `IOC`, yet `tif=IOC` passes what-if validation on it (measured
  2026-08-13, at the same validation stage that refuses `FOK` with `201`). An absent order type is
  a no; an absent TIF goes to a what-if.

**Where simulated-versus-native is documented**: per exchange, not per order type. Each exchange's
listing page on the IBKR site carries an expandable "Order Types" section naming which types the venue
takes natively and which IBKR simulates; the trigger-method machinery applies **only to IB-simulated
stops** (a natively-held stop ignores `triggerMethod`), and Snap-to-Midpoint is documented as simulated
on every exchange. The simulation locus matters operationally: a simulated type is held by IBKR or by
your terminal rather than resting at the venue, so its behaviour depends on that process being alive
(see `reconnection-resilience.md`).

This is the first step of every capability question. The probe is the second, and
`venue-questions-and-probes.md` covers when it is warranted.

## Time in force: how long the order stays alive

| TIF | Meaning | Notes that bite |
|---|---|---|
| `DAY` | Dies at the end of the regular session | The default when the field is left empty. Leaving `tif` unset is not "no opinion"; it is a choice of DAY |
| `GTC` | Good til cancelled | Not universally native. See the simulation note below. **Documented as unsupported with IBKR algos**: pairing `algoStrategy` with `tif="GTC"` is a contradiction the catalogue rules out |
| `GTD` | Good til a date | Requires `goodTillDate`, and its time zone handling is a common source of surprise |
| `GAT` | Good after time | Requires `goodAfterTime`. The order is inert until then |
| `GTT` | Good til time | |
| `IOC` | Immediate or cancel | Fills what it can now, cancels the rest. Partial fills are expected, not exceptional: IBKR's worked example fills 400 of 1,000 and cancels 600. Documented for CFDs, and measured accepted on an FX CFD whose `orderTypes` does not declare it |
| `FOK` | Fill or kill | A documented `Order.tif` value in its own right ("if the entire order does not execute as soon as it becomes available, the entire order is canceled"), but its availability box reads **Options Only, US Products Only**. Measured 2026-08-13: refused with `201` ("The time-in-force FOK is invalid for this combination of exchange and security type") on an FX CFD and on a US stock alike. It never appears as a capability token in `orderTypes`, so the probe, not the token, is the test; `IOC` + `allOrNone` approximates it only where AON is itself supported (10236/10237 constraints apply) |
| `OPG` | At the open | Routed for the opening auction only |
| `AUC` | Auction | Venue-specific |
| `DTC` | Day til cancelled | Deactivated at session end rather than cancelled, and re-armed |

**The GTC simulation caveat is the one that produces silent surprises.** On venues where GTC is not
native, IB simulates it: the order is deactivated at session close and re-armed at the next open,
described as transparent to the client. What that order reports as *while deactivated*, and whether a
reconciliation snapshot taken in that window classifies it as working, is not documented. If your system
reconciles open orders on a timer across a session boundary, this is a measurement you owe yourself.
See `venue-questions-and-probes.md`.

**Leaving `tif` empty is a decision.** Value it explicitly on every leg of every order. A default that
differs from your intent is indistinguishable in the code from an intent you never had.

**A GTC condition does not survive the day it fired on.** IBKR documents that for a conditional order,
"unless the order is executed on the same day as the condition trigger, the condition has to be
retriggered again on the following day(s) for the order to become active". A conditional GTC is
therefore not a standing instruction that waits indefinitely for its condition to be met once: the
condition must re-fire on the day the order is meant to work. A strategy that arms a condition on
Monday and expects Tuesday's touch to execute it is relying on behaviour IBKR documents as absent.

## Fill modes and execution attributes

| Attribute | Type | Effect | Where it bites |
|---|---|---|---|
| `allOrNone` | bool | Do not fill unless the whole quantity can fill | Support is per contract and per order type; the availability box is Stocks, ETFs, Options, Bonds, EFPs, US products only. Refused with the undocumented `10257` on an FX CFD while accepted on a US stock, same session. Where it is supported, IBKR documents that it "will typically route to the native exchange, or hold the order if the AON order type is not supported by the primary exchange", simulating it under a stated condition for US stocks: the NBBO must qualify the limit price **and** its size must be at least the order size plus 1000 shares. An accepted AON is therefore a resting condition, not an execution promise. `10236`: a child must be AON if the parent is AON. `10237`: an AON ticket can route entire unfilled size only |
| `minQty` | int | Minimum acceptable fill size | Unset by default (`UNSET_INTEGER`), not zero. Narrow support: refused with the undocumented `10256` on a US stock and an FX CFD alike (measured 2026-08-13); the documented associations are Smart-routed options and bonds, and `350` refuses it for combos. `minQty=totalQuantity` would be AON in effect; neither probed class accepts it |
| `sweepToFill` | bool | Prioritise speed over price across venues | Equities-oriented |
| `blockOrder` | bool | Large-size block handling | Narrower than "large size" suggests: documented for **ISE option orders of at least 50 contracts**, US only, directed |
| `hidden` | bool | Not displayed in the book | Venue-restricted; some venues reject outright |
| `notHeld` | bool | Releases the venue from price/time obligation | Meaningful for `REL` and discretionary routing |
| `outsideRth` | bool | Eligible outside regular trading hours | If the order type or destination cannot honour it, TWS **ignores it and warns with 2109** rather than rejecting |
| `discretionaryAmt` | float | Hidden price discretion beyond the limit | Equities |
| `percentOffset` | float | Offset for relative order types | Only meaningful for the types that define it |
| `ocaGroup` / `ocaType` | str / int | One-cancels-all membership and reduction behaviour | See the OCA note below |

**`ocaType` values 2 and 3 mean "proportionately reduced in size" for OCA siblings when one of them
fills.** They act between members of the same OCA group. They are not a parent-to-child mechanism, and
the OCA documentation never mentions `parentId`. Do not reach for `ocaType` to solve a bracket sizing
problem; it does not address it.

**`advancedErrorOverride` is a string, not a flag.** Its declared type is `str = ""`, and IBKR
documents the accepted value: parameters obtained from `advancedOrderRejectJson`, the payload that
arrives with an advanced rejection (`trade.advancedError` in `ib_async`). Assigning a boolean sends a
nonsense string and proves nothing about whether an override was applied.

## Order types worth knowing precisely

- **`MKT`**: no price, immediate. On illiquid instruments this is how you discover the width of the
  book the expensive way.
- **`LMT`**: the workhorse. Price must satisfy the contract's minimum increment at your price band, not
  just `minTick`. See `contracts-and-instruments.md`.
- **`STP`**: becomes a market order when the trigger is touched. The trigger method itself is
  configurable and venue-dependent.
- **`STPLMT`**: becomes a limit order at the trigger. Safer on gaps, and can fail to fill entirely,
  which is the trade being made.
- **`TRAIL` and `TRAILLMT`**: trailing by amount or percent. The trail is maintained by IB, so the
  order's behaviour depends on IB's server-side state, not on your process being alive.
- **`REL` (Relative / Pegged-to-Primary)**: pegs to the NBBO with an offset. Commonly paired with
  `notHeld`.
- **`MIDPRICE`**: attempts to fill between bid and ask. US and SMART only.
- **`MOC` / `LOC`**: auction-only, with venue cutoff times that are not the session close.
- **Algos** (`Adaptive`, `TWAP`, `VWAP`, `ArrivalPx`, `DarkIce`, `Accumulate/Distribute`): delivered
  through `algoStrategy` and `algoParams`, gated by the `ALGO` token in `orderTypes`. GTC is documented
  as unsupported with them.
- **Scale orders**: one limit order that "automatically creates a series of buy (sell) limit orders
  with incrementally lower (higher) prices". Documented as "only available via TWS and the TWSAPI",
  so a scale strategy cannot be ported to the Web API. Its parameters have a dense refusal family of
  their own (`408`-`410`, `417`-`419`, `433`, `446`-`449`), which is the practical way to learn the
  constraints: the limits themselves are not published.

**Trigger methods matter for stops.** The price event that fires a stop (last, bid/ask, double bid/ask,
midpoint) is configurable per order and defaults differently per instrument class. Two systems with the
same stop price can trigger at different moments. Set it explicitly when it matters.

## How order type, TIF and attribute interact

There is no single global compatibility table, because the answer is a three-way function of order
type, venue and instrument, and IBKR does not publish it as a matrix. What exists is:

1. **`ContractDetails.orderTypes`** for the vocabulary that contract accepts.
2. **Refusal codes** that name the incompatibility when a combination is rejected, e.g. 2109 for an
   ignored `outsideRth`, 10236/10237 for AON constraints, 10268-10270 for retired attributes, `201`
   whose reason string names an invalid TIF for the exchange and security type, and the undocumented
   `10256`/`10257` pair for attributes the class refuses outright.
3. **`whatIf=True`** to test a specific combination without market risk.

The practical procedure, in order, for any "can I do X on Y" question:

1. Qualify the contract and read `orderTypes` and `validExchanges`.
2. If an order-type token is absent, stop: the answer is no for that contract on that exchange. An
   absent TIF token proves nothing (the list under-reports TIFs, and `FOK` never appears in it at
   all); TIF questions continue to step 3.
3. If present, build the exact order and submit it with `whatIf=True`. Respect the documented budget:
   at most one what-if per minute, roughly one per ten real submissions, and cancel it afterwards.
4. If the what-if passes but the real order is refused, suspect the terminal layer: presets,
   precautions, and messages. Discriminate with a reversible config change, and do not ship a
   dependency on it.
5. Record the result with the shape it was measured on. An answer measured on a `STP` parent says
   nothing about a `LMT` parent.

**Retired attributes are a real category.** `EtradeOnly` (10268), `firmQuoteOnly` (10269) and
`nbboPriceCap` (10270) are no longer supported and will refuse orders that still set them. Library
defaults have historically carried these; check what your library sends rather than what your code sets.

## Related

- `bracket-orders.md` - the bracket in depth: variants, TIF interactions, the documented silences
- `contracts-and-instruments.md` - `orderTypes` lives on `ContractDetails`, alongside the increment rules
- `error-codes-and-verdicts.md` - what a refusal code means, and what your library does with it
- `venue-questions-and-probes.md` - when to probe, and what counts as an answer
- `gateway-verification.md` - the prober that dumps this matrix for your own contracts
