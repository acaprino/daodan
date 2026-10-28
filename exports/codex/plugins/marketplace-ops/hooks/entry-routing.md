# Entry routing: marketplace-ops

These lines are the entry workflows and knowledge of the `marketplace-ops` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `marketplace-health-workflow`: TRIGGER WHEN: the user asks to validate marketplace.json, check plugin file references, report plugin counts and version status, or audit structural integrity. DO NOT TRIGGER WHEN: reviewing plugin content quality (use marketplace-review-workflow) or authoring new plugins.
- `marketplace-review-workflow`: TRIGGER WHEN: the user asks to review plugin, agent or skill quality, audit descriptions or trigger keywords, or evaluate activation accuracy and cross-plugin coherence. DO NOT TRIGGER WHEN: just validating marketplace.json structure (use marketplace-health-workflow) or authoring new components (use marketplace-scaffold-plugin-workflow).
- `marketplace-scaffold-plugin-workflow`: TRIGGER WHEN: the user asks to create a new plugin, bootstrap plugin structure, or add a new entry to marketplace.json.
- `skills-validate-workflow`: TRIGGER WHEN: the user asks to validate skill/agent quality, enforce trigger patterns, check description token budgets, or run pre-commit marketplace checks. DO NOT TRIGGER WHEN: checking structural JSON references only (use marketplace-health-workflow) or doing an AI-only content review (use marketplace-review-workflow).
