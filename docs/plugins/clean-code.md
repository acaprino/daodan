# Clean Code Plugin

> Rewrite source code to be more readable and human-friendly without changing behavior. Improves naming, removes AI boilerplate, simplifies structure, and adds clarity comments, with mandatory validation before and after.

## Agents

### `clean-code-agent`

Rewrites source code for readability and maintainability with zero behavior changes.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | `Read, Edit, Write, Glob, Grep, Bash, Task` |
| **Use for** | Code cleanup, naming improvements, removing AI-generated boilerplate, simplifying structure |

**Invocation:**
```
Use the clean-code-agent to clean up [file/module]
```

**What it does:**
- Renames vague variables and parameters to domain-meaningful names
- Removes paraphrase comments and empty boilerplate docstrings
- Adds brief why-comments for non-obvious business logic
- Simplifies overly complex expressions and control flow

**Safety rules (what it must never touch):**
- Error handling (try/catch, try/except, error callbacks)
- Validations and type-checks (guard clauses, assertions)
- Import statements (may have side effects)
- Top-level declaration order
- Test files (unless renaming symbols it renamed in source)

---

## Commands

### `/clean-code:clean-code`

Rewrite source code for readability with validation checkpoints.

```
/clean-code:clean-code src/utils.py
/clean-code:clean-code src/ --dry-run
/clean-code:clean-code src/ --yes --strict
```

| Flag | Effect |
|------|--------|
| `--dry-run` | Preview changes without modifying files, then stop |
| `--yes` | Skip the confirmation prompts and apply after showing the preview. Never bypasses the no-validation hard gate |
| `--strict` | Step 5 also flags remaining readability concerns that were not auto-fixable |
| `--force` | The only way past the hard gate: proceed even without tests or a type checker |

**Pipeline:**
1. **Identify target:** a file, or every source file in a directory, with test files filtered out
2. **Establish validation baseline:** detects and runs the type checker, test runner and linter. **Hard gate:** with no tests and no type checker it stops and offers cancel or `--force`
3. **Preview:** mandatory for `--dry-run` or a directory with more than 3 files; lists the proposed renames, comment removals and additions, and structural simplifications, and asks apply all, apply to specific files, or cancel
4. **Apply:** spawns `clean-code-agent` with the file list and the approved changes
5. **Validate and report:** re-runs the checks in order (type checker, tests, linter), reverting a file whose type check or previously passing tests now fail, fixing or reverting on new lint errors, then greps non-code files (`.json`, `.yaml`, `.toml`, `.env`, `.md` and similar) for the old names of renamed symbols and reports stale references as warnings

---

**Related:** the upstream agent-teams `/agent-teams:team-feature` (wshobson/agents) can include clean-code as a final step | [senior-review](senior-review.md) (code review before cleaning)
