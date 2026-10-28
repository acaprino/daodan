# Entry routing: opentelemetry

These lines are the entry workflows and knowledge of the `opentelemetry` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `otel-audit-workflow`: TRIGGER WHEN: the user asks to review, audit, or validate OTel instrumentation: span hygiene, context propagation, exporter config, sampling, async handling, attribute budgets, or AWS X-Ray / ADOT setup.
