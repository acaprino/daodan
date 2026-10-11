<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Architecture Patterns

Game-level structure, Screen management, Scene2D for UI, Ashley ECS for entities, Box2D physics, and 3D basics.

## ApplicationListener and Game

The entry point implements `ApplicationListener` (6 callbacks: create, resize, render, pause, resume, dispose). For most projects, extend `Game` instead of implementing ApplicationListener directly. `Game` adds a Screen abstraction and delegates lifecycle callbacks to the current Screen.

```java
public class MyGame extends Game {
    public SpriteBatch batch;
    public AssetManager assets;
    public Skin skin;

    @Override
    public void create() {
        batch = new SpriteBatch();
        assets = new AssetManager();
        setScreen(new LoadingScreen(this));
    }

    @Override
    public void dispose() {
        if (getScreen() != null) getScreen().dispose();
        batch.dispose();
        assets.dispose();
        if (skin != null) skin.dispose();
    }
}
```

## Screen Pattern

Each major game state is a `Screen`: MainMenuScreen, GameplayScreen, PauseScreen, GameOverScreen, OptionsScreen. The `Screen` interface has show, render, resize, pause, resume, hide, dispose.

### Switching Screens
`Game.setScreen(newScreen)` calls the new screen's `show()` and the previous screen's `hide()`. It does NOT dispose the previous screen automatically.

Two strategies:

**A. Keep all screens alive, switch with no disposal**
```java
public class MyGame extends Game {
    public MainMenuScreen menu;
    public GameplayScreen gameplay;

    @Override
    public void create() {
        menu = new MainMenuScreen(this);
        gameplay = new GameplayScreen(this);
        setScreen(menu);
    }

    @Override
    public void dispose() {
        menu.dispose();
        gameplay.dispose();
    }
}
```
Best for screens with heavy assets you want to keep loaded.

**B. Dispose old screen when switching permanently**
```java
public void switchTo(Screen newScreen) {
    Screen old = getScreen();
    setScreen(newScreen);
    if (old != null) old.dispose();
}
```
Best for one-way transitions (menu -> game -> game over -> back to menu).

### Screen Lifecycle Rules
1. Construct screens lazily if they hold heavy assets
2. Reuse screen instances rather than constructing new ones on every transition (construction reallocates GPU resources)
3. Set `Gdx.input.setInputProcessor(...)` in `show()`, NOT in the constructor; constructor runs before the screen is visible
4. Null the input processor in `hide()` to avoid stale handlers
5. Call `viewport.update(width, height, true)` in `resize()`
6. Dispose all owned resources in `dispose()`

### Transition Library
For animated screen transitions, the canonical community library is `crykn/libgdx-screenmanager`. It handles input processor switching, transition effects (fade, slide, blinds), and resource lifecycle.

## Scene2D

UI framework: a scene graph of `Actor`s rooted at a `Stage`. The Stage owns a `Viewport`, a `Batch`, and handles input routing.

### Core Hierarchy
```
Stage
  Group (e.g. root Table)
    Table
      Label
      TextButton
      Image
      ScrollPane
        Table (inner)
          ...
```

### Tables for Layout
`Table` is the most common layout container. Cells with row()-based positioning:
```java
Table table = new Table();
table.setFillParent(true);
stage.addActor(table);

table.add(new Label("Score:", skin)).left().pad(10);
table.add(new Label("0", skin)).expandX().right().pad(10);
table.row();
table.add(playButton).colspan(2).fillX().pad(20);
```

