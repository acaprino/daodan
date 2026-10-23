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

# Contracts and Instruments

Building the right `Contract` for each asset class, and reading the venue parameters that decide whether
an order is well-formed.

Most IBKR integrations are written against one asset class and quietly assume its rules are the API's
rules. They are not. Tick semantics, size semantics, the meaning of `multiplier`, which `whatToShow`
returns data, and whether qualification is even required all change per class. This file states what is
general and what is per-class, so a system written for one can be extended to another without inheriting
a false premise.

## The Contract object

The documented minimum viable structure is either:

- `conId` + `exchange`, or
- `symbol` + `secType` + `exchange` + `primaryExchange` + `currency`

Derivatives require more: `lastTradeDateOrContractMonth`, `strike`, `right`, `tradingClass`,
`multiplier`.

`primaryExchange` matters more than it looks. `SMART` alone is ambiguous for symbols listed on several
venues, and the ambiguity resolves differently over time. Pin `primaryExchange` for equities.

`tradingClass` is the discriminator between contracts that share a symbol and expiry, most visibly
weekly versus monthly options. Omitting it where it is needed returns several contracts, and
qualification will not choose for you.

Resolution mechanics worth knowing before blaming the venue:

- `reqContractDetails` accepts an under-specified contract and fans out one callback per match; every
  other call (orders, data) needs the contract already unique. Error **200** covers both "does not
  exist" and "not specified enough", and chain sweeps also produce **322** for combinations with no
  contract: expected noise there, not failures.
- A `currency` filter is geographic in practice: `reqContractDetails` with `currency='USD'` is
  documented to return **only US contracts**, even though non-US instruments trade in USD.
- `primaryExchange` takes only the part before a period for dotted venues: `ENEXT`, not `ENEXT.BE`.
- Corporate actions: a symbol can change while the `conId` persists (observed on split-plus-rename
  cases; key long-lived state on `conId`, never on symbol), and the TWS API exposes no structured
  corporate-action feed to say what happened.

## Per-class construction

`ib_async` ships convenience classes; the underlying object is always `Contract`.

| Class | Constructor | Required beyond symbol/currency | Notes |
|---|---|---|---|
| Equity | `Stock(symbol, exchange, currency)` | `primaryExchange` when SMART-routed | Fractional shares are a separate permission with their own refusal codes (most of 10243-10252) |
| Option | `Option(symbol, lastTradeDateOrContractMonth, strike, right, exchange)` | expiry, strike, right, often `tradingClass` and `multiplier` | Strike must exist. Discover, never construct, strikes |
| Future | `Future(symbol, lastTradeDateOrContractMonth, exchange)` | expiry or `localSymbol` | Expiry format is contract-month or a full date depending on the contract. `includeExpired=True` reaches expired futures (futures only) for details and history, documented to about two years back |
| Continuous future | `ContFuture(symbol, exchange)` | | **Historical data only**: documented as unusable for orders and for live market data, and `endDateTime` must be an empty string. Resolve to the front `Future` for everything else |
| Future option | `FuturesOption(...)` | as Option plus the future's parameters | |
| Spot FX | `Forex('EURUSD')` | | The API `symbol` is the base currency alone (`EUR`), with `currency` the quote. `FXCONV` is an order routing destination for balance conversion (no virtual position), not a contract field |
| CFD | `CFD(symbol, currency=...)` | | For FX-pair CFDs the split form is required: `CFD('EUR', currency='USD')` |
| Crypto | `Crypto(symbol, exchange, currency)` | exchange (`PAXOS` or `ZEROHASH`), currency (`USD`) | The same coin has a different `conId` per venue (BTC: 479624278 at PAXOS, 541686651 at ZEROHASH, documented), and accounts are not necessarily permissioned for both |
| Index | `Index(symbol, exchange, currency)` | | Data only, not tradable |
| Bond | `Bond(secIdType='ISIN', secId=..., exchange=...)` | an identifier | Its own details callback (`bondContractDetails`), and license restrictions leave few fields populated (documented: minTick, exchange, short name) |
| Warrant | `Contract(secType='WAR', ...)` | often `localSymbol` or `conId` | Documented for Dutch warrants and IOPTs: symbol plus expiry plus strike is insufficient; identify by `localSymbol` or `conId` |
| Combo | `Contract(secType='BAG', ...)` with `comboLegs` | legs with `conId`, `ratio`, `action`, `exchange` | See below |

**Qualification is not uniform.** `qualifyContractsAsync` is a no-op for a fully specified spot FX
contract, and mandatory for options, futures, CFDs and anything ambiguous. Two rules hold everywhere:

- A returned `conId` of `0` or negative is a **placeholder, not a contract**. Reject it and retry.
  Never cache it.
