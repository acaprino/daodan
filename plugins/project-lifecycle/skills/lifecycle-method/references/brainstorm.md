# Brainstorm

Explore an idea with the user before a task exists. It reads the project and
writes no code, no decision record and no plan; its run, with operation
`brainstorm`, holds the conversation.

## Ground first

1. Load `codebase-map:map-method` and deepen the idea's area as its
   `references/deepen.md` directs. Name the code the idea would touch and the
   existing code that already does part of it, with the concept index of
   `abstraction-architect` when present.
2. Load `project-knowledge:adr-method` and run `resolve` on that area: the
   active records are constraints, and a record the idea contradicts is said
   at once.
3. Read what the project's instructions say about the area.

## Talk

Ask by the work record's question rule, one per turn, anchored to code
("today `path:line` does X; should the idea change that?"): purpose, users,
constraints, success, never what the code settles. Once the idea is clear,
ask which of two or three alternatives to take, each costed in modules and
files, records extended or superseded, tests, risks and waves; name one that
gives a concept a second owner.

## Close with the user's choice

- **Do it.** Write the brief into the run (objective, chosen alternative,
  examples, constraints, rejected alternatives with their reasons) for the
  change cycle's interview to start from.
- **Keep it.** With the user's agreement, write
  `docs/ideas/<YYYY-MM-DD>-<slug>.md`: the idea, the code and records it
  touches, the alternatives with their costs, and the open questions. It is
  the only project file a brainstorm writes.
- **Drop it.** Nothing is written outside the run.
