<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# Rendering and Performance

The libGDX rendering pipeline, batching, viewports, frame-budget profiling, and the most common performance pitfalls.

## The Render Loop

`ApplicationListener.render()` is called once per frame on the render thread. `Gdx.graphics.getDeltaTime()` gives elapsed seconds since the last frame.

Frame-time budgets:
- 60 fps: 16.6 ms per frame
- 120 fps: 8.3 ms per frame
- VR / mobile high-refresh: 8.3-11 ms

Anything that exceeds this budget drops the frame rate. On Android, blocking the render thread for too long triggers an ANR (Application Not Responding) dialog.

## Core Rule: Never Block the GL Thread

The render thread is the ONLY thread allowed to call `Gdx.gl.*` or touch OpenGL-backed resources (Texture, Mesh, ShaderProgram, FrameBuffer).

Forbidden on the render thread:
- File IO that isn't going through `AssetManager` async loading
- Network requests
- Heavy CPU work (pathfinding over large grids, decompression, JSON parsing of large blobs)
- Thread.sleep, blocking semaphore acquisitions

Correct pattern: run heavy work on a worker thread and push results back:
```java
new Thread(() -> {
    String json = httpClient.get("https://api.example.com/leaderboard").body();
    Gdx.app.postRunnable(() -> {
        leaderboard.update(parseJson(json));
    });
}).start();
```
`Gdx.app.postRunnable` queues a Runnable to execute on the next render frame.

## SpriteBatch

`SpriteBatch` is the workhorse for 2D rendering. It batches draw calls that share the same Texture, flushing to the GPU when:
- `end()` is called
- A different Texture is bound
- The internal vertex buffer fills (default 1000 sprites per batch)
- A different blend mode is set
- A different shader is set

Cost of a flush: one OpenGL draw call. The dominant performance variable for 2D libGDX games is the number of flushes per frame.

### Reducing flushes
1. Pack sprites into one (or few) atlases so most sprites share a texture
2. Order draw calls by texture, not by entity:
   - All backgrounds (texture A) first
   - All enemies (texture B) next
   - All UI (texture C) last
3. Use `TextureRegion` from a single `TextureAtlas` to draw multiple sprites without binding
4. Pre-multiplied alpha or premultiplied PNGs can avoid some blend-mode changes

### SpriteBatch boilerplate
```java
batch.begin();
batch.draw(region, x, y, width, height);
batch.end();
```
Always pair `begin()`/`end()`. Inside the begin/end pair, do NOT call other rendering operations (no ShapeRenderer, no Stage.draw on a different batch).

## TextureAtlas and TexturePacker

A `TextureAtlas` is a single large texture (typically 2048x2048, power-of-two) containing many smaller sprite regions, plus a `.atlas` file describing UV coordinates.

### Why POT and 2048
- Older Android GPUs require POT textures
- 2048x2048 fits within virtually every device's maxTextureSize
- Larger atlases save flushes; smaller atlases waste VRAM

### Packing workflow
1. Drop loose PNGs into a folder (e.g. `assets-raw/`)
2. Run TexturePacker:
   ```bash
   java -cp gdx.jar:gdx-tools.jar com.badlogic.gdx.tools.texturepacker.TexturePacker \
     assets-raw/ android/assets/atlas/ game
   ```
   Produces `android/assets/atlas/game.atlas` plus `game.png` (or `game1.png`, `game2.png` if it splits)
3. In code:
   ```java
   TextureAtlas atlas = assets.get("atlas/game.atlas", TextureAtlas.class);
   TextureRegion player = atlas.findRegion("player");
   ```

### TexturePacker settings (`pack.json` next to source folder)
- `pot: true` (force power-of-two)
- `maxWidth: 2048, maxHeight: 2048`
- `paddingX: 2, paddingY: 2` (prevents bleed between regions)
- `duplicatePadding: true` (clamps edge pixels)
- `filterMin: Linear, filterMag: Linear` (smooth scaling)
- `useIndexes: false` for static sprites; `true` for animations

## Cameras and Viewports

A `Camera` defines the view frustum; a `Viewport` adapts the camera to screen size.

| Viewport | Behavior |
|----------|----------|
| `FitViewport` | Keeps aspect ratio, black bars on mismatched screens |
| `FillViewport` | Keeps aspect ratio, crops overflow |
| `StretchViewport` | Stretches to screen, distorts aspect |
| `ScreenViewport` | 1 unit = 1 pixel, no aspect handling |
| `ExtendViewport` | Keeps aspect ratio, extends in one dimension |

Standard pattern for 2D games:
```java
camera = new OrthographicCamera();
viewport = new FitViewport(1280, 720, camera);

@Override
public void resize(int width, int height) {
    viewport.update(width, height, true);  // true centers the camera
}
```

Always call `viewport.apply()` and `camera.update()` before rendering, and apply `batch.setProjectionMatrix(camera.combined)` once per begin/end pair.

## Profiling

