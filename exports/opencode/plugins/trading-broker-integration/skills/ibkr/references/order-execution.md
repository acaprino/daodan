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

# Order Execution and Management

Placing orders, brackets, monitoring fills, reconciling positions. The principle is "anything you can do in TWS you can do via API"; the gotchas around state, races, and message rates are what make production hard.

## When to use

Submitting, modifying, cancelling, or reconciling orders. For market data subscriptions (which use the same event pattern), see `event-driven-data.md`. For what "placed" actually means and how the venue's verdict arrives, see `order-lifecycle-contracts.md`.

## Order shapes (just the most useful ones)

| Type | Code | Use |
|------|------|-----|
| Market | `MKT` | Immediate, accepts slippage |
| Limit | `LMT` | Price control, may not fill |
| Stop | `STP` | Trigger on breach |
| Stop-Limit | `STP LMT` | Stop + price protection |
| Trailing Stop | `TRAIL` | Dynamic |
| MOC / LOC | `MOC` / `LOC` | Market / Limit on close |
| Relative (Pegged-to-Primary) | `REL` | Pegged to the same-side primary quote plus offset |
| Midprice | `MIDPRICE` | Pegged to midpoint; US stocks via SMART only |

IB algos available too: Adaptive (Urgent/Normal/Patient), TWAP, VWAP, ArrivalPx, DarkIce, Accumulate/Distribute, PctVol.

## Gotchas

- **`orderStatus` is NOT guaranteed for every state change.** Market orders that fill instantly may never callback. **Always monitor `execDetails` as the authoritative fill source** -- not `orderStatus`. `orderStatus` messages are also sometimes duplicated (echoed from TWS, server, exchange) -- de-dupe in code.
- **Bracket order transmit pattern is positional.** Set `transmit=False` on parent and on every child *except the last*; only the last child has `transmit=True`. Submitting parent with `transmit=True` before the children = unprotected position. This is the #1 bracket-order bug.
- **Order ID management**: `nextValidId` arrives on connect; IDs must be unique positive ints, always greater than the last used. In multi-client setups, your IDs must exceed all open order IDs across clients. Error **103 (Duplicate order ID)** is one of the most common production errors. `ib.client.getReqId()` auto-increments safely.
- **`nextValidId` is also the startup gate and the session anchor.** IBKR documents that calls made before it fires can be dropped by TWS, and that the sequence persists between sessions: wait for it before subscribing or placing anything. `permId` is the venue's stable id across sessions; ib_async keys manually-placed TWS orders (`orderId <= 0`) by `permId` (verified on 2.1.0), so a clientId-0 session shared with a human can merge Trade objects when ids are handled loosely.
- **Orders staged with `transmit=False` never reach the IB server, and IBKR documents exactly how narrow they are**: "Untransmitted orders will only be available within that TWS session (not for other usernames) and will be cleared on restart. Also, they can be cancelled or transmitted from the API but not viewed while they remain in the 'untransmitted' state." So a staged bracket leg is invisible to `reqOpenOrders`, dies with the terminal, and is not shared with a second username. Keep your own record of staged ids, and call `reqOpenTrades()` after transmitting a leg mid-session so the library resyncs.
- **Modify only price, size and TIF.** IBKR's own guidance: "It is not generally recommended to try to change order fields aside from order price, size, and tif (for DAY -> IOC modifications)", and for anything else it says cancelling and replacing "might be preferable". The modify call must carry the same fields as the open order, `orderId` included, since that id is what identifies the target. Whether a given field change is amended in place or becomes a venue cancel/replace (with the queue-priority loss that implies) is **not documented per field**: measure it before building a strategy that repriced aggressively.
- **Cancel-fill race.** Between `cancelOrder()` and confirmation, a fill can happen. Sequence may be: cancel sent → execDetails (fill) → orderStatus(Cancelled for the residual). Never assume cancel succeeded until you've seen `Cancelled` or `Filled` in `orderStatus`.
- **Order Efficiency Ratio: <= 20:1** (submissions+modifications+cancellations vs executions). Exceeding generates warnings, then restrictions. Avoid rapid-fire modifications.
- **Message rate: 50 msg/sec to IB.** Exceeding causes disconnect (error 100). **Enable `+PACEAPI`** so TWS throttles instead of disconnecting:
  ```python
  ib.client.setConnectOptions('+PACEAPI')
  ```
  The documented formula behind the number is max market data lines divided by 2 per second (50/s at
  the default 100 lines). `+PACEAPI` addresses this message-rate limit only: no IBKR source says it
  paces the historical-data regime, and community reports agree it does not. Keep the historical
  throttle in your own code (`event-driven-data.md`).
  The two modes are documented and differ in consequence: in **reject mode** TWS answers a breach with
  error 100, and **"If the pacing limits are broken 3 times, the API session will terminate"**; in
  pacing mode TWS delays its acknowledgements instead. Three strikes is a session kill, not a warning
  ladder, so a burst-prone client belongs in pacing mode with its own throttle in front.
  Note what this limit is *about*: IBKR's page defines a request as a query submitted to retrieve
  data. No retrieved IBKR source states an orders-per-second cap, an identical-order guard, or the
  semantics of a "potential duplicate order" warning. Treat order throughput as unmeasured rather than
  as covered by the 50/s number.
