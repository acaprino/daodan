# System Utils Plugin

> Tame messy folders. Organizes files, finds duplicates, and cleans up directories with approval before any changes.

## Skills

### `file-organizer`

Personal organization assistant for maintaining clean, logical file structures.

| | |
|---|---|
| **Invoke** | Skill reference or `/system-utils:organize-files` |
| **Use for** | Messy folders, duplicates, old files, project restructuring |

**Capabilities:**
- **Analyze**: Review folder structure and file types
- **Find Duplicates**: Identify duplicate files by hash
- **Suggest Structure**: Propose logical folder organization
- **Automate**: Move, rename, organize with approval
- **Cleanup**: Identify old/unused files for archiving

---

## Commands

### `/system-utils:organize-files`

Quick command to organize files and directories.

```
/system-utils:organize-files Downloads
```

**Examples:**
| Command | Action |
|---------|--------|
| `/system-utils:organize-files Downloads` | Organize Downloads by type |
| `/system-utils:organize-files ~/Documents find duplicates` | Find duplicate files |
| `/system-utils:organize-files ~/Projects archive old` | Archive inactive projects |
| `/system-utils:organize-files . cleanup` | Clean up current directory |

---

**Related:** [senior-review](senior-review.md) (`/code-review --fix` for removing unused code)