- **Clear the qualified-contract cache on every reconnect**, under the same lock as the fast-path read.
  Contract data can be dropped during a reconnect burst, and a stale cache outlives the session it was
  built for.

## Minimum price increments: `minTick` is not the increment

This is the most commonly mis-implemented rule in the API, and it produces error **110** on prices that
look correct.

IBKR's own wording: `ContractDetails.minTick` "specifies the smallest possible minimum increment
encountered on **any exchange or price**". It is a floor across every venue and every price band, not
the increment in force for your contract, on your exchange, at your price.

The actual increment comes from **market rules**:

1. `reqContractDetails` returns `ContractDetails.marketRuleIds`, a list parallel to the valid-exchanges
   list. Index into it with the position of your exchange.
2. `reqMarketRule(marketRuleId)` returns, on the `marketRule` callback, an array of `PriceIncrement`
   with `lowEdge` and `increment`.
3. The increment in force is the one whose `lowEdge` band contains your price.

Snapping to `minTick` when the band's increment is coarser produces a price the venue rejects. Snapping
to the band increment is correct everywhere, including for instruments with a single band.

Three further traps:

- **Read the increment from the ORDER contract's details, not the data contract's.** Where the two
  differ (a CFD traded against a spot contract used for data), their increments differ too.
- **`minTick` is unpopulated on a `Contract`.** It lives on `ContractDetails`. Reading
  `contract.minTick` off a qualified contract yields a default, and your rounding becomes a silent
  no-op.
