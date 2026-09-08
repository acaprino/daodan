---
name: probe
description: Single-worker output-contract probe, plus the two-worker coordination probe. TRIGGER WHEN: running the disposable Daodan host protocol probe.
---

# Daodan single-worker probe

Return exactly DAODAN_PROBE_OK.

Do not add commentary, formatting or any other text.

# Daodan two-worker coordination probe

When asked for the coordination probe instead, dispatch two workers, one with nonce `alpha` and one
with nonce `beta`. Use the `subagent` tool supplied by the `pi-subagents` package. If no such tool is
available in this session, say so rather than running the two workers in this one context: what the
probe measures is isolation, and one context cannot provide it.

Role body to supply inline to each worker:

```text
You are given exactly one nonce value. Return exactly NONCE=<value> and nothing else.
Do not read another worker's result.
```

Requirements:

1. Each worker runs in its own isolated context and never sees the other worker's result.
2. Run both workers in parallel when the host supports it. Fall back to serial dispatch otherwise.
3. Wait until both workers have delivered before returning anything.
4. Return the two nonce lines followed by `DELIVERED=2/2`.

State in `tests/host-probes/README.md` whether a subagent tool was present, and whether the hidden
role skill below was loadable by name.
