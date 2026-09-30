# Obsidian Development Plugin

> Obsidian community plugin development with automated review compliance (Community hub, community.obsidian.md), project scaffolding, and pre-submission checks.

## Skills

### `obsidian-plugin-development`

Write Obsidian plugin code that passes Obsidian's automated plugin review on first submission. Since May 2026 plugins are submitted and reviewed through the Community hub at community.obsidian.md, which scans every GitHub release; the old PR workflow gated by ObsidianReviewBot is retired, and a failing version of an already-listed plugin is removed from directory search within 24 hours. Covers the required rules enforced by `eslint-plugin-obsidianmd` and `@typescript-eslint`, with code examples.

| | |
|---|---|
| **Trigger** | Writing, reviewing, or fixing Obsidian community plugin code |
| **Coverage** | 25 required rules (sentence case, no inline styles, promise handling, etc.), API reference |
| **Reference** | Condensed TypeScript API reference for Plugin, Vault, Workspace, Setting, Modal, and more |

### `obsidian-scaffold`

Scaffold a new Obsidian community plugin project, compliant with the automated review from day one.

| | |
|---|---|
| **Trigger** | Creating a new Obsidian plugin from scratch |
| **Creates** | `manifest.json`, `package.json`, `tsconfig.json`, `esbuild.config.mjs`, `eslint.config.mjs` (flat config with `eslint-plugin-obsidianmd` and eslint-comments), `src/main.ts`, `styles.css`, `LICENSE`, `README.md`, `.gitignore` |
| **Validates** | Plugin ID, name, and description against the automated review rules |

### `obsidian-check`

Pre-submission lint and review against the automated review that the Community hub runs on every GitHub release. Auto-installs `eslint-plugin-obsidianmd` and `@eslint-community/eslint-plugin-eslint-comments` if missing, runs the obsidianmd recommended rule set (including `ui/sentence-case`) over `src/` and `package.json`, plus manual checks the linter does not cover.

| | |
|---|---|
| **Trigger** | Before pushing or submitting an Obsidian plugin |
| **Auto-setup** | Installs `eslint-plugin-obsidianmd`, `@eslint-community/eslint-plugin-eslint-comments` and their peer dependencies if not present; if no ESLint config exists, writes an `eslint.config.mjs` with the obsidianmd recommended config plus the eslint-comments rules the review platform adds (`require-description`, and `no-restricted-disable` for `obsidianmd/no-static-styles-assignment` and `obsidianmd/ui/sentence-case`) |
| **Checks** | TypeScript compilation, ESLint via `eslint-plugin-obsidianmd` recommended config over `src/` and `package.json` (sentence case, inline styles, commands, manifest, undescribed or forbidden `eslint-disable` directives, deprecated dependencies, etc.), 6 required + 5 optional manual checks, manifest validation, LICENSE |
| **Output** | Structured report with severity grouping, file:line locations, and suggested fixes |

---

**Related:** [typescript-development](typescript-development.md) (TypeScript coding standards) | [learning](learning.md) (mind maps for Obsidian MarkMind)
