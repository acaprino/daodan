# Workspace evidence packet

Scope full/content; repository conventions publish dist as a documented package. All records below share candidate C.

## Git inventory and intent
| path | Git state | owner/intent |
|---|---|---|
| nul | tracked | command transcript and author note identify accidental shell redirection; no fixture references |
| pkg/__pycache__/module.cpython-313.pyc | tracked | interpreter-generated, source pkg/module.py exists |
| dist/index.js | tracked | required published SDK artifact |
| scratch/trace.txt | tracked | temporary completed debug output; no retained outcome |
| .daodan/runs/R/work.json | ignored | active project record; .daodan-root sentinel present |
| docs/report.png | tracked | old report removed; complete source/config/CSS/template/generator/docs inventory has no binding |
| docs/logo.svg | tracked | site.config points to it |
| src/new.ts | added | required source |

## Ignore sources
Tracked .gitignore:
```gitignore
*.json
node_modules/
```
Required ungenerated app.json is ignored. pkg contains Python source and no bytecode exclusion exists. Local .git/info/exclude ignores local.log; global ignore hides editor caches.

## Auxiliary state
- stash@{0}: active feature work, owner confirmed needed.
- stash@{1}: completed incident scratch, owner has not authorized disposal.
- no other worktree or bisect state.
