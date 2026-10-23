<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# Deployment Platforms

Targeting Desktop (LWJGL3), Android, iOS (RoboVM), and HTML5 (GWT/TeaVM) from a shared libGDX codebase.

## Desktop (LWJGL3)

The Desktop backend uses LWJGL3 (Lightweight Java Game Library 3) for windowing, input, and OpenGL.

### Launcher
```java
public class Lwjgl3Launcher {
    public static void main(String[] args) {
        Lwjgl3ApplicationConfiguration config = new Lwjgl3ApplicationConfiguration();
        config.setTitle("My Game");
        config.setWindowedMode(1280, 720);
        config.setForegroundFPS(60);
        config.useVsync(true);
        config.setWindowIcon("icon128.png", "icon32.png", "icon16.png");
        new Lwjgl3Application(new MyGame(), config);
    }
}
```

### Build Outputs
- `:lwjgl3:run` -- launch in IDE
- `:lwjgl3:dist` -- builds a fat JAR with all dependencies bundled (large, ~50-100 MB for a typical game)
- `:lwjgl3:jpackage` (manual setup) -- builds platform-native installers via `jpackage`

### Packaging Options
1. **Fat JAR**: simplest distribution; requires user to have Java installed; runs with `java -jar mygame.jar`
2. **jpackage**: ships a bundled JDK runtime and creates `.exe`/`.dmg`/`.deb` installers. Recommended for end-user distribution. Requires JDK 14+ on the build machine
3. **PackR** (community): older alternative to jpackage; bundles a minimal JRE; still works but jpackage is the modern path
4. **Steam**: distribute as fat JAR or jpackage build; Steam runtime handles launching

### LWJGL3 Version
libGDX 1.14.0 ships LWJGL3 3.4.1 by default, which supports Java 25+. Earlier libGDX shipped LWJGL3 3.3.x.

### Window and Fullscreen
```java
config.setWindowedMode(1280, 720);
// or
Graphics.DisplayMode primary = Lwjgl3ApplicationConfiguration.getDisplayMode();
config.setFullscreenMode(primary);

// In-game toggle:
Gdx.graphics.setFullscreenMode(Gdx.graphics.getDisplayMode());
Gdx.graphics.setWindowedMode(1280, 720);
```

### Audio Backends
LWJGL3 uses OpenAL via `OpenALAudio`. No configuration usually needed.

## Android

The Android backend uses native libraries and runs on the GLSurfaceView thread.

### Project Layout
```
android/
  AndroidManifest.xml
  build.gradle              # Android-specific Gradle config
  src/main/java/.../android/AndroidLauncher.java
  res/                      # icons, drawables
  assets/                   # shared with the game (symlinked or referenced from core)
```

### Launcher
```java
public class AndroidLauncher extends AndroidApplication {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        AndroidApplicationConfiguration config = new AndroidApplicationConfiguration();
        config.useImmersiveMode = true;
        initialize(new MyGame(), config);
    }
}
```

### Recommended Versions (2025-2026)
- `compileSdk = 34` or 35
- `targetSdk = 34` or 35 (Play Store requires 34+ for new submissions as of August 2024)
- `minSdk = 21` (covers ~99% of active devices)
- `kotlin = "1.9+"` if using Kotlin

### Build Outputs
- `:android:installDebug` -- install debug APK to connected device
- `:android:assembleRelease` -- release APK (requires signing)
- `:android:bundleRelease` -- AAB (Android App Bundle); required for Play Store

### Signing
Add to `android/build.gradle`:
```gradle
android {
    signingConfigs {
        release {
            storeFile file(System.getenv("KEYSTORE_PATH"))
            storePassword System.getenv("KEYSTORE_PASSWORD")
            keyAlias System.getenv("KEY_ALIAS")
            keyPassword System.getenv("KEY_PASSWORD")
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled false  // libGDX + Proguard requires careful rule tuning
        }
    }
}
```

### Permissions
Add to `AndroidManifest.xml` only what you need:
- `android.permission.INTERNET` for networked games
- `android.permission.VIBRATE` for `Gdx.input.vibrate(...)`
- Storage permissions are no longer needed for `Gdx.files.local(...)`

### Android-Specific Lifecycle
- `pause()` is called when the activity backgrounds
- `resume()` is called when it returns to foreground
- The OpenGL context may be destroyed; libGDX recreates Textures from cached pixmaps where possible. Custom GPU resources may need manual recreation
- AssetManager-managed assets survive pause/resume

### Immersive Mode
Hide system bars during gameplay:
```java
config.useImmersiveMode = true;
```

### Gradle Plugin Compatibility
libGDX 1.14.0 supports recent Android Gradle Plugin versions (8.x). Always match the Android Gradle Plugin to the Gradle version (8.x AGP requires Gradle 8.x+).

## iOS (RoboVM)

iOS deployment uses RoboVM, an AOT compiler that converts Java bytecode to native ARM. RoboVM is now maintained by the libGDX team after the Microsoft acquisition shutdown.

### Constraints
- **Java 8 language level cap**: RoboVM does not support Java 9+ syntax or APIs. Your core module must compile against Java 8 if it targets iOS
- **macOS-only builds**: Xcode is required; you cannot produce iOS builds from Linux or Windows
- **Apple Developer account required** for App Store distribution

### Project Layout
```
ios/
  build.gradle
  robovm.properties      # app id, version, build type
  robovm.xml             # frameworks, resources, info.plist
  src/main/java/.../ios/IOSLauncher.java
```

