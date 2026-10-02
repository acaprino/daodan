# OpenCode V2 Host Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile every Daodan kernel into a fifth package, `exports/opencode/`, installable into OpenCode V2 (CLI and Desktop) through a generated, data-driven JS loader, after renaming the five cross-kind homonyms.

**Architecture:** A new adapter `adapters/opencode/` renders skills, agents and commands like the other hosts. The compiler also writes a package `package.json` whose `daodan` key carries every plugin's components, permissions, dependencies and MCP servers, and copies a fixed dependency-free `index.js` that registers them through the V2 plugin transform hooks. A new validator rule forbids a name shared across component kinds inside a plugin, and five kernel components are renamed to satisfy it.

**Tech Stack:** Python 3.11 stdlib (compiler, tests), plain ES-module JavaScript with no dependency (loader), `node --test` (loader tests).

**Spec:** `docs/superpowers/specs/2026-10-02-opencode-host-adapter-design.md`

## Global Constraints

- Target OpenCode V2 only (`@opencode/cli` 2.0.x, source tag `v2.0.22`). No V1 export, no `opencode-ai` API.
- The loader imports nothing outside Node's standard library (`node:fs`, `node:path`, `node:url`). No `@opencode/plugin`, no `effect`.
- The loader never throws out of `setup`, and never throws out of a transform callback.
- IDs: workflows `<plugin>:<workflow>`, roles `<plugin>:<role>`, skills `<plugin>:<skill>`.
- Install line, verbatim: `opencode plugin add 'github:acaprino/daodan#v<metadata.version>::path:exports/opencode'`.
- Package manifest fields: `name: "daodan"`, `version` = `metadata.version`, `private: true`, `type: "module"`, `main: "index.js"`, `keywords: ["opencode-plugin"]`, plus the `daodan` key.
- Marketplace version becomes `29.0.0`.
- Renames, verbatim: role `abstraction-architect` to `abstraction-architect-agent`; role `firefox-extension-dev` to `firefox-extension-dev-agent`; skill `brand-naming` to `brand-naming-method`; skill `reply-to-customer-review` to `review-reply-method`; skill `python-refactor` to `python-refactor-method`. Workflows and plugin names keep their names. `.python-refactor/` and `.abstraction-architect/` do not move.
- Plugin bumps: major for `abstraction-architect` (3.0.1 to 4.0.0), `browser-extensions` (1.8.1 to 2.0.0), `digital-marketing` (2.3.2 to 3.0.0), `python-development` (1.22.1 to 2.0.0); patch for `senior-review` (12.0.2 to 12.0.3), `clean-code` (1.3.1 to 1.3.2), `marketplace-ops` (2.3.0 to 2.3.1), `system-utils` (2.1.0 to 2.1.1).
- No dash-aside construct anywhere (`—`, ` -- `, ` - ` bracketing a clause), in code, comments, docs or commit messages.
- Nothing under `exports/` and no root catalog is edited by hand; every one is rebuilt with `python scripts/daodan_build.py`.

## Review Focus

- **A user selects a plugin whose dependency they also excluded.** Expected: the dependency stays loaded and the log names who needs it. Pinned in Task 5 (`exclude yields to a dependency`).
- **A user's own config already defines an agent, skill or command with a Daodan ID.** Expected for MCP: the user's server wins and is logged. For agents, `update` would merge into the user's entry; the loader only touches IDs it owns, so the user's fields are overwritten only for those IDs. Pinned in Task 5 (`existing MCP server left alone`); the agent case is a documented behaviour in the README (Task 8).
- **A command invoked with quoted arguments, fewer arguments than placeholders, or no placeholder at all.** Expected: the core's semantics exactly. Pinned in Task 5 (argument expansion table).
- **A role whose body reads `references/...` from the installed package, outside the project.** Expected: allowed by the scoped `external_directory` rule, never by `*`. Pinned in Task 3 (permission list ends with the package-scoped rule) and Task 5 (`<package-root>` substituted).
- **The package is loaded from a path containing spaces or backslashes (Windows).** Expected: every registered `path` is absolute and `<plugin-root>` substitution uses forward slashes. Pinned in Task 5 (`windows-style root`).

---

### Task 1: Forbid names shared across component kinds

