# Worktrunk delegation and upstream maintenance

Decision source: user request of 2026-10-26 to proceed with Worktrunk intake and
upstream updates after comparing existing worktree tools. The merge choice asks
the user, with Squash preselected. The external CLI approach was recommended
because it reuses maintained Git operations while retaining Daodan ownership.

## Boundary

`worktree-manager` owns an original adapter and workspace catalog. Worktrunk
remains the external executable, dual licensed MIT OR Apache-2.0. The provider
pin records the release, source commit and verified asset provenance. No upstream
source, agent plugin or binary is incorporated into the marketplace.

The `daodan:worktrees` entry exposes inventory and free-text operations. Existing
delivery methods compose the same workspace skill. Work Controller owns task
records, questions, authorizations and completion. Senior Review remains the
review owner; GitHub integration remains in the delivery workflow.

## Requirements

1. New managed worktrees resolve beneath the main checkout's
   `.daodan/worktrees/`, including requests made from another worktree. Git
   inventory includes every checkout, while the durable catalog adds task ID,
   descriptions and labels without duplicating the agenda's state.
2. Create/retry never overwrites foreign paths or branches. Stable identities,
   reservations, path checks and atomic metadata writes make interrupted
   creation recoverable. Setup and active-host binding are separately verified.
3. Squash/rebase preparation precedes final review. Integration preserves the
   reviewed candidate; original commits and immutable receipts remain available.
   Cleanup follows verified closure and scoped authority, preserving local data.
4. Upstream checks are read-only. Candidate upgrades undergo isolated contract
   tests before their pin and installation advance. Unsupported executables fail
   explicitly. No global hooks, automatic update polling or vendored sync target.
5. Generated packages ship the same original method, helpers and references on
   five hosts. Compiler parity, helper tests, real Windows CLI probes and live
   installed-host workflow evidence are reported separately.

## Acceptance and limits

Exercise main/nested home discovery, complete inventory, annotation retention,
creation/resume, naming collisions, symlink/path escape, malformed output, wrong
versions, upstream unavailability and unrelated file preservation. Run existing
repository contract gates and inspect each exported consumption path.

The original task proposal and online comparison are retained in the owned
`.daodan/runs/20261026-worktree-management-design/` record. Implementation evidence
belongs in `.daodan/runs/20261026-worktrunk-intake/`. Neither structural export
support nor a unit test constitutes a live end-to-end probe on all five hosts.

## Review-driven invariants

1. Automatic executable discovery searches authorized installation locations,
   excluding repository content and implicit current-directory lookup before
   running a version probe. Explicit executable selection remains a separate
   authorization path.
2. A saved Git registration is not proof of the checkout currently at its path.
   Creation confirmation and resume verify the actual repository, administrative
   directory, branch and HEAD without adopting a replacement repository.
3. Tag additions/removals are catalog transactions. Aggregate serialized size is
   validated before replacing the readable catalog; a rejected write preserves
   both its bytes and revision.
4. Squash equivalence accepts already matching committed bytes first. Any
   remaining text conversion uses Git's own classification with matching
   committed/live attributes and index identity, without running custom filters.
   An interrupted transition to the integrated detached commit is reconciled
   only against the recorded review, unchanged inputs and retained source branch.
5. An explicit finish request through the worktrees entry carries the delivery
   owner's declared isolated-worker contract. Plain inventory and annotation
   dispatch no workers. Tests exercise the complete local remote-style squash,
   fetch, detach, interrupted resume and closure sequence; actual GitHub and
   installed-host execution remain separately evidenced operations.
