---
description: >
  Propose a plan first, then move or delete only what the user confirms, batch by batch.
  TRIGGER WHEN: organizing messy folders (Downloads, Desktop, Documents), finding duplicate files, cleaning up directories, or restructuring file hierarchies.
  DO NOT TRIGGER WHEN: the task is about code refactoring (use /clean-code:clean-code or /python-development:python-refactor).
argument-hint: "<path> [find duplicates | by type | by date]"
---

# File Organizer

This entry organizes personal/document folders or inactive archives. An active
repository needs its project-specific development and hygiene process; do not
rearrange its source, tests, instructions or run artifacts through this organizer.

Use the `file-organizer` skill to organize, cleanup, and restructure:

$ARGUMENTS

**Safety**: the skill always proposes a plan and asks for approval before moving or deleting anything. Destructive operations (duplicate removal, file deletion) require explicit confirmation per batch.

## Quick Examples

- `/organize-files Downloads` - Organize Downloads folder by file type
- `/organize-files ~/Documents find duplicates` - Find and remove duplicate files
- `/organize-files ~/Projects archive old` - Archive inactive projects
- `/organize-files . cleanup` - Clean up current directory
