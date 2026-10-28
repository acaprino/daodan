<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# File Organization Reference Guide

Condensed best practices for naming, structuring, and maintaining files. Use as optional suggestions -- propose to users during organization, never force.

---

## Organization Philosophies

Propose these when a user needs a top-level structure. Let them choose based on personality and context.

### PARA Method (Tiago Forte)

Four folders ordered by actionability. Max 2-3 levels deep.

```
00_Inbox/
01_Projects/       ← active work with deadlines
02_Areas/          ← ongoing responsibilities (no deadline)
03_Resources/      ← reference material by interest
04_Archives/       ← anything no longer active
```

Best for: freelancers, creatives, knowledge workers wanting simplicity.
Weakness: ambiguity between Areas and Resources.

### Johnny Decimal

Numeric IDs: max 10 areas (00-99), max 10 categories each. Item format: `AC.ID` (e.g. `23.04`). Never more than 2 levels deep.

```
10-19 Finanze/
│   ├── 11 Tasse/
│   │   ├── 11.01 FY2024
│   │   └── 11.02 FY2025
│   └── 12 Estratti-Conto/
20-29 Lavoro/
    └── 21 Clienti/
        ├── 21.01 Acme-Corp
        └── 21.02 Globex-Inc
```

Best for: methodical users, shared environments needing unambiguous references.
Weakness: rigid -- hard to restructure after initial setup.

### GTD File System (David Allen)

Separate Reference (consultation) from Actionable (action). Flat alphabetical A-Z for reference. Digital flow: Inbox → Active Projects → Reference → Someday/Maybe → Archive.

Best for: complementary philosophy layered onto other systems.

### 7-Folder Rule

Max 7 folders per level, max 3 levels deep = 343 folders reachable in 1-3 clicks. Simple, predictable, great for teams and SMBs.

---

## Naming Conventions

### Formula

```
[Date]_[Context]_[Description]_[Version].ext
```

All lowercase. No spaces, no accents, no special characters.

### Dates -- ISO 8601

Always `YYYY-MM-DD`. Guarantees correct alphabetical sort across all OSes. Position at start when chronological order matters, after context when grouping by project matters.

### Versioning

`v` + zero-padded digits: `v01`, `v02`, `v03`. Minor revisions: `v01.1`, `v01.2`. Always last element before extension. Status prefixes: `WIP_`, `DRAFT_`, `REVIEW_`, `APPROVED_`.

### Separators

Prefer `kebab-case` or `snake_case`. Never spaces. CamelCase acceptable for project folder names only.

### Zero-Padding

Always pad numbers: `01`, `02`... `99` -- avoids `1, 10, 11, 2` sort order.

### Examples

| Bad | Good |
|-----|------|
| `report finale.docx` | `2026-03-03_report-vendite-Q1_v03.pdf` |
| `Copia di budget (2).xlsx` | `budget-2026_marketing_v02.xlsx` |
| `IMG_20260303_142355.jpg` | `2026-03-03_evento-lancio_001.jpg` |
| `notes march 3rd meeting!!.txt` | `2026-03-03_meeting-notes_team-design.md` |

### Characters to Avoid

`< > : " / \ | ? *`, accents (`è, ñ, ü`), emoji, leading dots (hidden on Unix), Windows reserved names (`CON, PRN, AUX, NUL`).

### Path Length

Windows limit: 260 characters for full path. Deep hierarchies with long names hit this easily.

---

## Context-Specific Structures

### Photos & Video

Year → date+event, with RAW/Edited/Export subfolders.

```
Photos/
└── 2025/
    ├── 2025-01_capodanno-roma/
    │   ├── RAW/
    │   ├── Edited/
    │   └── Export/
    └── 2025-06_vacanza-sardegna/
```

File naming: `YYYY-MM-DD_event_location_NNN.ext`.

### Music

```
Artist/
└── [Year] Album/
    └── NN - Track.ext
```

Always fill Album Artist tag to prevent phantom albums from compilations.

### Work Projects

Numbered prefixes for logical order. Template folder to duplicate for new projects.

```
Clients/
└── ClientName/
    └── 2025_ProjectName/
        ├── 01_Brief/
        ├── 02_Research/
        ├── 03_Assets/
        ├── 04_Deliverables/
        │   ├── WIP/
        │   └── FINAL_APPROVED/
        ├── 05_Meetings/
        └── 06_Admin/
```

### Personal Archive & Finance

Include expiry dates in filenames: `passport_exp_2030.pdf`. Finance by year → type (invoices, statements, tax returns, receipts). Invoice naming: `invoice_NNN_client_YYYY-MM-DD.pdf`.

### Code / Developer Workspace

GOPATH-inspired mapping of local paths to remote URLs.

```
Code/
├── github.com/
│   ├── my-username/
│   │   ├── project-portfolio/
│   │   └── side-project/
│   └── org-work/
│       └── backend-api/
├── sandbox/        (temporary experiments)
└── archive/        (finished projects)
```

---

## Anti-Patterns to Detect

Flag these during analysis and propose fixes:

- **Desktop as archive** -- zero permanent files on Desktop
- **`New Folder (3)`** -- unnamed folders with unknown content
- **`document_FINAL_v2_DEFINITIVE_copy.docx`** -- broken versioning
- **Downloads never cleaned** -- thousands of unsorted files
- **No backup strategy** -- recommend 3-2-1 rule (3 copies, 2 media, 1 offsite)
- **Duplicates everywhere** -- 78% of professionals have this problem
- **One file, multiple locations** -- use shortcuts/aliases instead of copies

---

## Maintenance Schedule

Propose this after organizing -- adapt frequency to user's needs.

| Frequency | Duration | Tasks |
|-----------|----------|-------|
| Weekly | 15 min | Empty Downloads, process Inbox to zero, verify recent files are in place |
| Monthly | 45 min | Scan for duplicates, verify backups, archive completed projects |
| Quarterly | 2 hours | Disk space audit (WizTree/ncdu), archive projects inactive 3+ months, test backup restore, review automation rules |
| Yearly | Half day | Full disaster recovery test, retention policy review, top-level structure update |

### Inbox Principle

Single entry point for all new files. Must be empty after each review session. No file stays in Inbox longer than 7 days.

### Archive Tiers

- **Hot** -- active files on SSD
- **Warm** -- recent files on HDD/NAS
- **Cold** -- archive on external disk or cheap cloud

Compressed archives: `YYYY-MM_project-name_archive.7z` with a `README.txt` describing contents and archive date.
