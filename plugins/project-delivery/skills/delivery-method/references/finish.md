# Finish a task (phase 7)

Load `worktree-manager:worktree-method` and read its `references/lifecycle.md`.
That method owns preparation and cleanup; existing reviews and protocol gates
remain mandatory.

1. **Task.** Resolve the agenda's branch task and holder. Take over only after
   confirmation that the other session closed. A branch without a task finishes
   without inventing one. Require sealed waves and answered questions.
2. **Candidate.** Record the method choice with **Squash** preselected and
   **Preserve full history** offered. Preselection is not consent. Prepare the
   selected candidate separately, retaining original commits and receipts.
   Complete transformations before stage D in `references/verify.md`.
   Report the last receipt's residual obligations. Blocking findings stop integration.
3. **Integrate.** Recheck source, target and candidate identities. Changes require
   preparation and review again. Use authorization covering the exact candidate,
   method and destination; otherwise ask. Integrate without unreviewed changes
   and record `integration.merged_sha` and `integration.candidate_review`.
4. **Realign.** Follow the worktree method's original-checkout binding procedure,
   then `references/realign.md`. Additional tracked changes need reviewed,
   authorized integration and fresh gates; never relabel earlier evidence.
5. **Close.** Require current HEAD to equal the verified integrated SHA, passed
   gates and completed realignment. A bound process also requires
   `VERIFIED_SUCCESS` with matching delivered artifacts. Complete before removing
   the bound checkout. Perform authorized cleanup separately; failure preserves
   recovery and never repeats integration. Push requires its own authorization;
   `references/retention.md` governs requested output disposition.
