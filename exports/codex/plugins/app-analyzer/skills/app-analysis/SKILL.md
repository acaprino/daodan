---
name: app-analysis
description: >
  Report templates for the app-analyzer teardown: the competitive analysis, the user-flow diagrams and the visual HTML report.
  TRIGGER WHEN: writing the Phase 2 reports of an app-analyzer run ({APP}_ANALYSIS.md, {APP}_USER_FLOWS.md, {APP}_REPORT.html).
  DO NOT TRIGGER WHEN: exploring the app itself (that is the app-analyzer agent's Phase 1), or auditing a codebase rather than a running product.
---

# App analysis reports

The `app-analyzer` agent reads this skill when it writes its Phase 2 deliverables. The templates live in `references/report-templates.md`:

| Deliverable | Template section |
|---|---|
| `docs/{APP}_ANALYSIS.md`: structured competitive analysis | `## ANALYSIS.md` |
| `docs/{APP}_USER_FLOWS.md`: Mermaid flowcharts of the key journeys | `## USER_FLOWS.md` |
| `docs/{APP}_REPORT.html`: visual report with a screenshot gallery | `## REPORT.html` |

Fill every placeholder from what the run observed. A section the run has no evidence for says so; it is never filled with a guess.
