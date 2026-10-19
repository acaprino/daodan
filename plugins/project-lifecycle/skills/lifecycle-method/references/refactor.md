# Refactor

A change whose observable behavior stays the same: structure, names,
duplication, complexity, readability. It runs the change cycle with three
differences.

1. **Interview.** Fix what changes in the structure and why, the public
   surface that must not move, and what is out of scope. A record is written
   only when the refactor changes an ownership or a contract the records
   govern; otherwise the plan carries the intent. The invariant of every task
   is the same: behavior unchanged.
2. **Characterization first.** Before any refactoring wave, one wave in which
   `testing:test-writer` pins the current behavior of the scope's public
   surface where tests do not cover it. Those tests pass on the base; a
   failing one is a finding about the base, reported before going on.
3. **Waves.** Each task's oracle is a structural check that fails before the
   change: the duplicate still present, the complexity above the threshold
   the plan names, the import edge still there, the function longer than the
   plan allows. Its verification is the characterization tests and the
   scope's suite, unchanged and green. A task that needs to change a test's
   expectation stops with `NEEDS_REPLAN`: that is a behavior change.

Writers: for Python, load the skill `python-development:python-refactor-method`,
whose measurements give the structural oracles; for readability only, load the
skill `clean-code:readability-method`; otherwise the stack's specialist. Reviews
check equivalence: the light review's intent is "behavior unchanged", and stage
D adds the abstraction audit when the roster's signals call for it.
