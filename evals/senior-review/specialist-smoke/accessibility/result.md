# Accessibility smoke review

- dimension: accessibility
- reviewer: senior-review:accessibility-auditor
- status: delivered
- output_path: evals/senior-review/specialist-smoke/accessibility/result.md
- knowledge_usage: []
- scope: Content audit of the complete `requirements.md`, `view-a.html` and `view-b.html` read from this folder. No changeset comparison or introduction claim.
- checks_completed: Required consent dismissal, control semantics and names, keyboard reachability and activation, dismissal handler, and alternative paths in both complete documents.

## Findings

### Keyboard users cannot activate Continue in view A

- file: evals/senior-review/specialist-smoke/accessibility/view-a.html
- line: 5
- severity: High
- confidence: 99
- confidence_rationale: The complete document contains only a click handler on a non-native control, with no keyboard handler or alternate dismissal route; the authoritative requirements exclude shared scripts or components. The conclusion follows from standard HTML activation behavior. Runtime behavior was not exercised.
- evidence_class: derived
- premise: Each view must allow consent dismissal using keyboard alone (`requirements.md:3`); these documents are complete and have no shared scripts or components (`requirements.md:4-5`).
- premise_provenance: independent
- provenance_rationale: Established by reading the authoritative requirements and both documents.
- trigger: A keyboard user tabs to Continue and presses Enter or Space to dismiss consent.
- evidence: The only dismissal route is an `onclick` handler on a `div`. `tabindex="0"` makes it focusable and `role="button"` identifies its intended semantics, but neither supplies native keyboard activation. There is no keyboard handler or alternate dismissal control in the complete document. The supported journey therefore cannot complete through ordinary keyboard activation.
- counterevidence_checked:
  - The focusable element is reachable and its click handler correctly removes consent. Neither fact supplies keyboard activation. No shared behavior can provide it under the fixture requirements. View B uses a native `button` with the same handler, which supplies keyboard activation without additional ARIA or keyboard handlers.
- fix_direction: Replace the custom control with a native `button type="button"`, retaining its text and dismissal handler.

## Coverage and limitations

No finding in `view-b.html`: its native button provides the required keyboard activation path under standard HTML behavior. Both documents were read in full; no external styles, scripts or wrappers were assumed. Findings describe source-derived behavior, not reproduced execution. No browser, assistive technology or runtime probes were performed, as required by the assignment; comprehensive accessibility conformance is not claimed.

- gaps: No missing input or unfinished check within the assigned static scope. Runtime and assistive-technology behavior remain unmeasured and are outside this assignment.