### GLProfiler
Built-in OpenGL call profiler:
```java
GLProfiler profiler = new GLProfiler(Gdx.graphics);
profiler.enable();
// ... render frame ...
Gdx.app.log("GL", "calls=" + profiler.getCalls()
                + " drawCalls=" + profiler.getDrawCalls()
                + " textureBindings=" + profiler.getTextureBindings()
                + " shaderSwitches=" + profiler.getShaderSwitches());
profiler.reset();
```
Watch for drawCalls and textureBindings. Per frame, target:
- < 50 draw calls for mobile
- < 200 for desktop
- Texture bindings should be at most a handful per frame

### Frame-time logging
```java
@Override
public void render() {
    long start = System.nanoTime();
    // ... render ...
    long elapsedMs = (System.nanoTime() - start) / 1_000_000;
    if (elapsedMs > 16) Gdx.app.log("frame", "slow: " + elapsedMs + "ms");
}
```

### Profiler stop signal
When `glClear` dominates the profiler output (Android Studio Profiler, JProfiler, JVisualVM, or Renderdoc), you have hit the vsync ceiling. The GPU is idling between frames waiting for the next vblank. Code-level optimization beyond this point will NOT increase frame rate. To squeeze more, you would need to disable vsync or target a higher refresh rate.

## Memory Management

OpenGL resources do NOT participate in the JVM garbage collector. Every Texture, Sound, Music, ShaderProgram, Stage, Skin, BitmapFont, ParticleEffect, FrameBuffer, ModelInstance you create allocates GPU/native memory that the JVM cannot reclaim.

### Disposal checklist
| Resource | Disposed by |
|----------|-------------|
| Texture | Texture.dispose() |
| TextureAtlas | Atlas.dispose() (disposes contained Textures) |
| Pixmap | Pixmap.dispose() |
| BitmapFont | Font.dispose() (if you generated it; do NOT dispose if it came from Skin) |
| Sound | Sound.dispose() |
| Music | Music.dispose() |
| ShaderProgram | Program.dispose() |
| Stage | Stage.dispose() (disposes its Skin if owned, but be careful with shared Skin) |
| Skin | Skin.dispose() once at end of life |
| FrameBuffer | FrameBuffer.dispose() |
| ParticleEffect | Effect.dispose() |
| SpriteBatch / ShapeRenderer / ModelBatch | Batch.dispose() |

### Disposal anti-pattern: AssetManager + dispose()
If you got the resource via `assets.get(...)`, do NOT call `dispose()` on it yourself. AssetManager owns the resource. Call `assets.unload(path)` or `assets.dispose()` instead. Double-dispose corrupts AssetManager's internal state.

### Diagnosing VRAM leaks
- Android Studio Profiler -> Memory -> watch graphics memory line
- Steadily increasing graphics memory across screen transitions = leaked Texture or FrameBuffer
- Look for new Texture(...), new FrameBuffer(...), new Skin(...) outside of AssetManager that lack a corresponding dispose

## Scene2D Performance

Scene2D is the standard UI framework: `Stage`, `Group`, `Actor`, `Table`, `Cell`.

### Group.isTransform
Every `Group` defaults `isTransform = true`, which pushes/pops a transformation matrix on every draw call. Costs measurable CPU on UI trees with many Groups.
```java
group.setTransform(false);  // No rotation/scaling support, faster
```
Set false on any Group that does not need rotation or scale.

### Avoid Actor.act / draw overhead on static UI
Actors with no animation or hit-testing waste CPU each frame. Community pattern: subclass to no-op:
```java
public class ActionlessGroup extends Group {
    @Override public void act(float delta) { }
    @Override public Actor hit(float x, float y, boolean touchable) { return null; }
}
```

### Stage debug rendering
`stage.setDebugAll(true)` overlays bounding boxes; useful for layout debugging, costs frame time. Disable in production.

## ShapeRenderer

Primitive line/rect/circle drawing. Each `begin()` defines a mode (Line, Filled, Point) and ends with `end()`. Like SpriteBatch, batches draws between begin/end. Do NOT use mid-SpriteBatch.

## ModelBatch (3D)

3D analog of SpriteBatch:
```java
modelBatch.begin(camera);
modelBatch.render(instance, environment);
modelBatch.end();
```
3D rendering also requires:
- `Environment` for lighting (`ColorAttribute.AmbientLight`, `DirectionalLight`)
- `ModelInstance` (cheap, references shared `Model`)
- `PerspectiveCamera` with appropriate near/far

## Frame-Pacing Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Stutter every few seconds | Major GC | Pool Vector2/Color/Component objects; avoid per-frame allocation |
| Smooth desktop, choppy Android | Texture bindings, draw calls | Pack atlases; reduce flushes |
| First-frame freeze | Synchronous asset load | Move to AssetManager; show loading screen |
| Slow loading screen | Single update() per frame | Call assets.update() multiple times per frame |
| Frame drops on resize | Recreating textures/framebuffers | Cache and resize only if dimensions changed |

## Source References

- https://libgdx.com/wiki/graphics/2d/spritebatch-textureregions-and-sprites
- https://libgdx.com/wiki/graphics/2d/2d-graphics
- https://libgdx.com/wiki/graphics/profiling
- https://yairm210.medium.com/the-libgdx-performance-guide-1d068a84e181 (community canonical reference, 8+ years of Unciv experience)
