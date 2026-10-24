"""Senior-review policy stand-ins shared by the writer and the executor.

The real owner publishes the role catalog and the critical lenses. One copy
here keeps the selection gate and the routing floor in agreement.
"""

ROLE_CATALOG = {
    'senior-review:code-auditor': 'Trigger: every changeset.',
    'senior-review:security-auditor': 'User boundaries, authorization, sensitive data.',
    'senior-review:data-integrity-auditor': 'Persistence, partial writes, unique keys.',
    'senior-review:premise-auditor': 'Boundary conditions, defaults, sign handling.',
    'senior-review:temporal-resilience-auditor': 'Timers, retries, timeouts, background work.',
    'senior-review:ui-race-auditor': 'UI rendering, layout timing, event handling.',
    'senior-review:logic-integrity-auditor': 'State machines, transitions, invariants.',
    'senior-review:distributed-flow-auditor': 'Queues, webhooks, cross-service contracts.',
}

CRITICAL_ROLES = {
    'senior-review:security-auditor',
    'senior-review:data-integrity-auditor',
    'senior-review:premise-auditor',
}
