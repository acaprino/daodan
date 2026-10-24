# capacity-quota-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:capacity-quota-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX070`, `EX072`, `SD021`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.py`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.py` or `correct.py` to an isolated disposable directory as `subject.py`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Two replicas independently admit ten each in the same tenant/window; the global cap is bypassed.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Atomic shared admission enforces the same identity/window across replicas; no requirement for local counters.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.json` and `additional-correct.json` separately, each copied as `subject.json` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX071, EX073, EX074, EX132, EX142, RC013, RC036**. Defect: Bounded queue leaks work into waiting tasks; pool parents starve child completion; request IDs/cheap admission bypass weighted tenant bound; synchronized misses exceed origin; retries undercount work. Countercase: Upstream rejection, released workers, shared weighted tenant admission, bounded refreshes and per-attempt budget each satisfy the respective independent requirement.

## Authentication-attempt identity (SD021)

Materialize `auth-attempt-defect.py` / `auth-attempt-correct.py` as `auth-attempt.py` in the selected variant, using the existing materializer. Include only the same variant; keep this oracle outside the target.

The requirement permits at most three password-verification attempts for one canonical account/window across replicas, including failed attempts. Defect: four requests for Alice with different caller-selected trace IDs all reach password verification because each gets a fresh quota key. This is an adversarial identity bypass, independently of total workload or password correctness. Cite the effective gateway key and its reachable backend call.

Correct / must_not_report: every public route is forced through the supplied gateway, which atomically gates the canonical account/window across replicas before password verification. The backend intentionally has no duplicate local limiter. Different trace IDs and account spelling variants cannot evade the upstream gate. Do not require an application-local counter, lock, CAPTCHA or a universal login policy. This is supplied source/enforcement evidence, not an observed attack or live gateway probe.
