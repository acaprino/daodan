# Entry routing: stripe

These lines are the entry workflows and knowledge of the `stripe` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `/stripe:audit-webhooks`: TRIGGER WHEN: the user asks to audit or verify a Stripe webhook setup: endpoint configuration, signature verification, idempotency or event coverage.
