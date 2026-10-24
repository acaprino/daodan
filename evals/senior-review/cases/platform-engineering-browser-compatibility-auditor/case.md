# platform-engineering:browser-compatibility-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR142–146 and relevant PR162–175 reference leads (initial pair: unavailable picker). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The shipped WebView has no showOpenFilePicker, yet chooseFile calls it unconditionally. Opening a required document fails before the native bridge can be used. Feature capability is supplied explicitly, not inferred from browser popularity.

## Correct countercase

The available nativeOpenDocument fallback is called when the web API is absent. Do not demand another polyfill when the existing bridge returns the required document.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **keyboard-and-origin (PR143–144)**: Show hidden Confirm using supplied viewport facts and unavailable API through deployment origin. Countercase: Actual visual viewport and native fallback preserve the path.
- **resume-and-webview-callback (PR145 only)**: Despite its historical section name, this packet contains a suspended timer, not a WebView callback registration. A timer counter remains valid after more than a minute in suspended background. Countercase: Recomputed wall-time expiry does not require continuous timer delivery. PR146 is now tested separately below.

## Supported WebView callback (PR146)

The directory materializer includes `webview-callback.mjs` from the selected variant. The source binds the supported WebViewBridge version, case-sensitive callback name, supplied native payload and current view lifetime. Treat that contract as synthetic supplied platform evidence, not an installed browser probe.

Defect: mount registers authResult, but the supported native host delivers the required current request's terminal result only to oauthResult. The browser launches external authentication and remains waiting forever because complete is never reached by the actual native delivery. Cite registration, launch and the matching effective host contract. A DOM event or ordinary timer cannot substitute for that bridge callback.

Correct / must_not_report: registration matches oauthResult, request identity binds the payload, terminal success/cancel is forwarded, and the returned unsubscribe belongs to view teardown. There is no required runtime concurrency or additional retry mechanism. Do not widen accepted callback names, treat an intentionally ignored old request as lost work, or infer provider-authentication policy from this delivery-only fixture.
