# Workspace evidence packet

Scope full/content; repository conventions publish dist as a documented package. All records below share candidate C.

## Git inventory and intent
| path | Git state | owner/intent |
|---|---|---|
| fixtures/nul | tracked | parser fixture referenced by test |
| pkg/module.py | tracked | Python source |
| dist/index.js | tracked | required published SDK artifact |
| scratch/trace.txt | ignored | local debug output retained by owner |
| .daodan/runs/R/work.json | ignored | active project record; .daodan-root sentinel present |
| docs/logo.svg | tracked | site.config points to it |
| app.json | tracked | required ungenerated configuration |
| src/new.ts | added | required source |

## Ignore sources
Tracked .gitignore:
```gitignore
__pycache__/
*.pyc
node_modules/
scratch/
```
node_modules is currently absent; npm is an active stack. Local/global ignores affect only local/editor files.

## Auxiliary state
- stash@{0}: active feature work, owner confirmed needed.
- no other stash, worktree or bisect state.