**Files:**
- Modify: `scripts/daodan/validate.py` (add `validate_component_kinds`, call it from `validate_plugins`)
- Test: `tests/test_daodan_validate.py`

**Interfaces:**
- Produces: `validate_component_kinds(plugin: PluginSpec) -> list[ValidationIssue]`, issue code `component-name-shared-across-kinds`, detail `"<name>: <kind>, <kind>"` with kinds in the order `skills, roles, workflows`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_daodan_validate.py`, using the existing fixture-building helpers of that file:

```python
def test_skill_and_role_sharing_a_name_fail(self):
    issues = validate_component_kinds(plugin_with(skills=["x"], roles=["x"]))
    self.assertEqual([i.code for i in issues], ["component-name-shared-across-kinds"])
    self.assertEqual(issues[0].detail, "x: skills, roles")

def test_skill_and_workflow_sharing_a_name_fail(self): ...  # detail "x: skills, workflows"
def test_role_and_workflow_sharing_a_name_fail(self): ...   # detail "x: roles, workflows"

def test_real_kernels_have_no_cross_kind_homonym(self):
    plugins = discover_plugins(REPO_ROOT)
    self.assertEqual([i for p in plugins for i in validate_component_kinds(p)], [])
```

`plugin_with` is whatever helper the file already uses to build a `PluginSpec`; if none builds components directly, add one that writes a minimal kernel to a temp dir and calls `load_plugin`.

- [ ] **Step 2: Run, expect FAIL**

Run: `python -m unittest tests.test_daodan_validate -v`
Expected: the three synthetic cases fail with `NameError: validate_component_kinds`; the real-kernel case also fails (five homonyms), which stays red until Task 2.

- [ ] **Step 3: Implement `validate_component_kinds` and add it to `validate_plugins`**

Iterate `("skills", "roles", "workflows")` over `plugin.components`, map each name to the kinds containing it, emit one issue per name with two or more kinds, sorted by name. The file path is `plugin.root / "plugin.toml"`, like the other component issues.

- [ ] **Step 4: Run, expect the three synthetic cases PASS and the real-kernel case FAIL**

Run: `python -m unittest tests.test_daodan_validate -v`

- [ ] **Step 5: Commit** (the build stays red on validation until Task 2; commit them together if the executor prefers a green history)

```bash
git add scripts/daodan/validate.py tests/test_daodan_validate.py
git commit -m "Refuse a component name shared across kinds inside a plugin"
```

### Task 2: Rename the five homonyms in the kernels

**Files:**
- Rename: `plugins/abstraction-architect/roles/abstraction-architect.md` to `abstraction-architect-agent.md`
- Rename: `plugins/browser-extensions/roles/firefox-extension-dev.md` to `firefox-extension-dev-agent.md`
- Rename: `plugins/digital-marketing/skills/brand-naming/` to `brand-naming-method/`
- Rename: `plugins/digital-marketing/skills/reply-to-customer-review/` to `review-reply-method/`
- Rename: `plugins/python-development/skills/python-refactor/` to `python-refactor-method/`
- Modify: the eight `plugin.toml` files listed in Global Constraints (components and version)
- Modify: `plugins/abstraction-architect/workflows/audit.toml` (`role =`)
- Modify: `plugins/browser-extensions/workflows/firefox-{lint,publish,scaffold}.{md,toml}`, `plugins/browser-extensions/skills/firefox-extension-dev/SKILL.md`
- Modify: `plugins/senior-review/roles/code-auditor.md`, `plugins/senior-review/workflows/{code-review,team-review}.md`, `plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md`
- Modify: `plugins/digital-marketing/workflows/{brand-naming,reply-to-customer-review}.md`
- Modify: `plugins/clean-code/roles/clean-code-agent.md`, `plugins/python-development/roles/python-refactor-agent.md`, `plugins/python-development/skills/python-comments/SKILL.md`, `plugins/python-development/skills/python-performance-optimization/references/optimization-patterns.md`, `plugins/marketplace-ops/skills/skills-creator/references/skills-vs-agents.md`, `plugins/system-utils/workflows/organize-files.md`
- Modify: `docs/plugins/{abstraction-architect,browser-extensions,digital-marketing,python-development,senior-review,text-humanizer}.md`, `README.md` (line with `/python-refactor` keeps the command; only skill mentions change)
- Modify: `.claude/skills/downstream-exports/SKILL.md` (the `-workflow` paragraph, see spec section 11), `tests/test_daodan_host_rendering.py:173` comment
- Modify: `.claude-plugin/marketplace.json` `metadata.version` to `29.0.0`

**Interfaces:**
- Consumes: Task 1's rule as the acceptance gate.
- Produces: the five new names, which Task 3 onward renders.

- [ ] **Step 1: List every occurrence and classify it**

Run: `git grep -nwE "abstraction-architect|firefox-extension-dev|brand-naming|reply-to-customer-review|python-refactor" -- plugins docs/plugins README.md .claude tests scripts`
Classify each hit as plugin name, role, skill, workflow (`/plugin:name` or a `workflows/` path), or artifact path (`.python-refactor/`, `.abstraction-architect/`). Only role and skill hits change. Every `subagent_type`, `Load the skill`, "agent" and "skill" mention is decided by its sentence, not by its token.

- [ ] **Step 2: `git mv` the five components, edit frontmatter `name`, edit every role and skill reference from Step 1**

Inside each renamed skill directory, references to sibling files (`references/...`, `assets/...`) are relative and need no change.

- [ ] **Step 3: Bump the eight plugin versions and `metadata.version`**

- [ ] **Step 4: Rebuild and run the gates**

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check --support
python -m unittest discover -s tests
python scripts/lint_dependency_graph.py && python scripts/lint_bundled_paths.py && python scripts/lint_plugin_registration.py && python scripts/lint_host_vocabulary.py && python scripts/lint_fact_anchors.py
git grep -nwE "abstraction-architect:abstraction-architect\b|browser-extensions:firefox-extension-dev\b" -- plugins docs
```
Expected: build exit 0, every test passes including Task 1's real-kernel case, every linter `ok`, and the last grep returns nothing.

