---
name: file-organizer
description: >
  Scope, plan, and execute the reorganization behind approval gates.
  TRIGGER WHEN: organizing messy folders (Downloads, Desktop, Documents), finding duplicate files, cleaning up old files, restructuring project directories, separating work from personal files, or automating file cleanup tasks.
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# File Organizer

Operate on personal/document folders and inactive archives. Exclude active
repositories from generic file reorganization: their source layout, tests,
instructions and run artifacts have project-specific ownership and verification.
Never treat a repository's similarly named files as removable duplicates by hash
or age alone. Report that boundary and hand the project back to its development
or repository-hygiene process without moving its contents.

## Instructions

### 1. Understand Scope

Ask clarifying questions before starting:
- Which directory needs organization?
- Main problem? (can't find things, duplicates, no structure, general mess)
- Files or folders to avoid? (active projects, sensitive data)
- How aggressive? (conservative vs comprehensive cleanup)

For broad reorganization, briefly propose a philosophy from the reference guide (PARA, Johnny Decimal, GTD, 7-Folder). Let user choose - never force one. Skip for scoped tasks like cleaning Downloads.

### 2. Analyze Current State

```bash
ls -la [target_directory]
find [target_directory] -type f -exec file {} \; | head -20
du -sh [target_directory]/* | sort -rh | head -20
find [target_directory] -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn
```

Summarize: total files/folders, type breakdown, size distribution, date ranges, obvious issues.

**Anti-patterns to flag:**
- Desktop used as permanent archive (goal: zero permanent files on Desktop)
- Unnamed folders (`New Folder`, `New Folder (3)`)
- Broken versioning (`document_FINAL_v2_DEFINITIVE_copy.docx`)
- Downloads folder never cleaned (thousands of unsorted files)
- Same file duplicated across locations (use shortcuts instead)

### 3. Identify Organization Patterns

**By type:**
- Documents (PDF, DOCX, TXT), Images (JPG, PNG, SVG), Videos (MP4, MOV)
- Archives (ZIP, TAR, DMG), Code/Projects, Spreadsheets (XLSX, CSV), Presentations (PPTX, KEY)

**By purpose:**
- Work vs Personal, Active vs Archive, Project-specific, Reference, Temporary/scratch

**By date:**
- Current year/month, Previous years, Very old (archive candidates)

**Context-specific structures:**
- Photos/Video: `Year/YYYY-MM_event-location/` with RAW, Edited, Export subfolders
- Music: `Artist/[Year] Album/NN - Track.ext`
- Work projects: numbered prefixes (`01_Brief/`, `02_Research/`, `03_Assets/`, `04_Deliverables/`) with WIP/FINAL_APPROVED separation
- Finance/personal docs: include expiry dates in filenames (`passport_exp_2030.pdf`), organize by year then type
- Code: map local paths to remote URLs (`github.com/username/repo/`)

See `references/organization-guide.md` for detailed templates.

### 4. Find Duplicates

When requested:
```bash
find [directory] -type f -exec md5 {} \; | sort | uniq -d
find [directory] -type f -printf '%f\n' | sort | uniq -d
```

For each duplicate set: show paths, sizes, dates, recommend which to keep. ALWAYS confirm before deleting. Suggest shortcuts/aliases instead of keeping copies.

### 5. Propose Organization Plan

Present plan before making changes. Include:
- Current state summary (file count, size, type breakdown, problems found)
- Anti-patterns detected
- Proposed folder tree structure
- Changes to make: new folders, file moves, renames, deletions
- Files needing user decision (ambiguous placement)
- Ask for explicit approval before proceeding

### 6. Execute Organization

After approval, organize systematically.

**Rules:**
- Always confirm before deleting anything
- Log all moves for potential undo
- Preserve original modification dates
- Handle filename conflicts gracefully
- Stop and ask on unexpected situations

**File renaming conventions** (only when user agrees - never auto-rename):
- ISO dates: `YYYY-MM-DD` for correct alphabetical sort
- Formula: `[Date]_[Context]_[Description]_[Version].ext`
- Zero-padded versions: `v01`, `v02` (minor: `v01.1`)
- Separators: `kebab-case` or `snake_case` (never spaces)
- All lowercase, filenames under 25-30 chars, let folder context provide the rest
- Zero-pad sequences: `001`, `002` (prevents `1, 10, 11, 2` sort)
- Status prefixes when useful: `WIP_`, `DRAFT_`, `REVIEW_`, `APPROVED_`
- Avoid: `< > : " / \ | ? *`, accents, emoji, leading dots, Windows reserved names (`CON`, `PRN`, `AUX`, `NUL`)
- Watch full path length approaching Windows 260-character limit

### 7. Provide Summary

After organizing, report:
- Folders created, files organized, space freed, anti-patterns fixed
- New folder tree structure
- Maintenance schedule (below)
- Custom bash commands for ongoing cleanup

**Maintenance Schedule:**

| Frequency | Time | Tasks |
|-----------|------|-------|
| Weekly | 15 min | Empty Downloads, process Inbox to zero, verify recent files are in place |
| Monthly | 45 min | Scan for duplicates, verify backups, archive completed projects |
| Quarterly | 2 hrs | Disk space audit, archive projects inactive 3+ months, test backup restore |
| Yearly | Half day | Disaster recovery test, retention policy review, structure update |