- **FX and FX CFD market rules default to a coarser increment than 1/10 pip**, and the terminal can
  be switched to 1/10 pips (Global Configuration, Display, Ticker Row, "Allow Forex trading in 1/10
  pips"). IBKR's own page states the default inconsistently (1/2 pip in one bullet, 1/5 in the next),
  which is itself a reason to read the market rule rather than assert a number. The increment your
  orders must satisfy therefore depends on a GUI setting on the machine running the terminal. This is
  the same class of unversioned local input as order presets: audit it, and prefer reading the market
  rule at runtime over any table you maintain.

Two more increments hide near this one:

- **`tickReqParams.minTick` is a third number again**: the minimum increment of *market data* values,
  documented as legitimately different from the order-placement increment (combos: 0.01 for data
  versus 0.05 for orders). Never feed a data-side increment into order rounding.
- **`priceMagnifier` participates in the band lookup.** For pence-quoted and magnified contracts,
  divide the price by `priceMagnifier`, resolve the band, then multiply back (maintainer-grade
  procedure, not IBKR prose). For futures options, strike semantics changed at TWS 972: the magnifier
  no longer applies to FOP strikes.

Round with integer tick-steps via `Decimal`, validate the raw price, round, then re-validate. Round
bracket protective legs *away* from the entry and force at least one increment of clearance, so a
stop and an entry can never collapse onto the same price.

## Size semantics differ per class

`minSize` and `sizeIncrement` on `ContractDetails` do not mean the same thing everywhere, and reading
them as a universal venue floor is how dust orders and rejected orders both get produced.

- **Equities**: whole shares unless fractional trading is permitted for the account, the instrument and
  the order type. All three must hold; the refusals are distinct codes.
- **Futures and options**: integer contracts. `multiplier` is real and load-bearing for notional.
- **FX CFDs on SMART**: the reported minimum is **quantity precision** (on the order of 1e-7), not a
  venue floor. Applying it as a floor erases your lower bound.
- **Metal CFDs**: a real venue minimum, in the instrument's unit (ounces).
- **Spot FX on IDEALPRO**: precision, with real per-currency floors that are not in that field.
- **`multiplier` is `None` or `1` for FX and metals.** A canonical contract-size table is required; a
  multiplier fallback silently mis-sizes.

Consequence for sizing code: keep one canonical unit internally, convert to venue units only at the
wire, convert back on trade events, and treat a minimum as an **abort threshold**. A minimum that
rounds a degenerate input *up* turns a sizing bug into a live order.

## Option chains

Do not construct strikes. Request them:

```python
params = await ib.reqSecDefOptParamsAsync(
    underlyingSymbol='IBM', futFopExchange='', underlyingSecType='STK', underlyingConId=8314
)
```

`futFopExchange` empty means all exchanges. The response carries expirations, strikes, `multiplier` and
`tradingClass` per exchange, as **two flat sets**: IBKR documents that "it is possible there are
combinations of strike and expiry that would not give a valid option contract". Cross the sets, then
confirm each candidate by qualification, treating 200/322 refusals as expected noise. Sweeping chains
via `reqContractDetails` instead is documented as throttled and not recommended; where a large sweep is
unavoidable, unchecking "Expose entire trading schedule to the API" (Global Configuration, API,
Settings) is IBKR's documented way to shrink the per-option payload.

Two discovery utilities sit nearby, each with a documented limit: `reqMatchingSymbols` (fuzzy symbol
search, at most 16 results, minimum one second between calls; it names which derivative types exist,
not their terms) and `reqSmartComponents` (decodes the single-letter exchange codes of tick types
32/33/84 via the mapping id from `tickReqParams`, usable **only while the exchange is open**, so an
off-hours sweep fails for that reason alone).

Chains are large. Subscribing market data for a whole chain will exhaust market data lines immediately;
budget the subscription, or use snapshots and accept their billing.

## Combos and spreads

A spread is a `Contract` with `secType='BAG'` and a list of `comboLegs`, each carrying the leg's
`conId`, `ratio`, `action` and `exchange`. Two documented pricing rules constrain the design:

- **Per-leg pricing** (via `OrderComboLeg.price`, assembled into `Order.orderComboLegs`) is permitted
  only with **at most 2 legs**, and only on a **NonGuaranteed** spread.
- **More than 2 legs** must be priced as an overall order (`lmtPrice`) and **must not** be
  NonGuaranteed.

Leg `conId`s must be qualified first. A combo built from unqualified legs fails in ways that do not name
the leg at fault.

**Guaranteed is the default; non-guaranteed is opt-in and explicit.** Native exchange spreads are
guaranteed combos and that is the API default. A SMART-routed futures spread is the non-guaranteed
form, and IBKR states that "when placing an order for a non-guaranteed combo from the API, the
non-guaranteed flag must be set to 1", carried as a `TagValue("NonGuaranteed", "1")` in the order's
smart-combo routing parameters. The flag is what buys legging risk in exchange for routing: forgetting
it does not make a spread safer, it makes the order a different order than you designed. Attribute
refusals in this family are their own codes, e.g. `350` "Minimum quantity is not supported for best
combo order".

## `whatToShow` per class

| Class | Default | Notes |
|---|---|---|
| Equities, futures | `TRADES` | Historical `TRADES` bars are split-adjusted but **not** dividend-adjusted (documented); `ADJUSTED_LAST` adjusts for both, is documented for stocks, ETFs and options only, and requires an empty `endDateTime` like CONTFUT |
| Spot FX, FX CFDs | `MIDPOINT` | `TRADES` returns nothing; there are no prints |
| Options | `TRADES`, often thin | Illiquid strikes return sparse or empty series legitimately |
| Indices | `TRADES` | |
| Any class, spread analysis | `BID_ASK` | Counts as **2 requests** toward pacing limits |

An empty historical response is not an error. Distinguish "no data for this contract and setting" from
pacing and from duration caps before retrying.

## Data contract versus order contract

For some instruments the contract you trade and the contract you can get data for are different objects.
FX-pair CFDs are the clearest case: they trade, and they serve no market or historical data. The tell is
a `2127` immediately preceding a `366` *(observed diagnostic; 2127 is absent from IBKR's published
table)*; a lone `366` has other causes and deserves proof rather than assumption.

Where the split exists, resolve the underlying data-capable contract for every data path and keep the
tradable contract for orders. Then remember the increment rule above: read venue parameters from the
contract you are actually placing.

## Applicability: which failure modes bite which class

The traps documented in `venue-boundary-failure-modes.md` are not universal. This matrix says where to
look first.

| Failure mode | Equities | Options | Futures | Spot FX | CFDs |
|---|---|---|---|---|---|
| Tick conformance (110) via price bands | Yes | Yes | Yes | Yes | Yes |
| Data contract differs from order contract | No | No | No | No | **Yes** (FX pairs) |
| Minimum is precision, not a floor | No | No | No | Yes | Yes |
| `multiplier` absent, canonical size table required | No | No | No | Yes | Yes |
| Entity-dependent contract routing | Rare | Rare | Rare | **Yes** | **Yes** |
| Netted positions, no reduce-only | Account-dependent | Account-dependent | Yes | Yes | **Yes** |
| Session-reopen stub bars in history | No | No | Venue-dependent | **Yes** | **Yes** |
| Fractional-size refusal codes | **Yes** | No | No | No | No |
| Chain size exhausts data lines | No | **Yes** | Curve-dependent | No | No |

## Related

- `error-codes-and-verdicts.md` - what a refusal code means and what your library does with it
- `venue-boundary-failure-modes.md` - the adapter layer that builds these objects, and the FX,
  metals and CFD depth that the matrix above points at
- `order-types-and-attributes.md` - the capability vocabulary and how to resolve it per contract
- `event-driven-data.md` - subscriptions, bar construction, pacing