- [ ] **Step 5: Commit**

```bash
git add -A plugins docs README.md .claude tests exports .claude-plugin .github/plugin .agents package.json
git commit -m "Rename the five components that shared a name across kinds (29.0.0)"
```

### Task 3: Add the OpenCode adapter and render its packages

**Files:**
- Create: `adapters/opencode/capabilities.toml`, `coordination.toml`, `layout.toml` (content: spec 4.1 to 4.3 verbatim)
- Create: `adapters/opencode/templates/agent.md.tmpl`, `adapters/opencode/templates/team-command.md.tmpl`
- Modify: `scripts/daodan/adapter.py` (`HOSTS`), `scripts/daodan/render.py` (`OPENCODE_PERMISSIONS`, `opencode_permissions`, role template context key `permissions`)
- Test: `tests/test_daodan_host_rendering.py` (new `OpenCodeRenderingTests`)

**Interfaces:**
- Produces: `HOSTS = ("claude", "copilot", "codex", "pi", "opencode")`.
- Produces: `opencode_permissions(tools: str) -> list[dict[str, str]]` in `render.py`. Map: `Read`/`Glob`/`Grep` to `read`/`glob`/`grep`; `Write`/`Edit`/`NotebookEdit` to `edit`; `Bash` to `shell`; `WebFetch` to `webfetch`; `WebSearch` to `websearch`; `Agent`/`Task` to `subagent`. Result: `[]` for an empty `tools`; otherwise `[{"action":"*","resource":"*","effect":"deny"}]`, then one `allow` per mapped action in first-seen order, then `{"action":"skill","resource":"*","effect":"allow"}`, then `{"action":"external_directory","resource":"<package-root>/**","effect":"allow"}`. `COPILOT_TOOLS` and the new map live side by side under one comment so they cannot drift silently.
- Produces: rendered files at `exports/opencode/plugins/<p>/{skills/<s>/SKILL.md, agents/<r>.md, commands/<w>.md, contracts/...}`.

- [ ] **Step 1: Write the failing tests**

