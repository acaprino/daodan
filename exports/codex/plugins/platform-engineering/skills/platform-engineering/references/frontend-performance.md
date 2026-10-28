<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# Frontend Performance: Bundles, Images, and Core Web Vitals

## Bundle Size

The JavaScript you ship directly determines how fast your application becomes usable. **Pinterest reduced JavaScript from 2.5MB to <200KB and dropped Time to Interactive from 23 seconds to 5.6 seconds.** On slow 3G, a 2MB bundle takes ~7 seconds to download alone -- before a single line executes.

### MUST

- **Use ES modules for tree shaking.** Named imports (`import { fn } from 'lib'`) are tree-shakeable; CommonJS (`require`) is not. Mark `sideEffects: false` in package.json.
- **Implement route-based code splitting** -- without it, users download the entire application upfront. Use `React.lazy()`, Vue `defineAsyncComponent`, or Angular lazy-loaded modules.
- **Set performance budgets in CI/CD** using webpack `performance.hints: 'error'`, bundlesize, or Lighthouse CI to catch regressions before deploy.
- Target **<170KB compressed** for critical-path JavaScript on mobile.

### DO

- Replace heavy libraries with lighter alternatives: lodash to lodash-es or native methods; moment.js to dayjs or date-fns (saves ~200KB+).
- Use dynamic imports for heavy features loaded on demand.
- Use Brotli compression over gzip (15-25% smaller).
- Analyze bundles regularly with webpack-bundle-analyzer.

### DON'T

- Import entire libraries -- `import _ from 'lodash'` pulls ~70KB gzipped when you might need one function.
- Skip differential bundling -- ship modern ES2020+ to capable browsers and polyfilled bundles only to legacy browsers.
- Ignore CSS-in-JS bundle costs (some add 15-30KB+ runtime).

### Native Targets

- Mobile: target <20MB APK/IPA for lightweight apps. Enable R8/ProGuard (Android).
- Electron bundles Chromium at 80-150MB baseline regardless of app size.
- Tauri apps are <10MB total.

## Images

Images account for ~42% of LCP elements and over 60% of total page weight. Modern formats reduce payload by 50-80%.

### MUST

- **Serve images in modern formats** -- WebP minimum, AVIF with WebP fallback via `<picture>`. Browser support: WebP ~96%, AVIF ~90%+.
- **Set explicit width/height or aspect-ratio on all images** to prevent Cumulative Layout Shift.
- **Use responsive images with srcset/sizes** -- serving a 2400px image to a 375px phone wastes ~80% of downloaded bytes.
- **Never lazy-load the hero/LCP image** -- use `loading="eager"` and `fetchpriority="high"`. Preload it: `<link rel="preload" as="image" href="hero.webp" fetchpriority="high">`.

### DO

- Use `loading="lazy"` on all below-the-fold images.
- Use image CDNs (Cloudinary, imgix) for automatic format conversion, resizing, and compression.
- Compress to quality sweet spots: JPEG 75-85, WebP 75-80, AVIF 60-70.

### DON'T

- Serve unoptimized images -- a single 5MB hero image adds 3+ seconds to LCP on 4G.
- Use GIFs for animations -- replace with WebM/MP4 video for 90%+ size reduction.

### Mobile

Images are the #1 memory consumer on mobile. Downsample to display size, use LRU memory caches, recycle bitmaps, and decode off the main thread.

## Core Web Vitals

Google's Core Web Vitals measure real-world user experience and directly influence search rankings. Only ~48% of mobile pages currently pass all three metrics.

### Thresholds (75th percentile)

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | <=2.5s | 2.5-4s | >4s |
| **INP** (Interaction to Next Paint) | <=200ms | 200-500ms | >500ms |
| **CLS** (Cumulative Layout Shift) | <=0.1 | 0.1-0.25 | >0.25 |

### Business Impact

- **Vodafone:** improved LCP by 31%, saw 8% sales increase.
- **Renault:** improved LCP by 1 second, achieved 14% bounce rate reduction and 13% conversion increase.
- **Yahoo! JAPAN:** fixed CLS issues, gained 15.1% more page views per session.
- 53% of mobile users abandon sites taking more than 3 seconds to load.

### MUST (LCP)

- Preload the LCP image with `fetchpriority="high"`.
- Optimize server response time (TTFB <800ms).
- Never lazy-load the LCP element.

### MUST (INP)

- Break up long tasks (>50ms) on the main thread using `scheduler.yield()`, `requestIdleCallback`, or `setTimeout(0)`.
- Move heavy computation to Web Workers.

### MUST (CLS)

- Set explicit dimensions on all media elements.
- Use `font-display: swap` or `optional`.
- Reserve space for dynamic content with CSS `min-height`.

### DO

- Monitor with CrUX (real user data) + Lighthouse (lab data) continuously in CI. Field data from CrUX is what Google uses for ranking.

### Native Equivalents

- Cold start time (<2 seconds target), frame rendering latency (<16ms for 60fps), and layout stability during data loading.
- Desktop: track window render time, UI thread responsiveness, and resize stability.

## Official docs

- Core Web Vitals + thresholds: https://web.dev/articles/vitals
- LCP optimization guide: https://web.dev/articles/optimize-lcp
- INP optimization guide: https://web.dev/articles/optimize-inp
- CLS optimization guide: https://web.dev/articles/optimize-cls
- web.dev image optimization: https://web.dev/learn/images
- WebP / AVIF browser support (caniuse): https://caniuse.com/webp
- MDN responsive images (`srcset`/`sizes`): https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images
- MDN `font-display`: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display
- webpack-bundle-analyzer: https://github.com/webpack-contrib/webpack-bundle-analyzer
- Lighthouse CI: https://github.com/GoogleChrome/lighthouse-ci
- CrUX (Chrome User Experience Report): https://developer.chrome.com/docs/crux
- Brotli compression (RFC 7932): https://www.rfc-editor.org/rfc/rfc7932
- Pinterest case study: https://medium.com/pinterest-engineering/a-one-year-pwa-retrospective-f4a2f4129e05
