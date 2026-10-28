# Entry routing: daodan

These lines are the entry workflows and knowledge of the `daodan` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

The `daodan` entries are the primary entry points for project work, whatever the stack or domain. A domain vertical's entry applies when the request is specific to that domain.

- `brainstorm-idea-workflow`: TRIGGER WHEN: the user wants brainstorming, project design or specifications, or an idea needs clarification before building it; no explicit command is required. DO NOT TRIGGER WHEN: the request is already clear enough to build (use new-feature-workflow).
- `check-health-workflow`: TRIGGER WHEN: the user asks how healthy a project is, what its technical debt is, or what to clean up first. DO NOT TRIGGER WHEN: one change is to be reviewed (use review-changes-workflow or review-branch-workflow).
- `continue-task-workflow`: TRIGGER WHEN: the user wants to go on with an interrupted task, answers questions a command left pending, or opens a new session on a task branch. DO NOT TRIGGER WHEN: no task exists on this branch and the user wants new work (use new-feature-workflow, fix-bug-workflow or refactor-code-workflow).
- `document-workflow`: Create, derive, revise, review or export a native Word document through shared Office content/design and independent document composition and saved review.
- `finish-task-workflow`: TRIGGER WHEN: the user wants a task completed, merged or closed. DO NOT TRIGGER WHEN: the task still has open waves (use continue-task-workflow).
- `fix-workflow`: TRIGGER WHEN: the user asks to fix, repair or clean up defects in an existing DOCX, PPTX or XLSX, or to apply the findings of verify.
- `fix-bug-workflow`: TRIGGER WHEN: the user reports a bug to fix, a regression or a failing behavior and wants it corrected. DO NOT TRIGGER WHEN: the user only wants to understand a problem (use investigate-problem-workflow).
- `get-second-opinion-workflow`: TRIGGER WHEN: the user asks for a second opinion, another model's view, or a challenge of a plan or decision. DO NOT TRIGGER WHEN: a normal review is wanted (use review-changes-workflow or review-branch-workflow).
- `humanize-text-workflow`: TRIGGER WHEN: the user asks to humanize, rewrite naturally or de-AI a text or a file. DO NOT TRIGGER WHEN: code is to be refactored (use refactor-code-workflow) or documentation written (use write-docs-workflow).
- `init-project-workflow`: TRIGGER WHEN: a project has never been used with Daodan, or the user asks to set it up or start a new project.
- `investigate-problem-workflow`: TRIGGER WHEN: the user reports an error, a failure, a regression or behavior they cannot explain, and the cause is not known. DO NOT TRIGGER WHEN: the cause is known and a fix is wanted (use fix-bug-workflow).
- `maintain-tests-workflow`: TRIGGER WHEN: the user asks to clean up, rationalize, consolidate, reorganize or revise existing tests. DO NOT TRIGGER WHEN: only adding protection for a behavior (use write-tests-workflow) or fixing a product defect (use fix-bug-workflow).
- `map-code-workflow`: TRIGGER WHEN: the user asks to map, analyze or understand the structure of code, or to refresh the map. DO NOT TRIGGER WHEN: the user wants a written guide (use write-docs-workflow) or a verdict on a change (use review-changes-workflow).
- `new-feature-workflow`: TRIGGER WHEN: the user wants new behavior, a feature or a capability added; also the default when unsure which work command fits. DO NOT TRIGGER WHEN: a defect is to be fixed (use fix-bug-workflow) or behavior must stay the same (use refactor-code-workflow).
- `onboard-project-workflow`: TRIGGER WHEN: the user is new to a project, takes one over, or asks to be walked through it. DO NOT TRIGGER WHEN: the user wants a durable guide written into the repository (use write-docs-workflow).
- `presentation-workflow`: Create, derive, revise, review or export an editable PowerPoint presentation through shared Office content/design, native DeckCraft and independent review.
- `record-decision-workflow`: TRIGGER WHEN: the user wants to write down, propose, revise or document a technical decision.
- `refactor-code-workflow`: TRIGGER WHEN: the user wants code restructured, simplified, deduplicated, renamed or made more readable with the same behavior. DO NOT TRIGGER WHEN: behavior should change (use new-feature-workflow or fix-bug-workflow).
- `review-branch-workflow`: TRIGGER WHEN: the user asks for a full or deep review of a branch, a pull request or a large change, or before a merge. DO NOT TRIGGER WHEN: only the current changes or one commit are to be reviewed (use review-changes-workflow).
- `review-changes-workflow`: TRIGGER WHEN: the user asks to review their changes, a commit, a file or a document. DO NOT TRIGGER WHEN: a whole branch or a pull request is to be reviewed (use review-branch-workflow).
- `run-maintenance-workflow`: TRIGGER WHEN: the user wants a whole project brought back into good shape over several stages. DO NOT TRIGGER WHEN: one diagnosis is enough (use check-health-workflow) or one change is wanted (use new-feature-workflow, fix-bug-workflow or refactor-code-workflow).
- `show-status-workflow`: TRIGGER WHEN: the user asks what is open, where a task stands, who is working on what, or what to do next. DO NOT TRIGGER WHEN: the user wants a task continued (use continue-task-workflow).
- `start-workflow`: Route any Office request from one intake into the requested document, deck, workbook, theme, verification or repair methods with shared content/design.
- `sync-upstream-workflow`: TRIGGER WHEN: the user wants to pull, update from upstream, or see what others changed. DO NOT TRIGGER WHEN: the user wants their own work merged (use finish-task-workflow).
- `theme-workflow`: Create requested reusable PowerPoint/Word themes and templates from supplied brand materials or ad hoc visual proposals with native samples and checks.
- `tidy-repo-workflow`: TRIGGER WHEN: the user asks to clean up, tidy, remove dead code, junk files or redundant tests. DO NOT TRIGGER WHEN: the code itself is to be restructured (use refactor-code-workflow).
- `verify-workflow`: TRIGGER WHEN: the user asks to verify, check, validate or audit an existing DOCX, PPTX or XLSX.
- `workbook-workflow`: TRIGGER WHEN: the user requests XLSX work, spreadsheet analysis, a model, a tracker or a dashboard, or a change or review of an existing workbook.
- `worktrees-workflow`: TRIGGER WHEN: the user asks to list, describe, tag or manage task worktrees, or update the Worktrunk engine.
- `write-docs-workflow`: TRIGGER WHEN: the user asks for documentation, a guide, a diagram for the documentation, a README, onboarding docs, or project instructions (CLAUDE.md, AGENTS.md). DO NOT TRIGGER WHEN: the text only needs to sound natural (use humanize-text-workflow).
- `write-tests-workflow`: TRIGGER WHEN: the user asks for tests, more coverage or a test for a specific behavior. DO NOT TRIGGER WHEN: a defect is to be fixed with its test (use fix-bug-workflow) or the suite is to be audited (use check-health-workflow).
