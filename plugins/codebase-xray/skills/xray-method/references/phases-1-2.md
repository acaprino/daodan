# Phases 1 and 2

## Phase 1: Structure Extraction

Build the structural map from the current manifest. The inventory is what `snapshot.py` records: source in the parsed languages, stylesheets included with one symbol per rule, except a minified one, which stays file-level; configuration and documentation; and presentation files no adapter parses (markup, single-file components, indented Sass: file-level with no symbols). Any other extension is absent from the inventory and from every count derived from it, and the final report says so rather than letting a file count read as coverage. All of it sits inside the perimeter: nothing Git ignores and nothing under a dot directory enters the inventory, and the manifest's `scope` block says what was left out.

For each inventoried file, report recorded metadata and read source only for
additional claims required by the phase:
- Module/file name and path
- Language and framework
- Imports and dependencies
- Exported symbols (functions, classes, constants)
- File size and complexity indicators (line count, function count)

**Output file:** `$RUN_DIR/01-structure.md`

```markdown
# Phase 1: Structure Extraction

## File Inventory
| File | Language | Lines | Functions | Classes | Imports |
|------|----------|-------|-----------|---------|---------|
| ... | ... | ... | ... | ... | ... |

## Dependency Graph
[Mermaid diagram of module dependencies]

## Entry Points
[Main files, API routes, CLI handlers]

## Key Observations
[Notable structural patterns or concerns]

## Where to Add New Code
[For each major directory, describe what belongs there]
- New feature module: `[path]`
- New API endpoint: `[path]`
- New utility: `[path]`
- New tests: `[path]`

## Naming Conventions
[Prescriptive: "Use X" not "X is used"]
- Files: [pattern]
- Functions: [pattern]
- Classes: [pattern]
```

Update `$RUN_DIR/state.json`: add phase 1 to `completed_phases`.

---

## Phase 2: Interface Analysis

For each module, document the public interface:

Locate definitions in the manifest, then verify their public contract through
source blocks and the types, validators and configuration it depends on.

- Function signatures with parameter types and return types
- Class hierarchies and method signatures
- API endpoints with request/response shapes
- Configuration interfaces
- Event/signal contracts

**Output file:** `$RUN_DIR/02-interfaces.md`

```markdown
# Phase 2: Interface Analysis

## Public APIs
[Organized by module]

## Contracts
[Interface definitions, type shapes, schemas]

## External Dependencies
[Third-party libraries and how they're used]

## How to Add a New Module
[Step-by-step guide based on existing patterns]
1. Create file at `[path]`
2. Follow interface pattern from `[example file]`
3. Register in `[registration point]`
4. Add tests at `[test path]`
```
