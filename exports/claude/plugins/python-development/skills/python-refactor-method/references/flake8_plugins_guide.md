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
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Flake8 Plugins Guide for Human-Readable Code

Curated 16-plugin selector list for readability-focused linting. Per-plugin rule walkthroughs live in each plugin's PyPI README; this file is the **selection rationale** + recommended-setup tiers + the small set of rules worth memorizing.

## When to use

Setting up flake8 for a new project, or auditing an existing flake8 / ruff config to see which readability rules are missing. For ruff equivalents, see notes below.

## The curated 16 plugins (the local IP)

Organized in three priority tiers. The tier you adopt depends on team appetite for lint-driven feedback.

### Essential (5) -- highest ROI, install first

| # | Plugin | Codes | Catches |
|---|--------|-------|---------|
| 1 | **flake8-bugbear** | `B` | Likely bugs: mutable default args (B006), bare `except` (B001), function-call defaults (B008) |
| 2 | **flake8-simplify** | `SIM` | Pythonic alternatives: nested-if collapse (SIM102), `contextlib.suppress` (SIM105), ternary (SIM108) |
| 3 | **flake8-cognitive-complexity** | `CCR` | Sonar cognitive-complexity score per function (15 default threshold) |
| 4 | **pep8-naming** | `N` | snake_case / PascalCase / SCREAMING_SNAKE_CASE compliance |
| 5 | **flake8-docstrings** | `D` | PEP 257: missing docstrings, imperative mood, period termination |

### Recommended (7) -- catches subtler issues

| # | Plugin | Codes | Catches |
|---|--------|-------|---------|
| 6 | **flake8-comprehensions** | `C4` | Wasteful comprehension patterns (`list(map(...))`, `dict([(k,v)])`) |
| 7 | **flake8-expression-complexity** | `ECE` | Too-complex single expressions (lambda chains, deep ternaries) |
| 8 | **flake8-functions** | `CFQ` | Function length, parameter count, return count |
| 9 | **flake8-variables-names** | `VNE` | Single-letter / numeric / shadowed names |
| 10 | **tryceratops** | `TC` | try/except antipatterns (catching too broad, raise-from-from, abuse-of-finally) |
| 11 | **flake8-builtins** | `A` | Shadowing built-ins (`list = ...`, `id = ...`, `type = ...`) |
| 12 | **flake8-eradicate** | `E800` | Commented-out code (use VCS instead) |

### Optional (4) -- strict / opinionated

| # | Plugin | Codes | Catches |
|---|--------|-------|---------|
| 13 | **flake8-unused-arguments** | `U` | Unused function arguments (often a refactor smell) |
| 14 | **flake8-annotations** | `ANN` | Missing type annotations |
| 15 | **pydoclint** | `DOC` | Docstring/signature mismatch (param name typo, missing param in docstring) |
| 16 | **flake8-spellcheck** | `SC` | Spelling in identifiers and comments (US English dict + custom whitelist) |

## Recommended setup tiers

### Minimal (5)
```bash
pip install flake8 flake8-bugbear flake8-simplify \
            flake8-cognitive-complexity pep8-naming flake8-docstrings
```

### Recommended (12)
```bash
pip install flake8 flake8-bugbear flake8-simplify \
            flake8-cognitive-complexity pep8-naming flake8-docstrings \
            flake8-comprehensions flake8-expression-complexity \
            flake8-functions flake8-variables-names tryceratops \
            flake8-builtins flake8-eradicate
```

### Full (16) -- adds the strict/opinionated tier
```bash
# Plus:
pip install flake8-unused-arguments flake8-annotations pydoclint flake8-spellcheck
```

## Gotchas

