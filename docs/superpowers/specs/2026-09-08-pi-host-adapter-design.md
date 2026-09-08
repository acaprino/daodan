# A fourth host: the Pi adapter

## 1. Goal

Compile every Daodan kernel into a fourth native package, `exports/pi/`, installable
into the [Pi coding agent](https://pi.dev/) with one command and no new machinery.

Pi is a minimal agent harness by Mario Zechner (Earendil Inc). It is the first host
this marketplace targets that has **no marketplace concept at all**: it installs a
*package*, from npm, from git, or from a local path, and nothing else. That single
fact drives most of what follows.

## 2. What Pi is, and the five facts that shape the port

Established from the Pi documentation (`packages/coding-agent/docs/` in
`earendil-works/pi`) and from npm, on 2026-09-08:

1. **Skills are the Agent Skills standard.** `skills/<name>/SKILL.md`, frontmatter
   `name` and `description`, freeform `references/`, `scripts/`, `assets/` beside it.
   Our skill layout already matches, near byte for byte.
2. **Workflows map onto prompt templates.** `prompts/*.md`, where the **filename is the
   command name**, frontmatter is `description` plus optional `argument-hint`, and
   `$ARGUMENTS`, `$@`, `$1` and `${1:-default}` are expanded natively. Discovery inside
   a `prompts/` directory is non-recursive.
3. **There are no subagents in the core.** The `pi-subagents` package supplies a
   `subagent` tool with parallel and forked-context workflows. Without it, a fan-out
   workflow has to run serially in the current context.
4. **There is no MCP in the core, by design.** The README points at a post arguing for
   CLI tools with READMEs instead. The gap is filled by `pi-mcp-adapter` (2.32.1, MIT,
   `nicobailon/pi-mcp-adapter`, listed in the pi.dev gallery), which reads the standard
   MCP files in precedence order: `~/.config/mcp/mcp.json`, project `.mcp.json`,
   `<pi agent dir>/mcp.json`, `.pi/mcp.json`.
5. **Installation sources are npm, git, or a local path.** Nothing else. Pi cannot
   install an archive, so a release asset could only ever be unpacked by hand into
   `~/.pi/agent/skills/`, where it is loose files: no pinned ref, no `pi update`, no
   package filtering, no `pi config`.

Two measurements taken from the kernel at marketplace 27.5.0: 40 plugins, 58 skills, 76 roles,
57 workflows, with **no name collision** in any of the three kinds. The repository
working tree is 31 MB against roughly 6.4 MB of Pi content.

## 3. Decisions taken in the brainstorm

1. **Workflows are prompt templates, prefixed with their plugin.**
   `prompts/senior-review-code-review.md`, invoked as `/senior-review-code-review`.
   Pi's command namespace is flat and global, shared with the user's own prompts and
   every other installed package. The prefix mirrors Claude's
   `/senior-review:code-review` and keeps the Daodan from claiming 57 common words
   (`/analyze`, `/audit`, `/review`, `/tidy`) in that space. Internal collisions are not
   the reason: there are none.

2. **Distribution is git only, for now.**
   `pi install git:github.com/acaprino/daodan@v<marketplace version>`. The tag already
   exists, because `publish-marketplaces.yml` writes one per marketplace version. No
   secret, no publish job, no registry, and any commit or fork can be pinned. The cost is that the clone
   carries the whole repository for 6.4 MB of usable content. The generated manifest is
   byte-identical either way, so npm publishing stays purely additive later.

3. **`peer-review` reaches Pi through `pi-mcp-adapter`, and the kernel is untouched.**
   This decision was taken twice. The first answer was to add a CLI mode to
   `server.py`, on the reasoning that Pi rejects MCP outright. Then `pi-mcp-adapter`
   turned out to exist and to read the very `.mcp.json` shape the compiler already
   renders for Claude, which makes `mcp-registration`, the strategy Codex and Copilot
   already use, both correct and honest here: the note has a real destination, a real
   file, and a real install command. A CLI mode remains a good idea and is now optional
   future work rather than the price of this port.

4. **Roles ship as skills that the model never sees listed.** This decision was also
   taken twice, and the second time by a test. The first answer was to ship them as
   unregistered files under `roles/`, as on Codex, on the reasoning that Pi puts every
   registered skill's name and description in the system prompt and 76 roles would put
   134 entries in every session. That cost is real, but Pi has a flag for exactly it:
   `disable-model-invocation: true` hides a skill from the system prompt and keeps it
   loadable by name. The parity test written for section 8 then found what the first
   answer cost: `app-analyzer` and `csp` are role-only plugins, so under it they shipped
   files and registered nothing, and two of forty plugins simply did not exist on this
   host. Roles now render as `skills/<plugin>-<role>/SKILL.md` carrying that flag. Names
   were measured against Pi's limits before choosing this: the longest is 45 characters
   against a cap of 64, and the longest description 859 against 1024.

5. **No release asset, no extractor, no packaging job.** Fact 5 above makes an archive
   strictly worse than the native path, and CLAUDE.md already records that the packaging
   apparatus retired at the universal cutover is not to be rebuilt.

## 4. The adapter: `adapters/pi/`

### 4.1 `capabilities.toml`

Pi's built-in tools are `read`, `bash`, `powershell`, `edit`, `write`, `grep`, `find`
and `ls`.

| capability | state | strategy | note |
|---|---|---|---|
| `repository.read` | native | tool `read` | |
| `repository.write` | native | tool `edit` | |
| `shell.execute` | native | tool `bash` | |
| `network.fetch` | adapted | `shell-fetch` | no network tool in the core |
| `contexts.isolate` | adapted | `runtime-subagent` | package `pi-subagents` |
| `roles.dispatch` | adapted | `inline-prompt` | no named agents |
| `execution.parallel` | adapted | `concurrent-dispatch` | package `pi-subagents` |
| `tasks.share` | unsupported | none | |
| `peers.message` | unsupported | none | |
| `hooks.lifecycle` | unsupported | none | Pi exposes lifecycle events to TypeScript extensions, a mechanism no probe has measured |
| `mcp.servers` | adapted | `mcp-registration` | package `pi-mcp-adapter` |

`hooks.lifecycle` is required by no plugin, so `unsupported` blocks nothing and is the
only honest state until the extension mechanism is probed.

Three bindings carry the name of the companion package that satisfies them in a new
`package` field, so the install line a template renders is derived from the adapter
rather than written into the template text. It is deliberately not `value`: that field
names a host tool and feeds the Copilot coordinator's derived `tools` line, so a package
name there would read as a tool that does not exist. The day a companion is renamed, one file changes instead of 57
generated prompts. It is the same mechanism that already derives the Copilot
coordinator's `tools` line from the bindings.

### 4.2 `coordination.toml`

Two strategies, mirroring Codex, both `isolated = true` and
`role_delivery = "inline-prompt"`: `parallel-subagents` then `serial-isolated`. Both
carry `availability = "runtime-optional"`, because on Pi isolation comes from
`pi-subagents` rather than from the core.

### 4.3 `layout.toml`

```toml
[layout]
root = "exports/pi"
marketplace = "package.json"
plugin_root = "plugins/${plugin}"
skills = "skills/${skill}/SKILL.md"
roles = "skills/${plugin}-${role}/SKILL.md"
role_template = "role.SKILL.md.tmpl"
workflows = "prompts/${plugin}-${workflow}.md"
team_workflow_template = "team-prompt.md.tmpl"

plugin_root_reference = "<plugin-root>"
plugin_root_note = "`<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it."
arguments_reference = "$ARGUMENTS"
workflow_frontmatter = "description, argument-hint"
```

Three things are load-bearing. `plugin_manifest` is **absent**, because Pi has no
per-plugin manifest. `arguments_reference` maps onto itself and carries no note, which
only Claude does today, because Pi expands `$ARGUMENTS` natively. And
`workflow_frontmatter` omits `name` on purpose: on Pi the command name is the filename.

### 4.4 `templates/`

One template, `team-prompt.md.tmpl`, bound to `team_workflow_template`. It carries the
generated dispatch plan like the other three hosts, plus the clause specific to Pi: use
the `subagent` tool supplied by `pi-subagents`.

What happens when that tool is missing has **two branches**, and collapsing them into
one would be a defect. A workflow that requires isolation, which is every review
pipeline declaring the `reviewers-use-isolated-contexts` outcome, stops and tells the
user to run `pi install npm:pi-subagents`. Running its phases serially in one context
*is* the loss of isolation, so announcing it in the report would degrade a declared
contract quietly, which is exactly what this repository's dependency policy forbids. A
workflow that merely prefers concurrency may run serially and say so.

There is no `role_template`, because role bodies ship unrewritten.

## 5. The package

```
exports/pi/plugins/senior-review/
├── skills/review-quality-gates/SKILL.md              # the plugin's own skill
├── skills/senior-review-security-auditor/SKILL.md    # a role, hidden from the skill list
└── prompts/senior-review-code-review.md              # /senior-review-code-review
```

## 6. The root `package.json`, which is Pi's catalog

`pi install git:` reads the manifest from the root of the clone, so the Pi catalog is a
generated `package.json` at the repository root:

```json
{
  "name": "daodan",
  "version": "28.0.0",
  "private": true,
  "license": "MIT",
  "keywords": ["pi-package"],
  "pi": {
    "skills": ["./exports/pi/plugins/*/skills"],
    "prompts": ["./exports/pi/plugins/*/prompts"]
  }
}
```

Directory globs, not file globs: Pi recurses into a skills directory looking for
`SKILL.md` and reads a prompts directory non-recursively, which is exactly the shape
rendered above. `version` comes from `metadata.version`, so all four hosts stay on one
number. `private: true` states the git-only decision in the artifact and is the switch
to flip the day npm is added.

Cross-host identity is untouched: `catalog_document()` keeps producing the neutral
document for every host and `assert_cross_host_identity` keeps reading it. Only the
**serialization** differs, emitting the `package.json` shape for Pi instead of a
`plugins` array.

A consequence to accept: with a `package.json` at the root, `pi install git:` runs
`npm install` on the clone. It has no dependencies, so the install is a no-op, but npm
has to be on the machine.

## 7. Compiler changes

1. `plugin_manifest` becomes optional in the layout. `render_plugin` indexes the key
   directly today and would raise for Pi.
2. `render_catalog` becomes host-aware in serialization only.
3. `HOSTS` gains `"pi"`, and the partial-publication refusal names four hosts.

The hard-coded Copilot tool map is not touched: without a `role_template`, Pi never
reaches it.

## 8. CI, tests, probe

- `tests/host-probes/pi/`, packaging the same `daodan-probe` fixture as the other three,
  registered in `scripts/probe_host_marketplaces.py`.
- Pi assertions in `tests/test_daodan_host_rendering.py`: the prompt filename prefix,
  `$ARGUMENTS` left intact, the `<plugin-root>` marker with its note, and the MCP note
  naming `pi-mcp-adapter` and the config file to paste into.
- `scripts/lint_plugin_registration.py` gains a Pi mode. Pi's catalog does not enumerate
  components, it globs them, so the rule inverts: every generated component must fall
  inside a declared glob.
- `publish-marketplaces.yml` adds the root `package.json` to the committed paths.
- The roughly ten test files that name three hosts are updated to four.

## 9. Repository obligations

- README: an install section for Pi that names the one install command, **both companion
  packages with what each one unlocks and what stops working without it**
  (`pi-subagents` for every workflow that fans out, `pi-mcp-adapter` for `peer-review`),
  and a settings example showing per-plugin selection through the object form of
  `packages`. `pi-subagents` is still 0.x, so the text names the package and never the
  signature of its tools.
- `.claude/skills/downstream-exports/SKILL.md`: a Pi column in the host table, the Pi
  row in the placeholder table, and the note that Pi has no per-plugin manifest.
- `CLAUDE.md`: the Distribution section, the compiler description, and every place that
  says three hosts.
- `AGENTS.md` and `.agents/skills/` regenerated with `scripts/sync_codex_instructions.py`,
  whose `--check` is a parity gate.

## 10. Out of scope

No release asset, no extractor, no packaging job, no npm publication, no CLI mode on
`server.py`, no override, and no hand-written file under `exports/pi/`.

## 11. What the probe must confirm

That the directory globs in the manifest resolve nested skills as expected, that a
prompt template installed from a package keeps its filename as the command name, and
that `pi-subagents` and `pi-mcp-adapter` behave as documented when a plugin ships the
files rather than the user hand-writing them. Every capability state in section 4.1 is
provisional until that evidence is recorded, which is the standing rule for
`adapters/*/capabilities.toml` in this repository.
