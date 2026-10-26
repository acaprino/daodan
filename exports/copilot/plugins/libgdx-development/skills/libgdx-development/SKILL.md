---
name: libgdx-development
description: >
  Knowledge base for shipping production games from one Java or Kotlin codebase.
  TRIGGER WHEN: building, optimizing, debugging, or scaffolding libGDX games; migrating libGDX
  versions; choosing libGDX architecture patterns.
---

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# libGDX Cross-Platform Game Development

Knowledge base for building production-grade games with libGDX, the cross-platform Java/Kotlin game framework.

## When to Use

- Scaffolding a new libGDX project with gdx-liftoff
- Designing the Game/Screen structure and Scene2D + Ashley + Box2D integration
- Managing the rendering pipeline: SpriteBatch, TextureAtlas, viewports, cameras
- Handling AssetManager lifecycle and OpenGL resource disposal
- Targeting Desktop, Android, iOS, or HTML5 from a shared codebase
- Migrating to libGDX 1.14.0 and its breaking changes (`Pools` -> `PoolManager`, `JsonValue` case sensitivity)
- Debugging frame-rate drops, VRAM leaks, or input handling bugs

## Quick Start

For 80% of new libGDX projects, follow this path:

1. **Generate**: download latest `gdx-liftoff` JAR from https://github.com/libgdx/gdx-liftoff/releases, run with JDK 17 or later (Java 21 recommended)
2. **Configure** in gdx-liftoff: pick platforms (Desktop + Android typical), pick language (Kotlin if no HTML5 target, otherwise Java), pick extensions (Ashley, Box2D, FreeType, Controllers as needed)
3. **Open** the generated project in IntelliJ IDEA or Android Studio (do NOT use Eclipse for modern libGDX)
4. **Run** `:lwjgl3:run` Gradle task to launch the desktop module
5. **Architecture**: extend `Game`, create `MainMenuScreen` + `GameplayScreen`, use Scene2D for UI and Ashley for entities
6. **Assets**: pack sprites into `TextureAtlas` (2048x2048 POT), load via `AssetManager`, never load loose Textures per sprite
7. **Disposal**: every Texture, Sound, Music, Stage, Skin, BitmapFont, ShaderProgram MUST have an explicit `.dispose()` call

Then harden incrementally:
- GL thread blocking, push IO/compute to a worker thread via `Gdx.app.postRunnable`
- Screen lifecycle, set `Gdx.input.setInputProcessor` in `show()`, never in the constructor
- Memory leaks, audit static field references to Texture/AssetManager (forbidden on Android)
- Scene2D performance, set `Group.isTransform = false` on non-rotating Groups
- Ashley correctness, components with collections must implement `Poolable` and clear in `reset()`

## Reference Materials

- `references/setup-and-tooling.md`: gdx-liftoff workflow, Gradle multi-module layout, JDK and Kotlin versions, IDE setup, libGDX 1.14.0 changelog
- `references/rendering-and-performance.md`: SpriteBatch batching, TextureAtlas packing, viewports, GL thread rules, frame-budget profiling, vsync ceiling
- `references/architecture-patterns.md`: Game + Screen pattern, Scene2D + Ashley ECS combination, Box2D fixed timestep, 3D ModelBatch basics
- `references/asset-and-lifecycle.md`: AssetManager async loading, dispose discipline, Screen lifecycle, input processor management, screen transitions
- `references/deployment-platforms.md`: Desktop LWJGL3, Android (minSdk/targetSdk), iOS RoboVM constraints, HTML5 GWT vs TeaVM, packaging and signing

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Generator | gdx-liftoff | Always (gdx-setup is deprecated) |
| Language | Kotlin (Java if HTML5 needed) | HTML5 target requires Java |
| JDK build target | Java 21 | Java 17 minimum; iOS source level capped at 8 |
| Architecture | Game + Screen + Scene2D | Add Ashley ECS for mid-size entity counts |
| Physics | Box2D fixed timestep (60 Hz) | Bullet for 3D |
| Asset loading | AssetManager async, pump update() per frame | Multiple update() per frame on loading screen |
| Texture strategy | TextureAtlas, POT, packed via TexturePacker | Never load loose Textures per sprite |
| Screen transitions | Reuse Screen instances or libgdx-screenmanager | Constructing new screens per transition is wasteful |
| Input handling | Set processor in show(), null in hide() | InputMultiplexer for Stage + custom processors |
| HTML5 backend | GWT | TeaVM if you need Kotlin or modern JS interop (still WIP for libGDX) |

## Behavioral Rules

- Never share Texture or AssetManager via static fields (Android lifecycle breaks them)
- Never call OpenGL or `Gdx.gl.*` from a non-render thread
- Never load loose Textures per sprite, always pack atlases
- Always dispose every OpenGL-backed resource on Screen.dispose() or Game.dispose()
- Always set `Gdx.input.setInputProcessor` in Screen.show(), null it in Screen.hide()
- Always set `Group.isTransform = false` on Scene2D Groups without rotation or scaling
- Always cache `ComponentMapper.getFor(...)` references in Ashley systems
- Always use a fixed timestep for Box2D, decoupled from render rate

## Source Anchors

- libgdx.com (canonical wiki and news)
- javadoc.io/doc/com.badlogicgames.gdx/gdx/latest (canonical API)
- github.com/libgdx/libgdx (source)
- github.com/libgdx/gdx-liftoff (project generator)