### Skin
A `Skin` is a bundle of resources (textures, fonts, drawables, colors) plus a JSON style definition. Generate with Skin Composer (https://github.com/raeleus/skin-composer).

### Input Routing
`Stage` implements `InputProcessor`. Hand it to `Gdx.input` (often via an `InputMultiplexer` if you also have gameplay input):
```java
InputMultiplexer mux = new InputMultiplexer();
mux.addProcessor(stage);          // UI first
mux.addProcessor(gameInputHandler); // gameplay second
Gdx.input.setInputProcessor(mux);
```
The Stage will consume events it handles (button clicks), gameplay handler sees only events the Stage rejected.

### Actor Update vs Draw
- `Actor.act(float delta)` is called once per frame to update state, run actions, fire events
- `Actor.draw(Batch, parentAlpha)` draws to the Stage's Batch
- Stage handles both: `stage.act(delta); stage.draw();`

## Ashley ECS

Entity-Component-System framework that pairs naturally with libGDX. Game-world entities live as Ashley `Entity`s; logic lives in `EntitySystem`s.

### Core Concepts
- **Entity**: a unique ID + a bag of components
- **Component**: pure data (position, velocity, sprite, health)
- **System**: logic that operates on entities matching a Family

### Example
```java
public class Position implements Component {
    public float x, y;
}

public class Velocity implements Component {
    public float dx, dy;
}

public class MovementSystem extends IteratingSystem {
    private final ComponentMapper<Position> pm = ComponentMapper.getFor(Position.class);
    private final ComponentMapper<Velocity> vm = ComponentMapper.getFor(Velocity.class);

    public MovementSystem() {
        super(Family.all(Position.class, Velocity.class).get());
    }

    @Override
    protected void processEntity(Entity entity, float delta) {
        Position p = pm.get(entity);
        Velocity v = vm.get(entity);
        p.x += v.dx * delta;
        p.y += v.dy * delta;
    }
}
```

### Engine Setup
```java
Engine engine = new Engine();
engine.addSystem(new MovementSystem());
engine.addSystem(new RenderSystem(batch, camera));

Entity player = engine.createEntity();
player.add(new Position()).add(new Velocity());
engine.addEntity(player);

// Each frame:
engine.update(delta);
```

### Pitfalls
- **Cache ComponentMappers**: `ComponentMapper.getFor(...)` is moderately expensive. Cache as `private final` fields, never call per-frame
- **Components with collections must clear in `reset()`**: when implementing `Poolable`, clear arrays/maps in `reset()`. Otherwise pooled components retain dangling references and leak memory
- **Order systems by priority**: `engine.addSystem(system, priority)`. Lower priority runs first. Typical order: input -> physics -> movement -> collision -> rendering
- **Family changes are expensive**: adding/removing components from an entity recomputes Family membership. Avoid in hot paths

### Scene2D + Ashley Combination
Standard community pattern:
- Scene2D handles UI rendering, input routing, hit detection, layout
- Ashley handles game-world entities and logic

Do not try to use Ashley for UI (no built-in input or hit testing) and do not use Scene2D for game entities (poor scaling for hundreds of game objects). Both have legitimate roles.

## Box2D Physics

2D rigid-body physics simulation, ported from Erin Catto's C++ Box2D. Included as a libGDX extension.

### Core Concepts
- **World**: container, gravity, simulation
- **Body**: rigid body, position + velocity + mass
- **Fixture**: shape attached to body (circle, polygon, edge)
- **Joint**: constraint between bodies

### Fixed Timestep
Box2D simulation MUST run at a fixed timestep, decoupled from render rate. Variable timestep produces unstable simulation.

```java
private static final float STEP = 1f / 60f;
private float accumulator = 0f;

public void update(float delta) {
    accumulator += Math.min(delta, 0.25f);  // cap to avoid spiral of death
    while (accumulator >= STEP) {
        world.step(STEP, 6, 2);  // 6 velocity iterations, 2 position iterations
        accumulator -= STEP;
    }
}
```

### Units
- Box2D works best with units that approximate meters (0.1 to 10 range)
- libGDX uses pixels by default; convert with a scale constant
- Convention: `PPM = 100` (pixels per meter), divide pixel coords by PPM when passing to Box2D

### Performance
- Sleeping bodies: Box2D auto-sleeps inactive bodies; do not disable
- Contact listeners: implement `ContactListener` for collision callbacks; do NOT modify the world inside callbacks (queue changes)
- DebugRenderer: `Box2DDebugRenderer` overlays shapes; useful during dev, disable in production

## 3D Basics

libGDX has a 3D rendering API though less mature than 2D. Used for 3D games or 2.5D effects.

### Core Classes
- **Model**: shared mesh + materials, expensive
- **ModelInstance**: cheap reference to a Model with its own transform
- **ModelBatch**: 3D analog of SpriteBatch
- **Environment**: lighting setup
- **PerspectiveCamera**: standard 3D camera

### Minimal Setup
```java
camera = new PerspectiveCamera(67, viewport.getWorldWidth(), viewport.getWorldHeight());
camera.position.set(10, 10, 10);
camera.lookAt(0, 0, 0);
camera.near = 1f;
camera.far = 300f;

environment = new Environment();
environment.set(new ColorAttribute(ColorAttribute.AmbientLight, 0.4f, 0.4f, 0.4f, 1f));
environment.add(new DirectionalLight().set(0.8f, 0.8f, 0.8f, -1f, -0.8f, -0.2f));

modelBatch = new ModelBatch();

// per frame
modelBatch.begin(camera);
modelBatch.render(instance, environment);
modelBatch.end();
```

### Model Loading
- G3DJ format: libGDX's native JSON 3D format (fbx-conv to convert from FBX/Collada/OBJ)
- GLTF: third-party library `gdx-gltf` (https://github.com/mgsx-dev/gdx-gltf) is the modern choice
- OBJ: loadable but typically lacks animations

### 3D Physics
Bullet bindings come with libGDX (`gdx-bullet`). For most indie 3D games, Bullet via libGDX is the path of least resistance.

## Source References

- https://libgdx.com/wiki/scene2d/scene2d
- https://libgdx.com/wiki/scene2d/scene2d-ui
- https://libgdx.com/wiki/extensions/ashley
- https://libgdx.com/wiki/extensions/physics/box2d
- https://libgdx.com/wiki/graphics/3d/3d-graphics
- https://github.com/libgdx/ashley/wiki
- https://github.com/crykn/libgdx-screenmanager
