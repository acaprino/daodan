---
name: probe-worker
description: The probe's worker role, registered as a skill the model never sees listed. TRIGGER WHEN: dispatched by the Daodan two-worker coordination probe.
disable-model-invocation: true
---

# Daodan probe worker

You are given exactly one nonce value. Return exactly NONCE=<value> and nothing else.

Do not read another worker's result.
