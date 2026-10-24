---
name: model-routing
description: >
  Select the model and effort for each LLM job through task_router.py, and refresh
  the model catalog and prices. TRIGGER WHEN: a coordinator routes an LLM job,
  or the catalog or prices need a refresh.
---

# Model routing

For per-request routing, confirmation and dispatch/resume, read `references/task-routing.md`.
For catalog, price or price-rule refresh, read `references/model-catalog-refresh.md`.
