# Sync with upstream

Brings other people's work into this copy. It never rewrites published
history and never touches an uncommitted file.

1. **Fetch.** `git fetch --prune`. The working tree does not change.
2. **Report.** For the default branch and the current one: how many commits
   arrived and from whom, which modules they touch (through the map's file
   inventory) and which records under `docs/adr/`, and whether they touch a
   write set of an open task in the agenda. A conflict risk with an open task
   is named with its paths.
3. **Update.** The local default branch moves by fast-forward only:
   `git merge --ff-only` when it is checked out, `git fetch origin
   <branch>:<branch>` when it is not. A diverged branch, or uncommitted edits
   in the incoming paths, stops with the options (merge, rebase of
   unpublished commits only, or leave it as it is) and the choice is the
   user's. An open task's branch is never rebased on the session's own
   initiative; its holder decides.
4. **Realign.** Follow `references/realign.md` with the incoming range.
