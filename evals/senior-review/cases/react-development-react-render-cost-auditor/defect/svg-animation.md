# Supported animation path

Requirement: the required progress graphic animates continuously while input remains responsive. Its animation may consume at most 8ms main-thread work per frame. This is a React-owned component using the following complete markup/style.

```html
<svg class="pulse" width="80" height="80" viewBox="0 0 80 80"><circle cx="40" cy="40" r="20"/></svg>
<style>
.pulse { animation: pulse 1s linear infinite; transform-origin: center; }
@keyframes pulse { to { transform: rotate(360deg); } }
</style>
```

Supplied candidate-bound synthetic profile for supported engine RenderEngine 5: transforming this SVG uses a raster path costing 18ms of main-thread work per frame. The engine's implemented wrapper-compositing path for an 80x80 HTML wrapper costs 2ms with the same graphic and transform. No compiler/build rule moves this transform. User-visible position and size must remain unchanged. This profile is an input record, not a new browser measurement; other engines may behave differently.
