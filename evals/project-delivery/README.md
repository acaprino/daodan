# Project Delivery behavioral evals

Development assets, never shipped. Run each case with a fresh agent on a
disposable, exclusively owned fixture. Do not expose scoring assertions. Record
host, versions, candidate digests, native reviews, commands, commit SHAs and
unexecuted checks separately. Compiler and helper tests do not prove a live
workflow executed.

| Case | Path | Invariant |
|---|---|---|
| precommit-evidence | change | Every step commit follows verification and PASS review of the same unchanged candidate |
| interrupted-commit | change, continue | An uncertain commit is reconciled from HEAD and scoped bytes without duplication or destructive rollback |
| independent-delivery | record, plan, change, finish | project-delivery works through declared providers without the daodan command umbrella and merges only after current candidate validation and authorization |
| adversarial-plan | plan, change | Task execution starts only after an adversarial PASS on the exact plan digest and current bytes |
| frd-bootstrap | bootstrap, revise | Missing ADR/FRD are drafted from verified evidence, while stale sources and manual corrections remain explicit |

See `cases.md` for prompts and assertions. Record execution in `RESULTS.md`;
missing execution is not a pass.
