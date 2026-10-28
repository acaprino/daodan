# Entry routing: pwa-expert

These lines are the entry workflows and knowledge of the `pwa-expert` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `pwa-audit-workflow`: TRIGGER WHEN: auditing a PWA, or verifying one is installable and production-ready.
- `pwa-checklist-workflow`: TRIGGER WHEN: checking PWA launch readiness, or walking a deterministic go/no-go list before deploying. DO NOT TRIGGER WHEN: an open-ended adversarial audit fits better (use pwa-audit-workflow).
- `pwa-scaffold-workflow`: TRIGGER WHEN: scaffolding, bootstrapping or adding PWA support to a Vite, Next.js, Angular, Nuxt or vanilla project.
