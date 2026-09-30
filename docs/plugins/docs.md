# Docs Plugin

> Craft magnetic, top-tier README.md files that capture attention in 3 seconds, prove value in 10, and get developers running code in 60.

## Skills

### `readme-craft`

Produces polished README.md files following open-source best practices: progressive disclosure, hero section with badges, visual proof, quick start, feature tables, collapsible advanced config, Mermaid architecture diagrams, and community sections.

| | |
|---|---|
| **Trigger** | "readme", "write a readme", "create readme", "scrivi il readme" |
| **Auto-detects** | Project name, tech stack, license, version, install commands, features, logo, CI/CD |
| **Asks user for** | Only what it cannot infer: logo, Discord link, demo GIF, badge style, copyright holder |

**How it works:**

1. **Scans the project** silently: reads manifests, LICENSE, README, source files, assets, CI config
2. **Presents a pre-filled brief** with everything it inferred
3. **Asks only for missing metadata** (license, logo, community link, sponsor link)
4. **Generates the README** following a strict progressive disclosure funnel

It runs every step itself in the conversation and never spawns agents. When a README.md already exists, it asks whether to replace it entirely or merge improvements into the existing structure.

**README structure generated:**

| Section | Purpose |
|---------|---------|
| Hero (centered) | Logo with dark/light mode, title, one-liner, 4-6 shields.io badges |
| Visual proof | Demo GIF or screenshot (skipped if none available) |
| Why this project? | 3-5 emoji bullet points with key features |
| Quick Start | Copy-pasteable install + run commands (60-second rule) |
| Features & Config | Command tables + collapsible advanced config |
| Architecture | Mermaid.js diagram (optional, only if meaningful) |
| Community | Contributing link, Discord, good-first-issue, contributors wall |
| Sponsors | GitHub Sponsors badge (optional) |
| Star History | Star history chart (optional) |
| Footer | License link, author credit |

**Quality rules:**
- No placeholder images: text-only hero if no logo exists
- Badges point to real URLs constructed from project metadata
- All code blocks are copy-pasteable (no `$` prefix)
- Collapsible `<details>` for anything over 15 lines
- Around 200 lines total, with 300 as a hard ceiling; anything longer links out to `docs/`
- Dark/light mode support via `<picture>` tags

---

## Commands

### `/docs:maintain-readme`

Audit, restructure, and improve an existing README.md: verifies accuracy against the codebase, fixes stale links and stats, improves structure, and optionally rewrites sections.

| | |
|---|---|
| **Use for** | Stale stats/badges, outdated feature lists, structural improvements, full restructure |

**Audit report:** before any change, the command scans the codebase silently and presents its findings in four categories:

| Category | Examples |
|---|---|
| **Critical** (factual errors) | Wrong counts, versions or stats; nonexistent paths; badges pointing at the wrong package; commands that do not work |
| **Structural** (information architecture) | Missing progressive disclosure, wrong section order for the adoption funnel, missing quick start or install, a README over 300 lines without collapsibles |
| **Content Quality** | Buried value proposition, a quick start that is not copy-pasteable, vague features, no visual proof when screenshots exist |
| **Freshness** | Stale version numbers, references to removed features, links to moved files, stats that no longer match |

**Audit levels:**

| Level | What it does |
|-------|-------------|
| **A) Fix facts only** | Correct counts, versions, paths, badges, links |
| **B) Fix facts + improve structure** | Reorder sections, add missing sections, apply progressive disclosure |
| **C) Full restructure** | Rewrite following readme-craft best practices, rebuild information architecture |

**Approval gates:** nothing is written until you approve. You pick the level (A, B or C) after seeing the audit, and the command then shows a diff or summary of the proposed changes and waits for confirmation before writing README.md. It closes with a list of manual follow-ups (missing screenshots, broken external URLs).

---

**Related:** [codebase-mapper](codebase-mapper.md) (technical documentation) | [project-setup](project-setup.md) (CLAUDE.md files)