```python
class OpenCodeRenderingTests(HostRenderingTests):  # reuses setUpClass packages
    def test_agent_frontmatter_is_a_v2_subagent(self):
        text = _read(self.packages[("opencode", "senior-review")] / "agents/code-auditor.md")
        meta = _frontmatter(text)
        self.assertEqual(meta["mode"], "subagent")
        self.assertIn("permissions:", text)
        self.assertNotIn("tools:", text.split("\n---\n", 1)[0])

    def test_permissions_deny_first_and_scope_the_package(self):
        rules = opencode_permissions("Read, Grep, Bash")
        self.assertEqual(rules[0], {"action": "*", "resource": "*", "effect": "deny"})
        self.assertEqual(rules[-1], {"action": "external_directory", "resource": "<package-root>/**", "effect": "allow"})
        self.assertNotIn({"action": "external_directory", "resource": "*", "effect": "allow"}, rules)
        self.assertEqual(opencode_permissions(""), [])

    def test_team_command_dispatches_with_the_subagent_tool(self):
        text = _read(self.packages[("opencode", "senior-review")] / "commands/team-review.md")
        self.assertIn("`subagent` tool", text)
        self.assertIn('agent: "senior-review:', text)
        self.assertIn("$ARGUMENTS", text)

    def test_plugin_root_becomes_the_marker(self):
        for path in self.packages[("opencode", "codebase-xray")].rglob("*.md"):
            self.assertNotIn(CLAUDE_ROOT, _read(path), path)

    def test_no_command_body_uses_shell_template_syntax(self):
        for path in self.packages[("opencode", "senior-review")].glob("commands/*.md"):
            self.assertIsNone(re.search(r"(?m)^!`", _read(path)), path)
```

The real-kernel sweep for `` !` `` over every plugin goes in Task 4's manifest test, where all plugins are rendered.

- [ ] **Step 2: Run, expect FAIL** (`python -m unittest tests.test_daodan_host_rendering -v`; `KeyError: 'opencode'` or missing adapter)

- [ ] **Step 3: Write the adapter files and templates, add `"opencode"` to `HOSTS`, implement `opencode_permissions`, pass `permissions` (YAML list rendered inline, one rule per line) into the role template context**

`agent.md.tmpl` frontmatter: `description: '${description}'`, `mode: subagent`, `permissions:` followed by `${permissions}`, then the generated-file comment and `${body}`. `team-command.md.tmpl`: the Pi template's structure with the OpenCode mechanism from spec 4.4 (subagent tool, `agent: "${plugin}:<role>"`, `background: true` for workers of one phase under `parallel-subagents`, wait for every completion notice, no missing-tool branch, a `subagent` failure on a registered agent is a broken install).

- [ ] **Step 4: Run, expect PASS**, then `python -m unittest discover -s tests` (the four-host tests now iterate five hosts; fix their per-host tables in `test_cutover_identity.py`, `test_universal_catalog_parity.py`, `test_dependency_audit_ports.py`, `test_host_limits.py` by adding the `opencode` row, catalog path `exports/opencode/package.json`, workflow path `commands/deps-audit.md`, frontmatter prefix `---\ndescription:`)

- [ ] **Step 5: Commit**

```bash
git add adapters/opencode scripts/daodan tests
git commit -m "Add an OpenCode V2 adapter that renders agents and commands"
```

### Task 4: Render the package manifest and copy the loader

**Files:**
- Modify: `scripts/daodan/catalogs.py` (`_source` for opencode, `_opencode_manifest`, branch in `render_catalog`)
- Modify: `scripts/daodan_build.py` (`package_files` copy step, inside the same transactional publish as the catalog)
- Modify: `scripts/lint_plugin_registration.py` (`check_opencode`)
- Create: `adapters/opencode/templates/index.js` (empty `export default { id: "daodan", setup() {} }` placeholder; Task 5 replaces it)
- Test: `tests/test_daodan_catalogs.py`, `tests/test_daodan_cli.py`

**Interfaces:**
- Consumes: Task 3's rendered tree and `opencode_permissions`.
- Produces: `exports/opencode/package.json` with this `daodan` shape, which Task 5 reads:

```json
{
  "daodan": {
    "schema": 1,
    "plugins": {
      "<plugin>": {
        "root": "plugins/<plugin>",
        "dependencies": ["<local plugin>", "..."],
        "skills":   [{"id": "<plugin>:<skill>", "name": "<name>", "description": "...", "file": "skills/<skill>/SKILL.md"}],
        "agents":   [{"id": "<plugin>:<role>", "description": "...", "file": "agents/<role>.md", "permissions": [...]}],
        "commands": [{"name": "<plugin>:<workflow>", "description": "...", "file": "commands/<workflow>.md"}],
        "mcp":      [{"name": "<server>", "command": ["<cmd>", "<arg with <plugin-root>>"]}]
      }
    }
  }
}
```

