# UI–State–Intent Coherence Defects

Domain reference for reviewing UI/frontend code alongside its state model and backend producers. Load only when the review touches UI components, view models, or user-facing status/action projections.

Scope: semantic alignment between what the system actually knows and does, what the UI tells the user, and which actions the user can actually perform. Distinct from UI timing/layout races (see `ui-race-auditor`) and domain/contract invariants (see `logic-integrity.md`).

---

## Graph-First Review Method

Start from the interconnect map or call/data-flow graph before reading UI copy in isolation:

1. **Trace end-to-end**: follow *backend/producer (actual work & diagnostic cause) -> frontend state model (enum/union/derived status) -> UI projection (badges, labels, headers, tooltips) -> exposed commands/actions*.
2. **Establish intent**: determine what the flow actually does and which user remedies exist in that context.
3. **Check coherence**: flag any point where the UI misrepresents the current fact, hides a known cause, or points to an action that does not exist or does not apply.

---

## Category U1: Overloaded State & Contradictory Projections

### U1.1 Overloaded State Value
- **Pattern**: A single state/enum value covers two or more distinct causes that require different user remedies (e.g., "missing/unavailable" merged with "stale/needs re-running").
- **Detection**: Inspect every branch returning the same status value in view-model functions (`cellState`, `statusFor`, selectors). Flag when branches represent different underlying facts or lead to different remedies.
- **Fix**: Split into distinct state values—one per cause/remedy—so the UI can render accurate status and severity.

### U1.2 Contradictory Entity Views
- **Pattern**: Two projections of the same entity in the same app (e.g., summary table vs detail panel, or two helper functions over the same model) report conflicting states or vocabulary for the same condition.
- **Detection**: From the graph, compare all consumers/selectors deriving user-facing status from the same domain fields.
- **Fix**: Derive from a single shared state model and use one consistent vocabulary across views.

---

## Category U2: Prescriptive Label vs Real Command

### U2.1 Prescription Disguised as Status
- **Pattern**: A status label tells the user *what to do* ("Needs a build", "Re-run setup") instead of stating *what is true now* ("Not available", "Outdated"), especially when the prescribed action is impossible or wrong for some cases.
- **Detection**: Check status badges, column headers, and empty-state banners; verify whether the text states a fact or prescribes an action, and whether that action is valid for every branch that produces the label.
- **Fix**: State the current fact in the status label; express the remedy as a separate action only when applicable.

### U2.2 Ghost or Misnamed Command
- **Pattern**: A label, tooltip, or error message names an action/command that does not exist in the UI, or uses a different name than the actual button/menu item.
- **Detection**: Cross-reference every action named in user-facing strings against the real buttons, menu items, and handlers wired in the component tree.
- **Fix**: Match the exact name of the real command, or remove the reference if no command exists.

---

## Category U3: Lossy Backend-to-UI Projection

### U3.1 Dropped Diagnostic Cause
- **Pattern**: The backend or domain layer already computes a specific reason (e.g., unsupported target, never scanned, missing variant, ambiguous source), but the UI collapses all of them into one generic badge/message, forcing the user to guess or run an extra step to learn why.
- **Detection**: Follow error/missing/diagnostic fields from backend producers through API/IPC payloads into UI components; flag where distinct causes are discarded before rendering.
- **Fix**: Preserve and surface the specific cause (e.g., in tooltip, subtitle, or inline detail) without losing the distinction.

---

## Category U4: Action–Applicability Mismatch

### U4.1 Unavailable or Invalid Remedy Offered
- **Pattern**: The UI enables or offers an action (or lets the user select an incompatible option) where the backend/model cannot fulfill it, without explaining the constraint.
- **Detection**: Compare action/control enablement conditions in the UI against the actual capability/eligibility guards in the model and backend.
- **Fix**: Gate the action on the same eligibility rule as the backend, or clearly indicate why it is unavailable.

---

## Severity Calibration

| Severity | Criterion |
|----------|-----------|
| HIGH | Misleading status/label causes wrong user action, hides a real required action behind noise, or offers a destructive/broken command |
| MEDIUM | Overloaded state merging distinct remedies, ghost command name, or dropped backend diagnostic causing user confusion |
| LOW | Minor vocabulary inconsistency across views with no wrong action induced |

## Anti-Patterns for the Reviewer

- Do NOT nitpick copy tone, phrasing style, or grammar when state, cause, and action are coherent.
- Do NOT flag a label without tracing its producing branches and available UI commands in the code/graph.
