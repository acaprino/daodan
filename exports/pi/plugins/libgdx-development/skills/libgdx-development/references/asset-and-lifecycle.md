<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# Assets and Lifecycle

AssetManager async loading, disposal discipline, Screen lifecycle, input processor management.

## AssetManager

`AssetManager` is libGDX's central asset loader. It handles async loading on a worker thread, dependency resolution (a Skin depending on a TextureAtlas), reference counting, and unloading.

### Basic Workflow
```java
AssetManager assets = new AssetManager();

// Queue loads (returns immediately)
assets.load("atlas/game.atlas", TextureAtlas.class);
assets.load("ui/skin.json", Skin.class);
assets.load("audio/music.ogg", Music.class);
assets.load("audio/jump.wav", Sound.class);

// In your render loop, pump:
if (assets.update()) {
    // All queued loads complete
    TextureAtlas atlas = assets.get("atlas/game.atlas", TextureAtlas.class);
    Skin skin = assets.get("ui/skin.json", Skin.class);
}
```

### update() return value
`update()` returns true when ALL queued assets are loaded. Returns false otherwise. Use `getProgress()` (0..1) for progress bars.

### Pumping in a Loading Screen
The default `update()` once per frame is too slow for snappy loading; the AssetManager async worker is rate-limited by the call frequency. On a dedicated loading screen, pump multiple times per frame:
```java
@Override
public void render(float delta) {
    ScreenUtils.clear(0, 0, 0, 1);
    for (int i = 0; i < 4 && !assets.update(); i++) {
        // Pump up to 4 times per frame
    }
    progressBar.setValue(assets.getProgress());
    if (assets.isFinished()) game.setScreen(new GameplayScreen(game));
}
```

### Custom Loaders
For custom asset types (e.g. binary level files), implement `AsynchronousAssetLoader<MyType, MyParameter>`. Register with `assets.setLoader(MyType.class, new MyLoader(...))`.

### Reference Counting
Each `load()` increments a refcount. `unload()` decrements. When refcount hits zero, the asset is disposed. This lets multiple screens share assets cleanly:
```java
// MainMenu calls
assets.load("atlas/ui.atlas", TextureAtlas.class);

// Gameplay also loads
assets.load("atlas/ui.atlas", TextureAtlas.class);  // refcount = 2

// MainMenu hide()
assets.unload("atlas/ui.atlas");  // refcount = 1, NOT disposed

// Gameplay dispose()
assets.unload("atlas/ui.atlas");  // refcount = 0, disposed
```

