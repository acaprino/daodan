# Lifecycle handoff

The caller owns its task cycle and loads this reference through worktree-method.
Return evidence to that caller; never fabricate a completed review or waive its
required gates. Direct inventory and annotations require no merge workflow.

## Prepare and integrate

The integration choice offers Squash first and preselected, then full history
(and rebase only where supported). Record the user's actual answer through the
existing question mechanism. Preselection is not consent. Reuse a scoped grant
already given for the exact candidate; changed candidate, target or method
requires revalidation. Apply repository merge rules and remote protections.

Preserve the source branch and original commits. Prepare the selected result in
an integration candidate with explicit source and target SHAs. Stage only owned,
authorized paths. Squash, rebase, conflict resolution and content-changing hooks
precede final tests and review. Full history must not acquire an implicit rebase.
The caller reviews the resulting candidate and records its identity, including
the target on which it was prepared. If either side moves, stop and refresh the
affected preparation and evidence.

Worktrunk's default merge can stage all local files, squash, rebase and remove
the source checkout. Do not use that default as a final integration operation.
The supported CLI documents `merge --no-commit --no-rebase --no-remove --no-hooks`
for integrating an already prepared, clean candidate without those transforms.
Use `--no-ff` only if a merge commit was chosen and the caller's review contract
covers that integration. Invoke the verified executable with explicit cwd and
controlled configuration; do not reuse a shell alias or append arbitrary user
flags. A local merge never fetches or publishes to GitHub. Remote PR integration
continues through the caller's GitHub method and branch-protection checks.

Work Controller requires current HEAD in the run-bound checkout to equal the
recorded merged SHA. Ordinarily it must descend from the reviewed candidate.
For a server-side squash, record `integration.strategy: squash` and the full
pre-merge `integration.target_sha`. The helper verifies actual Git objects: the
reviewed candidate includes that target, the merged commit has exactly that
target as its sole parent, and both candidate and result have the same tree.
It also requires the review snapshot to match the clean integrated checkout.
Fetch the result before checking it; a moved target or different tree requires
fresh preparation and review. There is no equivalent exception for an arbitrary
rebase. Retain the reviewed commit locally until verification and archival finish.
Do not rewrite sealed wave receipts to make a later squash appear reviewed.
Do not complete from another checkout merely because its files look identical.
The delivery owner must establish the original binding at the integrated result
and verify current state before closure, or leave the task open with the actual
integration recorded. Preserve the original branch when moving a clean checkout
to the integrated commit; never force-reset local work. Use a clean detached
checkout at that SHA in the original run-bound path, keeping the source branch
intact. Before detaching, persist the integration result, pinned target and
delivered branch candidate review while the recorded candidate still names the
reviewed source commit and raw snapshot. After detaching, call `resume` with the
same authorizations. It revalidates that recorded proof and original identity,
preserves the source branch and sealed receipts, and refreshes the candidate.
An interruption at this handoff uses the same resume route; discover a detached
task by the original checkout path and exact run ID, not branch `HEAD`.
Changed work blocks that transition. Realignment that changes tracked
content needs a new reviewed, authorized integration and fresh final gates.

The proof retains the raw reviewed snapshot and compares scoped content with
actual committed blobs. It recognizes Git's built-in text line-ending conversion
when committed and live attributes/configuration prove that conversion,
including Windows CRLF checkouts. Each matching raw blob is accepted first;
Git's own text statistics distinguish forced text from automatic binary detection
and preserve legacy CRLF index blobs. Arbitrary filters, encoding transforms and identity substitutions are
not accepted as equivalence evidence. Preserve an unsupported proof failure;
never change repository conversion settings automatically or relabel the review.

## Remove only owned, concluded workspaces

Record integration first. Close the run under its original binding before
removing that checkout. Worktree removal and branch disposition are separate:
a successful merge with failed cleanup is not another merge to repeat.

Before removal, re-resolve Git inventory, canonical path, branch/head, task and
holder. Confirm no active session, lock, nested worktree, changed fingerprint,
tracked changes, untracked files or ignored local data needing preservation.
Inspect ignored data explicitly: upstream removal can delete it. Only scoped
existing authorization permits removal; otherwise present the concrete path and
data disposition once. A catalog annotation alone proves no deletion authority.

Use foreground cleanup of the verified owned path and preserve the branch when
original history or evidence requires it. Inspect the actual Git inventory and
filesystem after return; do not interpret background launch as deletion success.
Keep task records and catalog history in the main home. Conflicts, interruptions
and partial cleanup retain their recovery information. No force removal, branch
force deletion or automatic trash purge belongs in this method.

Analysis-only tasks retain their report and close without invented commits or
merges. Their workspace still needs the same scoped removal checks.
