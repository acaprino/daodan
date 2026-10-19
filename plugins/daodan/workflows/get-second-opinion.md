---
description: >
  Have another model challenge a file (a plan, a decision record, a document, code), or have several models deliberate on a question. Asks for consent before any content leaves the machine.
  TRIGGER WHEN: the user asks for a second opinion, another model's view, or a challenge of a plan or decision.
  DO NOT TRIGGER WHEN: a normal review is wanted (use review-changes or review-branch).
argument-hint: "<file or question>"
---

# Get a second opinion

$ARGUMENTS

When the argument names a file, load the skill `peer-review:cross-model-peer-review`
and follow its `references/review.md` on that file.

When it is a question, load the skill `moe:multi-model-deliberation` and follow its
`references/deliberation.md`.

Either way, nothing leaves the machine before the user consents to what will be sent
and to whom.
