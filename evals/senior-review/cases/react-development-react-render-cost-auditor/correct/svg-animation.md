# Supported animation path

Requirement: the required progress graphic animates continuously while input remains responsive. Its animation may consume at most 8ms main-thread work per frame. This is a React-owned component using the following complete markup/style.

```html
<div class="pulse"><svg width="80" height="80" viewBox="0 0 80 80"><circle cx="40" cy="40" r="20"/></svg></div>
<style>
.pulse { width: 80px; height: 80px; animation: pulse 1s linear infinite; transform-origin: center; }
@keyframes pulse { to { transform: rotate(360deg); } }
</style>
```

Supplied candidate-bound synthetic profile for supported engine RenderEngine 5: the effective wrapper-compositing path costs 2ms main-thread work per frame, preserves this graphic's size/position and meets the 8ms requirement. A direct transform on this SVG would use an 18ms raster path on this engine. The wrapper has no accessibility/interaction role and adds no flow space beyond the original 80x80 graphic. This profile is an input record, not a new browser measurement; other engines may behave differently.
