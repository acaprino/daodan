# Automatic scientific checkpoint

Receive project, caller task ID, phase, semantic context (question, constraints,
candidate/document and relevant technology versions), budget and grants. Apply
during brainstorming, substantive problem/algorithm work, specification drafting
and ADR/FRD proposal or revision. An editorial-only change can be not-applicable.

1. Read mode using the helper in `runtime.md` before reading the archive.
   OFF returns disabled with no scientific reads, search or writes.
   Malformed configuration returns configuration-error; do not repair silently.
2. Evaluate whether empirical/theoretical evidence could affect this decision.
   If not, record not-applicable in the caller's run with the reason.
   No keyword match alone triggers research. Ignore callbacks caused solely by
   writing research, templates, receipts, indexes or mode configuration.
3. Inspect the checkpoint key using caller task, phase, semantic context and
   current mode revision. A workflow and a native event use the same key.
   Claim it with the helper only where the caller grants state writes. Do not
   launch another coordinator or repeat an in-progress/completed key. On resume,
   inspect the existing owner/result; an interrupted claim is not success.
4. Apply `reuse.md` to indexed and unindexed related Markdown before any new
   document. Consult pertinent current research. Choose reuse, refresh or new research
   from actual question/version/source fit. A reuse cites the exact revision
   and claims, and does not claim a new online check. Changed constraints form
   a new context; a simple save does not. Compose this skill in the caller.
5. Record the outcome and reason: disabled, not-applicable, reused, updated,
   created, partial, unavailable or configuration-error, with revision/claim
   references. Re-read mode before new automatic work; retain labelled partial
   output on cancellation and stop at the next safe point.

ON grants no additional write permission. Brainstorming may publish research only
when its caller already authorizes documented research; otherwise use chat or the
owned run. Specifications and decisions pin research revision and claim IDs.
Evidence never approves a requirement or rewrites an accepted ADR/FRD.

Native session/prompt hooks only supply routing context; they perform no research,
network access, mode mutation or archive publication. Claude/Codex packages
register supported events, subject to the host's trust settings. OpenCode's
loader registers prompt and primary-context callbacks, with a first-prompt
session-start fallback when creation was not observed. Copilot and Pi retain
these method checkpoints without promising interception outside Daodan.

## Resume and explicit retry

A running checkpoint is unfinished work. Inspect its task_id and the original
Work Controller run; resume that same authorized work without claiming a new
checkpoint, then finish the existing key with outcome/reason/references. Never
mark it successful because the previous worker stopped. If its holder is still
active, use the caller's normal coordination and do not duplicate execution.

A terminal partial/unavailable result remains historical. Retry only when the
user requests it or relevant context changes. Include that request's stable
identity in the semantic context, preserving the previous result; this forms a
new deduplication key. An explicit research command can also perform the requested
retry without toggling mode. There is no automatic retry scheduler.
