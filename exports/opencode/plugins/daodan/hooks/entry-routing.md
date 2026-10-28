# Entry routing: daodan

These lines are the entry workflows and knowledge of the `daodan` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

The `daodan` entries are the primary entry points for project work, whatever the stack or domain. A domain vertical's entry applies when the request is specific to that domain.

- `/daodan:brainstorm-idea`: TRIGGER WHEN: the user wants brainstorming, project design or specifications, or an idea needs clarification before building it; no explicit command is required. DO NOT TRIGGER WHEN: the request is already clear enough to build (use /daodan:new-feature).
- `/daodan:check-health`: TRIGGER WHEN: the user asks how healthy a project is, what its technical debt is, or what to clean up first. DO NOT TRIGGER WHEN: one change is to be reviewed (use /daodan:review-changes or /daodan:review-branch).
- `/daodan:continue-task`: TRIGGER WHEN: the user wants to go on with an interrupted task, answers questions a command left pending, or opens a new session on a task branch. DO NOT TRIGGER WHEN: no task exists on this branch and the user wants new work (use /daodan:new-feature, /daodan:fix-bug or /daodan:refactor-code).
- `/daodan:document`: Create, derive, revise, review or export a native Word document through shared Office content/design and independent document composition and saved review.
- `/daodan:finish-task`: TRIGGER WHEN: the user wants a task completed, merged or closed. DO NOT TRIGGER WHEN: the task still has open waves (use /daodan:continue-task).
- `/daodan:fix`: TRIGGER WHEN: the user asks to fix, repair or clean up defects in an existing DOCX, PPTX or XLSX, or to apply the findings of verify.
- `/daodan:fix-bug`: TRIGGER WHEN: the user reports a bug to fix, a regression or a failing behavior and wants it corrected. DO NOT TRIGGER WHEN: the user only wants to understand a problem (use /daodan:investigate-problem).
- `/daodan:get-second-opinion`: TRIGGER WHEN: the user asks for a second opinion, another model's view, or a challenge of a plan or decision. DO NOT TRIGGER WHEN: a normal review is wanted (use /daodan:review-changes or /daodan:review-branch).
- `/daodan:humanize-text`: TRIGGER WHEN: the user asks to humanize, rewrite naturally or de-AI a text or a file. DO NOT TRIGGER WHEN: code is to be refactored (use /daodan:refactor-code) or documentation written (use /daodan:write-docs).
- `/daodan:init-project`: TRIGGER WHEN: a project has never been used with Daodan, or the user asks to set it up or start a new project.
- `/daodan:investigate-problem`: TRIGGER WHEN: the user reports an error, a failure, a regression or behavior they cannot explain, and the cause is not known. DO NOT TRIGGER WHEN: the cause is known and a fix is wanted (use /daodan:fix-bug).
- `/daodan:maintain-tests`: TRIGGER WHEN: the user asks to clean up, rationalize, consolidate, reorganize or revise existing tests. DO NOT TRIGGER WHEN: only adding protection for a behavior (use /daodan:write-tests) or fixing a product defect (use /daodan:fix-bug).
- `/daodan:map-code`: TRIGGER WHEN: the user asks to map, analyze or understand the structure of code, or to refresh the map. DO NOT TRIGGER WHEN: the user wants a written guide (use /daodan:write-docs) or a verdict on a change (use /daodan:review-changes).
- `/daodan:new-feature`: TRIGGER WHEN: the user wants new behavior, a feature or a capability added; also the default when unsure which work command fits. DO NOT TRIGGER WHEN: a defect is to be fixed (use /daodan:fix-bug) or behavior must stay the same (use /daodan:refactor-code).
- `/daodan:onboard-project`: TRIGGER WHEN: the user is new to a project, takes one over, or asks to be walked through it. DO NOT TRIGGER WHEN: the user wants a durable guide written into the repository (use /daodan:write-docs).
- `/daodan:presentation`: Create, derive, revise, review or export an editable PowerPoint presentation through shared Office content/design, native DeckCraft and independent review.
- `/daodan:record-decision`: TRIGGER WHEN: the user wants to write down, propose, revise or document a technical decision.
- `/daodan:refactor-code`: TRIGGER WHEN: the user wants code restructured, simplified, deduplicated, renamed or made more readable with the same behavior. DO NOT TRIGGER WHEN: behavior should change (use /daodan:new-feature or /daodan:fix-bug).
- `/daodan:review-branch`: TRIGGER WHEN: the user asks for a full or deep review of a branch, a pull request or a large change, or before a merge. DO NOT TRIGGER WHEN: only the current changes or one commit are to be reviewed (use /daodan:review-changes).
- `/daodan:review-changes`: TRIGGER WHEN: the user asks to review their changes, a commit, a file or a document. DO NOT TRIGGER WHEN: a whole branch or a pull request is to be reviewed (use /daodan:review-branch).
- `/daodan:run-maintenance`: TRIGGER WHEN: the user wants a whole project brought back into good shape over several stages. DO NOT TRIGGER WHEN: one diagnosis is enough (use /daodan:check-health) or one change is wanted (use /daodan:new-feature, /daodan:fix-bug or /daodan:refactor-code).
- `/daodan:show-status`: TRIGGER WHEN: the user asks what is open, where a task stands, who is working on what, or what to do next. DO NOT TRIGGER WHEN: the user wants a task continued (use /daodan:continue-task).
- `/daodan:start`: Route any Office request from one intake into the requested document, deck, workbook, theme, verification or repair methods with shared content/design.
- `/daodan:sync-upstream`: TRIGGER WHEN: the user wants to pull, update from upstream, or see what others changed. DO NOT TRIGGER WHEN: the user wants their own work merged (use /daodan:finish-task).
- `/daodan:theme`: Create requested reusable PowerPoint/Word themes and templates from supplied brand materials or ad hoc visual proposals with native samples and checks.
- `/daodan:tidy-repo`: TRIGGER WHEN: the user asks to clean up, tidy, remove dead code, junk files or redundant tests. DO NOT TRIGGER WHEN: the code itself is to be restructured (use /daodan:refactor-code).
- `/daodan:verify`: TRIGGER WHEN: the user asks to verify, check, validate or audit an existing DOCX, PPTX or XLSX.
- `/daodan:workbook`: TRIGGER WHEN: the user requests XLSX work, spreadsheet analysis, a model, a tracker or a dashboard, or a change or review of an existing workbook.
- `/daodan:worktrees`: TRIGGER WHEN: the user asks to list, describe, tag or manage task worktrees, or update the Worktrunk engine.
- `/daodan:write-docs`: TRIGGER WHEN: the user asks for documentation, a guide, a diagram for the documentation, a README, onboarding docs, or project instructions (CLAUDE.md, AGENTS.md). DO NOT TRIGGER WHEN: the text only needs to sound natural (use /daodan:humanize-text).
- `/daodan:write-tests`: TRIGGER WHEN: the user asks for tests, more coverage or a test for a specific behavior. DO NOT TRIGGER WHEN: a defect is to be fixed with its test (use /daodan:fix-bug) or the suite is to be audited (use /daodan:check-health).
