# accessible-perception-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:accessible-perception-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX007`, `EX008`, `EX011`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.html`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.html` or `correct.html` to an isolated disposable directory as `subject.html`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Empty submission signals failure solely by red background; no associated reason is exposed.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Associated text and status communicate failure without forcing focus. No invented contrast ratio or full WCAG conformance claim.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.html` and `additional-correct.html` separately, each copied as `subject.html` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX009, EX010, EX012, EX013, EX014, EX015**. Defect: Important global matched selector hides consent, white-on-white button loses visible label, clipped fixed-height instructions fail reflow, image/media have no required equivalent, moving instruction ignores reduced-motion requirement. Countercase: Visible flow layout, contrasting label, reflow, text alternatives/transcript and static instruction preserve required information; source-only audit must not invent runtime geometry or media exercise.

## Media input clarification before defect attempt2

Original defect606a028f30d8 correctly failed its caption check: absent track markup does not exclude captions inside the unsupplied media. Original bytes and delivery are retained. The revised defect explicitly supplies the original oracle's complete media inventory: spoken instructions without open/in-band captions or another equivalent channel. This is a declared synthetic asset contract, not newly exercised media. Correct transcript alternative and production reviewer are unchanged.

## Independent contrast clarification before defect3/correct2

The original white-on-white consent button is inside a display:none ancestor, so its visible-label consequence is masked by the separate consent defect. Media-clarified defect2 correctly records that counterevidence; its six independently observable findings remain retained. Both variants now include a standalone required-label button outside that ancestor. Defect text/background are white/white; correct text/background are black/white. This isolates the original contrast obligation from consent visibility. New snapshots receive fresh native trials; prior reports are never relabeled.