- **Cognitive complexity > Cyclomatic complexity** for readability. Cyclomatic counts decision paths; cognitive adds nesting penalties. Use a cognitive-specific tool for that metric; [Ruff C901](https://docs.astral.sh/ruff/rules/complex-structure/) measures McCabe cyclomatic complexity.
- **`flake8-docstrings` checks PEP 257 compliance** but not coverage -- pair with `interrogate` for "% functions with docstrings."
- **`flake8-bugbear B006` is the highest-value single rule** -- mutable default arg is one of the top 3 Python footguns.
- **`tryceratops TRY003` ("avoid specifying long messages outside exception class")** is opinionated -- toggle if your team prefers inline messages.
- **`pep8-naming N803`** flags non-snake_case argument names. Disable for compatibility shims that mirror C library APIs.
- **Spell-check (`flake8-spellcheck`) needs a whitelist file** (`whitelist.txt`) for project-specific terms -- otherwise it flags every brand name and acronym.

## Rules you'll be tempted to disable but shouldn't

- `B006` (mutable default args)
- `B008` (function-call default args, e.g. `datetime.now()` in a default)
- `B904` ("raise without from inside except" -- always preserve traceback chain)
- `SIM102` (collapse nested ifs)
- `SIM105` (`contextlib.suppress` over try/except/pass)
- `N803` / `N806` (snake_case discipline)
- `E800` (no commented-out code -- VCS exists)

## ruff: the 2025+ alternative

`ruff` re-implements most of these in Rust at 100× the speed. Equivalent rule sets:

```toml
[tool.ruff.lint]
select = [
  "E", "W", "F",         # pycodestyle + pyflakes
  "B",                   # flake8-bugbear
  "SIM",                 # flake8-simplify
  "C4",                  # flake8-comprehensions
  "C901",                # cyclomatic complexity (McCabe)
  "N",                   # pep8-naming
  "D",                   # pydocstyle
  "TRY",                 # tryceratops
  "A",                   # flake8-builtins
  "ERA",                 # flake8-eradicate
  "ARG",                 # flake8-unused-arguments
  "ANN",                 # flake8-annotations
  "I",                   # isort
  "UP",                  # pyupgrade
]
```

ruff covers ~95% of the curated 16 plus more. New projects in 2025-2026 should start with ruff; flake8 stays for legacy projects with custom plugin sets.

## Per-plugin documentation

| Plugin | Docs |
|--------|------|
| flake8 (core) | https://flake8.pycqa.org/ |
| flake8-bugbear | https://github.com/PyCQA/flake8-bugbear |
| flake8-simplify | https://github.com/MartinThoma/flake8-simplify |
| flake8-cognitive-complexity | https://github.com/Melevir/flake8-cognitive-complexity |
| pep8-naming | https://github.com/PyCQA/pep8-naming |
| flake8-docstrings | https://github.com/pycqa/flake8-docstrings |
| flake8-comprehensions | https://github.com/adamchainz/flake8-comprehensions |
| flake8-expression-complexity | https://github.com/best-doctor/flake8-expression-complexity |
| flake8-functions | https://github.com/best-doctor/flake8-functions |
| flake8-variables-names | https://github.com/best-doctor/flake8-variables-names |
| tryceratops | https://github.com/guilatrova/tryceratops |
| flake8-builtins | https://github.com/gforcada/flake8-builtins |
| flake8-eradicate | https://github.com/wemake-services/flake8-eradicate |
| flake8-unused-arguments | https://github.com/nhoad/flake8-unused-arguments |
| flake8-annotations | https://github.com/sco1/flake8-annotations |
| pydoclint | https://github.com/jsh9/pydoclint |
| flake8-spellcheck | https://github.com/MichaelAquilina/flake8-spellcheck |
| ruff (modern alternative) | https://docs.astral.sh/ruff/ |

## Cognitive complexity reference

Threshold guidance from Sonar (which flake8-cognitive-complexity adapts):

| Score | Quality |
|-------|---------|
| 0-10 | Clean, easy to understand |
| 11-15 | Moderate -- watch for further additions |
| 16-25 | Hard to understand, refactor candidate |
| 26+ | Untestable in practice |

Default flake8-cognitive-complexity threshold is 15. Lower to 10 for high-discipline projects.

## Related

- `cognitive_complexity_guide.md` -- the full Sonar-derived metric explanation with worked examples
- `anti-patterns.md` -- catalog with detection criteria + impact analysis
- `patterns.md` -- positive refactoring patterns (the alternatives these plugins suggest)
- `python-refactor-method/SKILL.md` -- workflow that runs these plugins as gates
