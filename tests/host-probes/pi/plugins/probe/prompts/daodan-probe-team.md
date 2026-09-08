---
description: 'Run the Daodan two-worker coordination probe.'
argument-hint: '[nonce-prefix]'
---

Run the two-worker coordination probe described in the `probe` skill of this package.

Report, in this order: the two nonce lines, `DELIVERED=2/2`, whether a `subagent` tool was
available, and whether `/skill:probe-worker` resolved even though the skill declares
`disable-model-invocation`.
