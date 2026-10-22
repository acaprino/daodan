# Case: synthetic-single-turn-frontier (temporal-resilience, logic-integrity)

Synthetic. Setup is deterministic: start from an empty scratch repository, make one empty base commit, materialize exactly the two files below verbatim in a second commit, and treat that second commit as `review_rev`. The review scope given to the reviewer is literally `context/frontier.ts context/agent-loop.ts` (the diff of base to `review_rev`). The reviewer receives the materialized files and diff only, never this case file.

Semantics declared for the target, binding on the scorer: `compact(messages)` compacts only the prefix up to the frontier returned by `billionFrontier` at call time, replacing that prefix with a 20000 token summary. It cannot touch the suffix after the frontier. Whether the frontier ought instead to advance during autonomous work is the design question the ground truth answers; the fix direction itself is not scored.

## Buggy code

```ts
// context/frontier.ts
export type Message = { role: 'human' | 'assistant' | 'tool'; tokens: number }
export function billionFrontier(messages: readonly Message[]): number {
  const boundaries: number[] = []
  let total = 0
  for (const message of messages) {
    total += message.tokens
    if (message.role === 'human') boundaries.push(total)
  }
  return boundaries.length ? boundaries[boundaries.length - 1] : 0
}
export function compressionPressure(messages: readonly Message[], budget: number): 'none' | 'apply' {
  // Only the stable prefix up to the last human boundary may be compacted.
  const eligibleTokens = billionFrontier(messages)
  const totalTokens = messages.reduce((sum, m) => sum + m.tokens, 0)
  const estimatedSavings = Math.max(0, eligibleTokens - 20000)
  return totalTokens > budget && estimatedSavings > 50000 ? 'apply' : 'none'
}
```

```ts
// context/agent-loop.ts
import { compressionPressure, type Message } from './frontier'
// One delegated task arrives as a single human message, then the agent works alone.
export async function runDelegatedTask(task: string, steps: number, budget: number) {
  const messages: Message[] = [{ role: 'human', tokens: 24000 }]
  for (let step = 0; step < steps; step++) {
    messages.push({ role: 'assistant', tokens: 2600 })
    messages.push({ role: 'tool', tokens: 900 })
    if (compressionPressure(messages, budget) === 'apply') compact(messages)
  }
  return messages
}
// compact: replaces the prefix up to the current frontier with a 20000 token
// summary; the suffix after the frontier is never touched.
declare function compact(messages: Message[]): void
```

## Ground truth (1 bug)

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | Only the prefix up to the last human boundary is eligible for compaction, and the frontier is that boundary token offset. A delegated run with exactly one human message at the start keeps eligible tokens fixed at 24000 and estimated savings fixed at 4000, below the 50000 threshold, while assistant and tool messages grow total context by 3500 tokens per step without bound. `compressionPressure` therefore returns `none` on every step even as live context passes the budget many times over, and even an `apply` could only ever reclaim the frozen 24000 token prefix. Compression designed to trigger under pressure never triggers for the single-turn shape. | temporal-resilience (failure over time, silent degradation), logic-integrity (invariant: pressure triggers compression) |

## must_not_report

| Claim | Status on these facts | Why |
|-------|----------------------|-----|
| Multi-turn human conversations never compress | False at this revision | With later human messages the frontier advances to the newest human boundary, eligible tokens and estimated savings grow, and pressure past that boundary can return `apply`. The defect is specific to runs with one human message followed by long autonomous work. |

## Scoring notes

- Full credit requires the single human message precondition and the autonomous step loop in the trigger, plus the frozen eligible prefix mechanism (eligible 24000, savings 4000). Naming only the arithmetic in `frontier.ts` without the caller shape is a partial.
- The expected user-visible consequence is silence: no compression outcome, no warning, context and per-step latency grow until an external limit stops the run.
- The fix direction (advance the frontier during autonomous work, compact the suffix, or score pressure on uncompacted tokens) is not scored. Any recommendation is recorded as an observation, never as found or missed.
- Reviewers receive both files. A run that reviews only `frontier.ts` is a protocol violation by the coordinator, not a reviewer miss.
