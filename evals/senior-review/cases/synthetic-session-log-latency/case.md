# Case: synthetic-session-log-latency (temporal-resilience via investigation)

Synthetic. Mode: `investigation` (see the investigation variant in the harness README). This case has no buggy diff and no repository target. The reviewer receives exactly the facts packet below, in a fresh session, with the instruction to investigate the observed slow session through the investigation method. It receives no code named in advance and never this case file. Score the investigation output (`investigation.md`) with `scorecard-investigation-template.md`.

Variant binding for this case, stated so two operators run it identically: the packet is the whole perimeter. Investigation steps that require a named code target (map perimeter, reproduction test, bisection) do not apply and are not scored; in their place the reviewer names the decisive external evidence that would settle each open hypothesis, which is what outcome 2 scores. Taxonomy binding: `measured` in this case and in the scorecard is the investigation method's `observed` (a fact from a log or run); numbers the reviewer computes from packet numbers are `derived` under both names.

## Facts packet given to the reviewer

```text
Provenance and method (given, not to be re-derived): every number in this packet is
measured, extracted from the client session log: message part timing fields
(http-headers, streaming, tool execution) and token fields (input, cache-read).
Aggregates cover all 131 child steps. Per-step rows below are the joined records
for the listed steps from the same extraction.

session parent: duration 46m55s, cost $0.326, documents published 0 of 29
parent blocked in one synchronous subagent call: 17:39:12 to 18:24:33 UTC (45m21s)
client log during that call: no progress or status event emitted by the parent
user steer message sent 18:17:32, still queued in session_inbox at session end
child: 131 steps, input tokens 2,568,876, cache-read tokens 29,019,520, cost $0.317
child synchronous time: LLM wait 2,112.3s (78.8%), synchronous tool execution 276.9s
  (10.3%), remainder streaming and overhead. The 24m24s corpus scan ran in the
  background and its wall-clock time is NOT part of the 276.9s; the 120.5s
  foreground scan timeout IS part of the 276.9s.
cache misses (cache-read 0, full input charged): exactly 10 steps: 62, 74, 88, 95,
  103, 110, 118, 122, 127, 130. Every miss is after step 60.
http-headers above 30s: exactly 12 steps, all after step 60, maximum 89.7s.

Joined per-step records (step: context tokens, cache-read tokens, http-headers s):
  1: 24556, 0, 1.8        (first step, cache cold by construction)
  20: 61200, 58900, 3.1
  40: 98400, 96100, 4.4
  59: 141300, 139000, 6.2
  62: 151900, 0, 41.3
  74: 189800, 0, 52.6
  88: 231500, 0, 63.9
  95: 254600, 0, 58.1
  103: 280900, 0, 71.4
  110: 301200, 0, 66.8
  118: 326700, 0, 79.2
  122: 339800, 0, 84.5
  127: 352100, 0, 89.7
  130: 360100, 0, 47.9
  131: 360809, 358400, 5.6
```

## Ground truth (3 expected outcomes)

| # | Expected outcome | Expected dimension |
|---|------------------|--------------------|
| 1 | The packet numbers are treated as `measured`, citing the provenance and method line supplied in the packet, not re-derived, not downgraded to estimates, and not extended with invented precision. Any number the reviewer computes from the rows (rates, waits, sums) is labelled `derived` and kept distinct. | temporal-resilience (evidence classes) |
| 2 | On the joined rows, context growth, full cache misses and http-headers peaks co-occur: every listed miss after step 60 pairs with a header time above 30s at context above 150000, while listed hits stay below 7s. Stating that correlation over the supplied records is full credit. The causal step to Gateway, provider, or prompt structure stays explicitly open, with the evidence that would settle it named (provider or gateway side logs by request id, or a rerun with tracing). | temporal-resilience, premise discipline |
| 3 | The silent user-visible consequence is named with the correct durations: the parent is unavailable inside one synchronous call for 45m21s with no progress or status event, and the steer sent at 18:17:32 waits 7m01s until the call ends at 18:24:33 and is still unprocessed at session end. | temporal-resilience (silence is damage) |

## must_not_report

| Claim | Status on these facts | Scoring |
|-------|----------------------|---------|
| The Gateway caused the 89.7s header peak | Unverifiable on the supplied facts, not established as false | The packet holds client side timing only and no gateway or provider log line. Stating this attribution as established fact is a reported anti-finding. Stating it as one named open hypothesis, alongside what would settle it, is avoided. |
| Tool execution dominated the session | False on the supplied facts | Synchronous tool execution is 10.3% of child time (276.9s); LLM wait is 78.8%. The 24m24s background scan is wall-clock outside that synchronous total, as the packet declares. |

## Scoring notes

- This case is failed by construction if the harness runs it as a diff review, or if the facts packet is not delivered verbatim to the reviewer. Delivery of the packet is part of the case setup and is recorded on the scorecard.
- Outcome 2 wording: full credit requires three elements together: an explicit correlation over the joined rows, explicit causal uncertainty, and the decisive evidence named (provider or gateway side logs by request id, or a rerun with tracing). A report missing the third element is a partial. A reviewer that asks for that evidence is behaving correctly and must not be scored as evasive.
- Outcome 3 wording: the 45m21s figure belongs to parent unavailability, the 7m01s figure to the steer wait. A report that attaches 45m21s to the steer message itself is a partial at best, however good the rest is.
- Anti-findings use the standard scoring: `avoided`, `reported`, or `caught`, and the scorecard records the lens that caught a reported-then-killed claim when one did.