### Launcher
```java
public class IOSLauncher extends IOSApplication.Delegate {
    @Override
    protected IOSApplication createApplication() {
        IOSApplicationConfiguration config = new IOSApplicationConfiguration();
        return new IOSApplication(new MyGame(), config);
    }

    public static void main(String[] argv) {
        NSAutoreleasePool pool = new NSAutoreleasePool();
        UIApplication.main(argv, null, IOSLauncher.class);
        pool.close();
    }
}
```

### Build Tasks
- `:ios:launchIPhoneSimulator` -- run in iOS Simulator
- `:ios:launchIPadSimulator` -- iPad simulator
- `:ios:createIPA` -- build a signed IPA for distribution

### Signing
Configure in `robovm.properties`:
```
app.id=com.example.mygame
app.version=1.0.0
app.build=1
app.name=MyGame
app.executable=MyGame
```

Provisioning profile and signing identity are configured per build via Xcode.

### iOS-Specific Constraints
- No reflection on classes that aren't explicitly forced-linked. Add `<forceLinkClasses>` entries in `robovm.xml` for any class loaded via reflection
- Larger app size due to AOT compilation
- Floating-point performance is good on iOS hardware

## HTML5 (GWT)

The HTML5 backend compiles Java to JavaScript via GWT (Google Web Toolkit).

### Constraints
- **Java only**: Kotlin is NOT compatible with GWT
- **No reflection**: classes must be explicitly listed in the GWT module XML
- **Limited Java API**: some `java.util` and `java.text` APIs are not implemented in GWT
- **Slow builds**: full GWT compile can take 1-5 minutes on first build
- **Larger asset sizes** are awkward over network; lazy-load if possible

### Project Layout
```
html/
  build.gradle
  src/main/java/.../html/HtmlLauncher.java
  src/main/java/.../GdxDefinition.gwt.xml
  src/main/java/.../GdxDefinitionSuperdev.gwt.xml
  webapp/index.html
```

### Launcher
```java
public class HtmlLauncher extends GwtApplication {
    @Override
    public GwtApplicationConfiguration getConfig() {
        return new GwtApplicationConfiguration(640, 480);
    }

    @Override
    public ApplicationListener createApplicationListener() {
        return new MyGame();
    }
}
```

### Build Tasks
- `:html:superDev` -- super dev mode; rebuilds on save, runs at http://localhost:8080
- `:html:dist` -- production build to `html/build/dist/`; deploy this directory to a web host

### Audio on HTML
Browsers restrict autoplay; audio must start after user interaction (first click). libGDX handles most of this transparently.

### Reflection Caveats
Add to `GdxDefinition.gwt.xml`:
```xml
<extend-configuration-property name="gdx.reflect.include" value="com.example.MyClass"/>
```
Or use `@GwtIncompatible` to mark Java-only code paths.

## HTML5 (TeaVM) Alternative

TeaVM is a modern alternative to GWT that supports Kotlin and produces smaller, faster output.

### Status (2025-2026)
libGDX TeaVM support is described as "work-in-progress". The community project `xpenatan/gdx-teavm` provides the runtime. Choose TeaVM if:
- You want Kotlin in your HTML build
- You need faster builds than GWT (TeaVM compiles in seconds)
- You can accept some libGDX features may not yet work

Stay on GWT if:
- You need maximum maturity and feature parity
- Your codebase is pure Java
- You rely on extensions known to work on GWT

## Cross-Platform Code Strategy

Keep platform-specific code in the platform module, NEVER in core:
```
core/                  # game logic, rendering, input handling
  uses only Gdx.app, Gdx.gl, Gdx.input, Gdx.files etc.

lwjgl3/                # desktop-specific (jpackage config, native file dialogs)
android/               # Android-specific (Google Play Games, AdMob, permissions)
ios/                   # iOS-specific (Game Center, StoreKit)
html/                  # HTML-specific (browser fullscreen API, web storage)
```

For platform-specific behavior in core code (e.g. "show ad banner"), use the `Gdx.app.getType()` check OR define a platform-abstraction interface in core and implement per-platform:
```java
// In core
public interface AdProvider {
    void showInterstitial();
}

// In android
public class AndroidAdProvider implements AdProvider {
    public void showInterstitial() { /* AdMob calls */ }
}

// In core MyGame constructor
public MyGame(AdProvider ads) { this.ads = ads; }

// In AndroidLauncher
new MyGame(new AndroidAdProvider(this));
```

## Build Pipeline (CI/CD)

Common setup:
- **GitHub Actions** for desktop, Android, HTML5 builds (Linux runners)
- **macOS runners** for iOS builds (separate workflow)
- Cache `~/.gradle` between runs to speed up dependency resolution
- For Android signing in CI, store keystore as base64-encoded secret and decode in pre-build step
- For iOS, store p12 and provisioning profile as base64 secrets; use `xcrun` for signing

## Source References

- https://libgdx.com/wiki/deployment/deploying-your-application
- https://libgdx.com/wiki/deployment/bundling-a-jre-jpackage
- https://libgdx.com/wiki/deployment/deploying-android
- https://libgdx.com/wiki/deployment/deploying-ios
- https://libgdx.com/wiki/deployment/deploying-html5
- https://github.com/xpenatan/gdx-teavm (TeaVM backend)
- https://github.com/MobiVM/robovm (RoboVM iOS compiler)