- **`placeOrder()` with the same orderId = modify** -- not a new order. Cannot modify already-filled portions; cancellation may fail mid-fill.
- **Error 201 ("Order rejected") -- never auto-retry.** Always investigate. Common causes: price check failure, margin, exchange-specific rules, and (on retail EU entities) FX currency-leverage on a leveraged spot cross. Blind retry generates more 201s and burns through OER budget. The FX currency-leverage case is fixable by routing through CFDs: see `venue-boundary-failure-modes.md`.
- **Compliance 201s are NOT order precautions -- no override exists.** Precautions are a terminal GUI feature with their own codes (109, 163, 164, 382, 383), not the `10xxx` range (see `error-codes-and-verdicts.md`); account/compliance rejections like FX currency-leverage are hard rejections. Neither "Bypass Order Precautions for API Orders" in the Gateway config nor `Order.advancedErrorOverride` will let them through. Do not burn time on override paths: fix the contract type (spot -> CFD) or the account, treat the code as permanently non-retryable.
- **Bracket children (SL/TP) are `tif='GTC'` whenever the position can outlive the session; `DAY` children are defensible only where flattening before the close is guaranteed. The parent TIF is its own deliberate choice (`DAY` for session-scoped entries, `GTC` for structural levels -- see `bracket-orders.md`).** Two symmetric failure modes otherwise: DAY children expire at session end and leave an open position **naked overnight**; and children that survive the position (closed by an opposing fill or manually) rest as live orders on a flat contract, ready to open an unintended position. The invariant is *protections live exactly as long as the position*: GTC children for the position's lifetime, plus a **residual-child reaper** -- on a position-closed event for a contract now flat, cancel any bracket children still open on that contract. Caveat: this recipe can still be defeated wholesale by a terminal-side order preset (error 10349) -- see `order-lifecycle-contracts.md`.
- **Phantom `Cancelled` during staged bracket transmit.** With the `transmit=False` staging pattern, children can report a *transient* `Cancelled` status before flipping to `PreSubmitted` once the last child transmits. Do not emit a real cancellation event (or notify anyone) on that transient -- confirm against `reqOpenOrders()`/broker state before treating a staged child's `Cancelled` as real.
- **Prove capabilities empirically before writing code around an assumption.** The used-in-anger path: place the exact contested order against the **paper gateway** and read the venue's verdict (this is how "the spot-rejected order is accepted as a CFD with normal margin" was proven before a contract-type migration). `whatIf=True` submissions are a cheaper complementary probe: they return margin impact and commission without placing and surface hard rejections like a compliance 201 with zero market risk. Pair either with read-only `reqContractDetailsAsync` to prove a contract form resolves at all.
- **A successful `placeOrder` is "submitted", not "accepted".** IBKR accepts or rejects asynchronously via `errorEvent`, typically within a sub-second verdict window. If you do not subscribe `errorEvent` and route rejection codes into your order lifecycle, a rejected order silently dies while your system thinks it is live. De-duplicate the rejection against `orderStatusEvent`. See `venue-boundary-failure-modes.md` for the ingress pattern and `order-lifecycle-contracts.md` for the verdict-window contract.
- **Error 110 ("price does not conform to minimum price variation") kills a not-yet-working bracket.** On a parent still in `PendingSubmit`, the 110 cascades: the children then die with **error 135 ("Can't find order with ID")** because their parent no longer exists. `placeOrder` still returned success, so the strategy records a sent order while no live order exists. Snap every price to the increment in force at its price band (`ContractDetails.marketRuleIds` -> `reqMarketRule` -> the band containing the price), read from the ORDER contract's details -- `minTick` alone is a floor across all venues and can still earn a 110 (see `contracts-and-instruments.md`) -- and round bracket SL/TP *away* from entry. On an already-working order the same 110 is only warning-grade and the order stays live -- see `order-lifecycle-contracts.md`. Full tick-conformance treatment: `venue-boundary-failure-modes.md`.
- **Partial fills** populate `trade.fills` (each individual execution) and increment cumulative quantity -- adjust bracket child quantities if a parent partially fills before children become live. Each partial carries its own `execId`, and an exchange **correction re-delivers the same execution** with only the digits after the final period changed: a ledger that sums every `execDetails` double-counts corrected fills. See `order-lifecycle-contracts.md` for the append-only rule.
- **Price checks cancel rather than warn.** An order priced too far through the market comes back as `Cancelled` plus **202**, with IBKR's regulatory wording ("we cannot accept your order at the limit price ### you selected because it is too far through the market"). A softer variant caps instead of rejecting, and the capped level arrives as `mktCapPrice` on `orderStatus`. Both are venue-side verdicts on a price your code chose; neither is retryable unchanged.