`dependencies` holds only local plugin names (entries without `@`). `file` paths are relative to `root`. Empty lists are omitted. Keys sorted, two-space indent, trailing newline, like every catalog.

- [ ] **Step 1: Write the failing tests**

```python
def test_opencode_manifest_is_a_v2_plugin_package(self):
    catalog = build_fixture_catalogs()["opencode"]
    self.assertEqual(catalog["main"], "index.js")
    self.assertEqual(catalog["type"], "module")
    self.assertEqual(catalog["keywords"], ["opencode-plugin"])
    self.assertTrue(catalog["private"])
    self.assertEqual(catalog["daodan"]["schema"], 1)

def test_opencode_ids_carry_the_plugin_prefix(self):
    entry = live_opencode_manifest()["daodan"]["plugins"]["senior-review"]
    self.assertIn("senior-review:code-auditor", [a["id"] for a in entry["agents"]])
    self.assertIn("senior-review:code-review", [c["name"] for c in entry["commands"]])
    self.assertIn("codebase-xray", entry["dependencies"])
    self.assertNotIn("superpowers@claude-plugins-official", entry["dependencies"])

def test_every_manifest_file_exists_and_no_command_uses_shell_syntax(self):
    manifest = live_opencode_manifest()
    for name, entry in manifest["daodan"]["plugins"].items():
        for kind in ("skills", "agents", "commands"):
            for item in entry.get(kind, []):
                path = OPENCODE / entry["root"] / item["file"]
                self.assertTrue(path.is_file(), path)
                if kind == "commands":
                    self.assertIsNone(re.search(r"(?m)^!`", path.read_text(encoding="utf-8")), path)

def test_peer_review_declares_its_server(self):
    mcp = live_opencode_manifest()["daodan"]["plugins"]["peer-review"]["mcp"]
    self.assertEqual(mcp[0]["name"], "peer-review")
    self.assertTrue(any("<plugin-root>" in part for part in mcp[0]["command"]))
