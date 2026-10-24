# testing:contract-test-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR021 (pair: mock-only serialization protection). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The test uses a hand-authored string-ID fixture and never serializes the real producer, which emits a number. It cannot detect the shown contract drift. Report the missing producer boundary protection and route the actual wire defect without duplicating it as a second test finding.

## Correct countercase

The test serializes the real producer and checks string identity; consumer behavior uses that same wire value. Do not demand OpenAPI or a live HTTP service for this explicit serialization contract.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **null-error-version (PR021)**: Report specifically unprotected null/absence/error/version/encoding drift, not mere fixture duplication. Countercase: Repeated assertions at independent service boundaries preserve distinct protection.

## Production-boundary and version protection correction

Prior defect5f2fd93f5944 correctly failed required source coverage because event encode/decode implementations were absent; its two supported protection findings remain. Prior correct44f8a3ebeff4 validly found unsupported-version rejection untested. Fresh defect supplies actual production encoder/decoder while retaining the defective local mocks. Fresh correct preserves all existing assertions and directly rejects independently specified version3 bytes. The explicit version-policy inputs are integer-valued; other integer versions must raise ValueError. No reviewer body changed, no runtime was exercised, and all old bytes/targets/reports remain archived.

## Independent wire protection correction

Correct attempt3 still allowed matching encoder/decoder wire-field drift: native fb1e594d0d5b constructed a valid coordinated error.code rename that all round-trip tests miss. Preserve that report and both attempts' stale D1 location limitation. Fresh correct assertions independently inspect encoded wire shape and decode literal wire fixtures, retaining absence/null, error-code and unsupported-version outcomes. Missing and non-string code rejection use direct independent wire inputs. Admitted envelope shapes and integer version scope are explicit in both variants. Attempts4 f9fbde02a61e/cb71c71dd783 were prepared but never dispatched and are superseded; original bytes remain unchanged. No reviewer body or runtime execution changed.

## Producer and consumer rejection correction

Attempt5 correct2b69015576cb validly identified that the declared invalid-input policy applies to both production boundaries, but encode had no validation and all negative assertions called only decode. Original source/report preserved. Both fresh variants share production validation at encode and decode; correct retains independent positive wire checks and direct decoder negatives, adding independently specified invalid producer inputs. Defect local mocks and original integer-ID producer disagreement remain unchanged. No narrowed producer-input assumption, reviewer-body edit or runtime execution is used. Static declaration locators are freshly derived from actual bytes.