## Bracket order skeleton (the pattern)

```python
def create_bracket(ib, contract, action, qty, entry, tp, sl):
    parent = LimitOrder(action, qty, entry)
    parent.orderId = ib.client.getReqId()
    parent.tif = 'DAY'          # entry may expire with the session
    parent.transmit = False

    opp = 'SELL' if action == 'BUY' else 'BUY'
    take_profit = LimitOrder(opp, qty, tp)
    take_profit.orderId = ib.client.getReqId()
    take_profit.parentId = parent.orderId
    take_profit.tif = 'GTC'     # protections must survive the session
    take_profit.transmit = False

    stop_loss = StopOrder(opp, qty, sl)
    stop_loss.orderId = ib.client.getReqId()
    stop_loss.parentId = parent.orderId
    stop_loss.tif = 'GTC'       # protections must survive the session
    stop_loss.transmit = True   # only the last child triggers transmission

    for o in (parent, take_profit, stop_loss):
        ib.placeOrder(contract, o)
    return parent.orderId
```

## Cancel-with-fill-race-awareness (composite local pattern)

```python
async def safe_cancel(ib, trade):
    ib.cancelOrder(trade.order)
    while trade.orderStatus.status not in ('Cancelled', 'Filled'):
        await asyncio.sleep(0.1)
    if trade.orderStatus.status == 'Filled':
        log.warning(f"Order {trade.order.orderId} filled during cancel attempt")
    return trade.orderStatus.status
```

## Position reconciliation (run on startup + periodically)

Positions are **account-level**; open-order visibility is **per-clientId**. With several clients on one account, differing order counts across clients are visibility, not divergence -- and never let multiple clients publish full account snapshots with replace semantics (see "Multi-Client State Hygiene" in `reconnection-resilience.md`). Real-time position deltas arrive via `positionEvent` -- whose handler signature must be contract-tested or it can silently never fire (see "Event Listener Contracts" in `event-driven-data.md`).

```python
async def reconcile_positions(ib, expected_positions):
    actual = await ib.reqPositionsAsync()
    for pos in actual:
        key = (pos.contract.symbol, pos.contract.secType)
        expected = expected_positions.get(key, 0)
        if pos.position != expected:
            log.error(f"POSITION MISMATCH: {key} expected={expected} actual={pos.position}")
    fills = await ib.reqExecutionsAsync()  # also catches fills during disconnect
    for fill in fills:
        log.info(f"Reconciled fill: {fill.execution.orderId} {fill.execution.shares}@{fill.execution.avgPrice}")
```

## Authoritative fill listener

```python
def on_exec_details(trade, fill):
    log.info(f"FILL: {fill.contract.symbol} {fill.execution.side} "
             f"qty={fill.execution.shares} price={fill.execution.avgPrice} "
             f"orderId={fill.execution.orderId}")

ib.execDetailsEvent += on_exec_details
```

## Paper Trading Caveats

Paper trading uses **simulated execution** from top-of-book only. Key differences:

- Order types not supported: VWAP, Auction, RFQ, Pegged to Market
- Stops and complex orders are always simulated -- behavior may differ from production
- Penny trading for US options is reported unsupported
- Simulator rejects residual of exchange-directed market orders that execute partially
- **Test in paper but never assume identical behavior to live.** The paper gateway is still the right place to *prove* venue verdicts empirically (see the probing gotcha above): rejections like compliance 201s reproduce faithfully there.

## Official docs

- Order types reference: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-ref/#order-types
- Bracket orders: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#bracket-orders
- Order status flow: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#order-status
- Error codes: https://www.interactivebrokers.com/campus/ibkr-api-page/tws-api-error-codes/

## Related

- `order-lifecycle-contracts.md` -- verdict windows, warning-vs-rejection grades, terminal presets, netted close paths
- `venue-boundary-failure-modes.md` -- async rejection ingress, tick conformance, FX-as-CFD routing, NaN-safe sizing
- `event-driven-data.md` -- the same event pattern for market data
- `reconnection-resilience.md` -- handling disconnect during open orders
- `tws-api-architecture.md` -- clientId strategy and PACEAPI option
