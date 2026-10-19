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

One question per turn, through the host's question tool, or recorded in the
run's `questions` with the turn closed. Each question is anchored to real
code: "today `path:line` does X; should the idea change that?". Ask about
purpose, who uses it, constraints and what success looks like, not about
implementation the code already settles.

When the idea is clear enough, present two or three alternatives, each with
its cost: modules and files touched, records it extends or supersedes, tests
it needs, risks, size in waves. Recommend one and say why. An alternative
that would give a concept a second owner is named as such.

## Close with the user's choice

- **Do it.** Write the brief into the run (objective, chosen alternative,
  examples, constraints, rejected alternatives with their reasons) and hand
  it to the change cycle, whose interview starts from it instead of from
  zero.
- **Keep it.** With the user's agreement, write
  `docs/ideas/<YYYY-MM-DD>-<slug>.md`: the idea, the code and records it
  touches, the alternatives with their costs, and the open questions. It is
  the only project file a brainstorm writes.
- **Drop it.** Nothing is written outside the run.
