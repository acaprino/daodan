---
description: 'Run the Daodan two-worker coordination probe.'
---

Dispatch two workers with the `subagent` tool, `agent: "probe:probe-worker"`, one with nonce `alpha`
and one with nonce `beta`, both with `background: true`. Wait for both completion notices before
returning anything.

Requirements:

1. Each worker runs in its own child session and never sees the other worker's result.
2. Wait until both workers have delivered before returning anything.
3. Return the two nonce lines followed by `DELIVERED=2/2`.

Then report, one line each: whether `skill({ id: "probe:probe" })` loaded (a skill ID with a
colon), whether `probe:probe-worker` was accepted as an agent name, and whether the two workers
ran concurrently. Arguments, if any: $ARGUMENTS