```

In `tests/test_daodan_cli.py`: a build of the fixture repository writes `exports/opencode/index.js` byte-identical to `adapters/opencode/templates/index.js`, and `--check` reports drift when that copy is edited.

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Implement**

`layout.toml` gets `marketplace = "exports/opencode/package.json"` and `package_files = "index.js"`. `_opencode_manifest(document, packages)` reads descriptions and names from the rendered frontmatter of each package (never from the kernel, so the manifest describes what ships), permissions by calling `opencode_permissions` on the kernel role's `tools`, and MCP from the plugin's `.mcp.json`-equivalent data (`plugin.mcp_servers` with `_host_arguments`). `render_catalog` therefore needs the `PluginSpec`s, which it already receives. The `package_files` copy runs in `build_repository` after the catalog, and under `--check` compares bytes like a catalog.

`check_opencode()` in the registration linter: every `file` in the manifest exists, and every rendered `skills/*/SKILL.md`, `agents/*.md`, `commands/*.md` under `exports/opencode/plugins/` appears in the manifest. Reported under `opencode manifest`.

- [ ] **Step 4: Run, expect PASS**; then `python scripts/daodan_build.py && python scripts/daodan_build.py --check --support && python scripts/lint_plugin_registration.py`

- [ ] **Step 5: Commit**

```bash
git add scripts adapters/opencode tests exports/opencode
git commit -m "Write the OpenCode package manifest and ship its loader"
```

### Task 5: Implement the loader

**Files:**
- Modify: `adapters/opencode/templates/index.js`
- Create: `tests/opencode/loader.test.mjs`, `tests/opencode/fixture/package.json` plus three tiny fixture plugins (`a` depends on `b`; `c` standalone; `a` has one skill, one agent, one command, one MCP server)
- Create: `tests/test_opencode_loader.py` (runs `node --test tests/opencode/loader.test.mjs`, `skipTest` when `shutil.which("node")` is None, asserts exit 0 and prints stdout on failure)

**Interfaces:**
- Consumes: Task 4's manifest shape.
- Produces, exported from `index.js` for tests: `default { id: "daodan", setup }`, and named exports `resolveSelection(manifest, options) -> { selected: string[], log: string[] }`, `expandTemplate(template, input) -> string`, `substituteRoot(text, pluginRoot, packageRoot) -> string`, `createLoader(packageDir)` returning `setup` bound to a directory (so tests point it at the fixture).

- [ ] **Step 1: Write the failing tests** in `loader.test.mjs` with `node:test` and `node:assert/strict`, and a fake `ctx` whose `skill/agent/command/mcp.transform(fn)` call `fn` on recording editors and resolve; `ctx.options` settable; `ctx.session.prompt` records its argument.

| test | assertion |
|---|---|
| no options loads everything | skill, agent, command IDs of `a`, `b`, `c` all registered |
| selection pulls in dependencies | `options.plugins=["a"]` registers `a` and `b`, not `c`; log mentions `b` required by `a` |
| exclude yields to a dependency | `plugins=["a"], exclude=["b"]` still registers `b`; log names `a` |
| exclude removes an unneeded plugin | `exclude=["c"]` registers `a`, `b` only |
| unknown name is logged, not fatal | `plugins=["zzz","c"]` registers `c`, log has an error for `zzz` |
| malformed manifest registers nothing | `package.json` without `daodan` key: no transform called, `setup` resolves |
| a rejected skill skips only itself | editor `add` throws for one ID: other skills still added, `setup` resolves |
| agent fields | `update` sets `mode:"subagent"`, `description`, `system` (body without frontmatter, root substituted), `permissions` with `<package-root>` replaced by the absolute package path |
| existing MCP server left alone | editor `get(name)` returns a config: `set` not called, log mentions it |
| MCP registered | `set("srv", {type:"local", command:[...]})` with `<plugin-root>` substituted |
| `$ARGUMENTS` | `expandTemplate("Review $ARGUMENTS.", "src a.ts")` is `"Review src a.ts."` |
| positional and quotes | `expandTemplate("Check $1. Focus on $2.", 'src/auth.ts "error handling"')` is `"Check src/auth.ts. Focus on error handling."` |
| last positional consumes rest | `expandTemplate("Compare $1 with $2.", "api stable branch")` is `"Compare api with stable branch."` |
| missing position is empty | `expandTemplate("A $1 B $2", "x")` is `"A x B "` |
| no placeholder appends | `expandTemplate("Explain.", "src/c.ts")` is `"Explain.\n\nsrc/c.ts"`; with empty input it is `"Explain."` |
| command execute prompts | `execute({sessionID:"s", prompt:{text:"x y"}, delivery:"d"})` calls `session.prompt` with `sessionID:"s"`, `delivery:"d"` and the expanded body |
| windows-style root | `substituteRoot("<plugin-root>/skills/a", "C:\\Users\\me\\pkg\\plugins\\a", ...)` is `"C:/Users/me/pkg/plugins/a/skills/a"` |

- [ ] **Step 2: Run, expect FAIL** (`node --test tests/opencode/loader.test.mjs`)

- [ ] **Step 3: Implement `index.js`**

Read and parse `package.json` beside the module (`fileURLToPath(import.meta.url)`), every read wrapped so a failure logs `[daodan] ...` with `console.error` and returns. Frontmatter is stripped with the same `---\n...\n---\n` split the compiler uses. `expandTemplate` follows the core's algorithm (`core/src/config/plugin/command.ts`): tokenize with `/(?:\[Image\s+\d+\]|"[^"]*"|'[^']*'|[^\s"']+)/gi`, strip one surrounding quote pair, replace `$N` by token N-1 except the highest N present which takes tokens N-1.. joined by a space, replace `$ARGUMENTS` with the trimmed input, and when neither occurs append the trimmed input after a blank line if non-empty. Each `draft.add`/`update`/`set` runs in its own `try`. Command bodies are read at `execute` time, not cached.

- [ ] **Step 4: Run, expect PASS**; then `python -m unittest tests.test_opencode_loader -v`, `python scripts/daodan_build.py`, `python scripts/daodan_build.py --check --support`

- [ ] **Step 5: Commit**

```bash
git add adapters/opencode/templates/index.js tests/opencode tests/test_opencode_loader.py exports/opencode
git commit -m "Register Daodan skills, agents, commands and MCP from the OpenCode loader"
```

### Task 6: Probe fixture for OpenCode

**Files:**
- Create: `tests/host-probes/opencode/` (package with `package.json` carrying a one-plugin `daodan` key for `probe`, `index.js` copied from the adapter template, `plugins/probe/skills/probe/SKILL.md`, `plugins/probe/agents/probe-worker.md`, `plugins/probe/commands/probe-team.md`)
- Modify: `scripts/probe_host_marketplaces.py` (`HOSTS`, `REQUIRED_FILES["opencode"]`, a manifest check that every `file` exists), `tests/host-probes/README.md` (opencode row: `commands/probe-team.md`, "agent registered by the loader, dispatched with the native `subagent` tool"; and the five probe items of spec section 10 as unmeasured rows)
- Test: `tests/test_host_probe_fixtures.py`

- [ ] **Step 1: Add the opencode case to `tests/test_host_probe_fixtures.py`** (fixture structure valid, `index.js` byte-identical to `adapters/opencode/templates/index.js`)
- [ ] **Step 2: Run, expect FAIL**
- [ ] **Step 3: Create the fixture and register it**
- [ ] **Step 4: Run** `python scripts/probe_host_marketplaces.py` and `python -m unittest tests.test_host_probe_fixtures -v`, expect PASS
- [ ] **Step 5: Commit** `git commit -m "Add an OpenCode host probe fixture"`

### Task 7: CI and publication

**Files:**
- Modify: `.github/workflows/publish-marketplaces.yml` (add `exports/opencode` to `git add`; add `actions/setup-node` before the tests if the job runs them)
- Modify: `.github/workflows/consistency.yml` (add `actions/setup-node@v4` with `node-version: "22"` before "Unit and contract tests")
- Modify: `tests/test_publish_workflow_contract.py` (assert `exports/opencode` is committed by the publication job)

- [ ] **Step 1: Write the failing contract assertion**, run `python -m unittest tests.test_publish_workflow_contract -v`, expect FAIL
- [ ] **Step 2: Edit both workflows**, rerun, expect PASS
- [ ] **Step 3: Commit** `git commit -m "Publish and test the OpenCode package in CI"`

### Task 8: Documentation and instruction parity

**Files:**
- Modify: `README.md` (OpenCode install section: the install line, the `options` selection example with one sentence on dependency closure, Desktop shares the CLI's installation, the Windows caveat, and that the loader overwrites only IDs it owns)
- Modify: `CLAUDE.md` (project structure: five hosts and `exports/opencode/package.json`; Distribution: the OpenCode paragraph; Conventions: the no-cross-kind-homonym rule with `-agent` and `-method`; every "four hosts")
- Modify: `.claude/skills/downstream-exports/SKILL.md` (opencode column in the host table, the placeholder table row, the loader and manifest, why the catalog lives under `exports/`)
- Modify: `evals/universal-daodan/catalog-parity.md`, `docs/migration-from-claude-code-daodan.md` (fifth host where hosts are enumerated)
- Regenerate: `AGENTS.md`, `.agents/skills/` via `python scripts/sync_codex_instructions.py`

- [ ] **Step 1: Edit the documents**
- [ ] **Step 2: Run** `python scripts/sync_codex_instructions.py && python scripts/sync_codex_instructions.py --check`, expect exit 0
- [ ] **Step 3: Run the full gate**

```bash
python scripts/lint_dependency_graph.py && python scripts/lint_bundled_paths.py && python scripts/lint_plugin_registration.py && python scripts/lint_fact_anchors.py && python scripts/lint_host_vocabulary.py
python -m unittest discover -s tests
python scripts/daodan_build.py --check --support
python adapters/copilot/policies/xray-guard/test_xray_guard.py
python scripts/check_version_bumps.py c79954c5 HEAD
git grep -nP "\x{2014}| -- " -- adapters/opencode docs/superpowers/plans/2026-10-02-opencode-host-adapter.md
```
Expected: every command exits 0; the support table shows `opencode` supported for every plugin; the last grep prints nothing.

- [ ] **Step 4: Commit** `git commit -m "Document the OpenCode host and resynchronize the Codex instructions"`