### finishLoadingAsset() pitfall
`finishLoadingAsset(path)` blocks until the named asset is loaded. Convenient for early-game critical assets, BUT combined with `AbsoluteFileHandleResolver` it can deadlock (see libgdx#4888). Prefer pumping `update()` in a loading screen over blocking.

## Disposal Discipline

OpenGL resources are NOT garbage-collected. Every Texture, Sound, Music, Skin, BitmapFont, ShaderProgram, FrameBuffer, Stage you create must be explicitly disposed.

### Ownership Rules
- If you `new`'d it, you dispose it
- If `AssetManager` loaded it, AssetManager owns it. Call `unload(path)` or `dispose()` on the manager, NEVER call `dispose()` on the asset directly
- If a parent owns it (e.g. `Stage` owns its `Batch` if you used the no-arg constructor), the parent disposes it
- `TextureAtlas.dispose()` disposes all contained textures
- `Skin.dispose()` disposes its TextureAtlas and BitmapFonts

### Common Leak Sources
1. Forgetting to dispose a `Skin` constructed with `new Skin(Gdx.files.internal("..."))` instead of using AssetManager
2. Creating `new Texture(...)` per frame or per entity instead of using an atlas
3. Re-creating `FrameBuffer` on resize without disposing the old one
4. Re-creating `BitmapFont` via `FreeTypeFontGenerator` without disposing the previous generation
5. Holding a static field reference (also causes Android-lifecycle bugs)

### Static Fields Are Forbidden
NEVER make AssetManager, Texture, Sound, Skin, or any OpenGL resource a `static` field:
```java
// WRONG
public class Assets {
    public static AssetManager assets = new AssetManager();  // BREAKS on Android
}
```
Why: Android may kill the rendering context (`pause`) while the JVM stays alive. The static reference persists into the next session, but the underlying GPU resource has been destroyed. Symptom: black/missing textures after resume.

Correct: hold AssetManager as an instance field of `Game`, or pass it via constructor into Screens.

### Dispose Checklist for a Screen
```java
public class GameplayScreen extends ScreenAdapter {
    private Stage stage;
    private FrameBuffer fbo;
    private ShaderProgram blurShader;
    private ParticleEffect explosion;

    @Override
    public void dispose() {
        stage.dispose();
        fbo.dispose();
        blurShader.dispose();
        explosion.dispose();
        // Do NOT dispose Skin, atlases, music here if loaded via AssetManager;
        // those are managed centrally
    }
}
```

## Screen Lifecycle

`Screen` interface methods, called by `Game`:

| Method | When |
|--------|------|
| `show()` | Screen becomes active. Set input processor, start music |
| `render(delta)` | Each frame |
| `resize(w, h)` | Window/screen resized. Update viewport |
| `pause()` | App lost focus (Android background, desktop alt-tab) |
| `resume()` | App regained focus |
| `hide()` | Screen swapped out. Null input processor, stop music |
| `dispose()` | Screen destroyed permanently. Free resources |

### Input Processor Pattern
ALWAYS set input processor in `show()` (not constructor):
```java
@Override
public void show() {
    InputMultiplexer mux = new InputMultiplexer();
    mux.addProcessor(stage);
    mux.addProcessor(gameplayInput);
    Gdx.input.setInputProcessor(mux);
}

@Override
public void hide() {
    Gdx.input.setInputProcessor(null);
}
```
Setting in constructor: input processor is set before the screen is visible, which can intercept clicks on the previous screen during transition animations.

### Resize Pattern
```java
@Override
public void resize(int width, int height) {
    viewport.update(width, height, true);  // true = center camera
    stage.getViewport().update(width, height, true);
}
```

### Pause/Resume on Android
On Android, the rendering context can be destroyed during pause and recreated on resume. libGDX handles most of this transparently if you use AssetManager, but:
- Sounds and Music may need to be restarted manually
- Custom shaders may need to be recompiled (libGDX handles this for `ShaderProgram` if you use it standard)
- Custom OpenGL state (uniform values not re-applied each frame) may need to be re-set

## Tiled Map Integration

`.tmx` files from the Tiled Map Editor (https://www.mapeditor.org/) are natively supported.

### Loading
```java
TmxMapLoader loader = new TmxMapLoader();
TiledMap map = loader.load("maps/level01.tmx");
OrthogonalTiledMapRenderer renderer = new OrthogonalTiledMapRenderer(map);

// In render:
renderer.setView(camera);
renderer.render();
```

For better packing, use `AtlasTmxMapLoader` with a pre-packed atlas:
```java
AtlasTmxMapLoader loader = new AtlasTmxMapLoader();
TiledMap map = loader.load("maps/level01.tmx", params);
```

### libGDX 1.14.0 Tiled Changes
- `TmxMapLoader` and `AtlasTmxMapLoader` share a unified base
- Class objects supported (Tiled's typed object system)
- Template objects supported

### Object Layers
Tiled object layers map to `MapObject` instances. Iterate to spawn entities:
```java
MapLayer objects = map.getLayers().get("objects");
for (MapObject obj : objects.getObjects()) {
    if (obj.getProperties().get("type", String.class).equals("spawn")) {
        float x = obj.getProperties().get("x", Float.class);
        float y = obj.getProperties().get("y", Float.class);
        spawnPlayer(x, y);
    }
}
```

## Audio Lifecycle

- **Sound**: small, fully decoded, played multiple times. Use for SFX (< 1 second)
- **Music**: streamed, played once at a time per instance. Use for background music

### Common Patterns
```java
Sound jump = assets.get("audio/jump.wav", Sound.class);
long id = jump.play(0.7f);  // volume; returns instance ID

Music bgm = assets.get("audio/level1.ogg", Music.class);
bgm.setLooping(true);
bgm.setVolume(0.5f);
bgm.play();
```

### Audio on Android
- OGG Vorbis is the safest format across all platforms
- WAV works but is large
- MP3 has licensing concerns and partial Android support
- iOS prefers M4A; libGDX can handle but watch encoding

### Stopping Audio on hide()
```java
@Override
public void hide() {
    bgm.stop();
}

@Override
public void dispose() {
    // Music is managed by AssetManager, do not dispose here
}
```

## Save/Load State

libGDX provides `Preferences` for small key-value storage (cross-platform):
```java
Preferences prefs = Gdx.app.getPreferences("MyGameSave");
prefs.putInteger("highScore", score);
prefs.flush();

int score = prefs.getInteger("highScore", 0);
```

For larger save files, use the `Json` class with serializable objects:
```java
Json json = new Json();
String save = json.toJson(saveState);
Gdx.files.local("save.json").writeString(save, false);

SaveState loaded = json.fromJson(SaveState.class, Gdx.files.local("save.json"));
```
Note: In libGDX 1.14.0, `JsonValue#get(String)` is case-sensitive. Audit any save files with mixed-case keys.

## Source References

- https://libgdx.com/wiki/managing-your-assets
- https://libgdx.com/wiki/file-handling
- https://libgdx.com/wiki/audio
- https://libgdx.com/wiki/preferences
- https://libgdx.com/wiki/graphics/2d/tile-maps
- https://github.com/libgdx/libgdx/issues/6642 (static AssetManager pitfall)
- https://github.com/libgdx/libgdx/issues/4888 (finishLoadingAsset deadlock)
