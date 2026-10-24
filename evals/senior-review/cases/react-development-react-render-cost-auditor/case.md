# react-development:react-render-cost-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR055, PR057–069, PR071–077, PR079–082, PR085, PR087–089, PR091–096, PR107, PR112, PR114, PR117 (initial pair: component identity). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

Draft is defined inside Screen, so each tick creates a different component type and remounts its stateful input. A typed draft is lost when the unrelated clock updates. Identify state loss, not merely an optimization preference.

## Correct countercase

Draft is defined once at module scope; Screen rerenders preserve its identity and input state. No memo is required for this contract.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **external-snapshot (PR085, PR107, PR114, PR117)**: Fresh object snapshots violate the external-store contract independent of compiler memoization. Countercase: Stable object/array identity is valid without useShallow.
- **item-identity (PR112, PR071, PR091)**: Index keys transfer drafts to a different item after reordering. Countercase: Stable item IDs preserve state; virtualization is not required for this bounded list.
- **hydration-and-zero (PR073, PR076–077)**: Server render reads unavailable storage and zero renders visible 0; report both with requirements. Countercase: Matching server-provided state needs no warning suppression or injected script.
- **hot-loop-and-layout (PR057, PR065/069 lookup mechanism, PR055)**: Derive repeated linear scan over budget and use supplied trace for layout/scroll impacts; do not invent milliseconds for the Map. Countercase: Indexed lookup, grouped reads and passive listener satisfy declared behavior; no additional cache or package is required. The former PR057–069 range did not establish each independent rule.
- **repeated-render-work (PR087)**: Identify repeated initializer evaluation despite state retaining only its first value. Countercase: Lazy initialization suffices. The former PR058/060–064/067–069/075/079–082/088–089/092–096 tags exceeded this scenario's actual mechanism. Existing references still preserve those controls; new scenarios below establish only their named mechanisms, with remaining variants explicitly unqualified.

## Additional causal mechanism packets

The existing directory materializer includes each new same-name file from exactly one variant. Each file/section has its own independent requirement and source-contained supported-environment assumptions. Supplied profiles and artifact facts are synthetic inputs, not measurements executed by the reviewer. Keep this oracle and all opposite-variant files outside the target.

- **svg-animation.md (PR072)**: Defect: the actual SVG transform takes the specified 18ms raster path and violates the required 8ms main-thread animation budget. Correct: the wrapper transform takes the supplied 2ms compositing path with equivalent geometry; do not require wrappers without that engine/workload evidence.
- **offscreen-work.md (PR074)**: Defect: offscreen card layout/paint is included in each update and the supplied profile is over the journey budget. Correct: supported containment defers offscreen layout/paint and the matching supplied profile meets the budget without changing visible content or reserved geometry. Do not claim that it eliminates React node creation or require a virtualizer.
- **svg-precision.mjs (PR080)**: Defect: 10,000 pairs with twelve fixed decimal digits emit at least 299,999 bytes, exceeding the 200,000-byte points-attribute budget despite a 0.001-unit error allowance. Correct: three decimals bound the attribute to at most 179,999 bytes and coordinate error to 0.0005. The separate precision-critical export legitimately retains twelve digits in both variants and must stay clean. No one-decimal rule or runtime timing is inferred.
- **script-scheduling.md (PR079)**: Defect: async application script can execute before its declared vendor dependency on the supplied finish order, so required startup fails. Correct: deferred scripts execute in document order. Neither async nor defer is universally preferred independent of dependency/parse semantics.
- **subscription-scope.md (PR082)**: Defect: an event-only value unnecessarily subscribes its expensive component to every whole-store replacement; the supplied clock updates cause unwanted work beyond budget. Correct: event-time read preserves current ID without subscribing. Do not add a cache, memo or mandatory store library.
- **prop-and-branch-work.md (PR088–089)**: Two independent defects: a fresh default array defeats the memoized child on unrelated ticks; a loading branch computes an unused expensive avatar. Correct: shared immutable default and an early loading return avoid each respective required work. No memo syntax or component split is universally mandatory.
- **work-dependencies.md (PR093; scoped clean PR092)**: Defect: sort-only changes recompute an unchanged expensive filter because unrelated dependencies share one memo. Correct: independent memo dependencies keep filtering unchanged. A separate cheap primitive memo is explicitly within budget in both variants and must not be reported for style or absence of preferred syntax. PR092 has no fabricated positive oracle.
- **priority-and-transients.md (PR081, PR094–096)**: Independent required outcomes: input echo before expensive derived render, pending indication until transition commit, and no React render for per-frame canvas-only coordinates. Defect scenes violate those outcomes through urgent derived work, premature manual pending reset and state-driven transient updates. Correct scenes use the supplied deferred/memo, transition-owned pending and ref-only lifetime paths. Preserve actual scheduler/version assumptions and do not infer a universal millisecond guarantee from a hook name.

These scenes materialize the previously missing independent mechanisms; they do not assert that every micro-optimization in a former broad numeric range has been exercised. PR058–064/066–069/075 techniques remain candidates under their canonical requirements and counterevidence, not automatic defects merely because a syntax form is absent.
