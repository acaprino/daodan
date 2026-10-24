# React bootstrap dependency

Requirement: the startup must mount the required React screen. Supported browser executes classic async external scripts when each fetch completes; classic defer scripts execute after parsing, in document order. There is no loader, import dependency or build rewrite. These are complete source/asset facts; no browser was run.

```html
<div id="root"></div>
<script src="/vendor.js" defer></script>
<script src="/app.js" defer></script>
```

Complete /vendor.js:
```js
window.Widget = {mount() { document.querySelector('#root').textContent = 'Ready'; }};
```
Complete /app.js:
```js
window.Widget.mount();
```

Supplied matching synthetic network schedule: app.js finishes at 10ms and vendor.js at 200ms after both requests start. Neither is cached, and Widget has no earlier definition. The root element is parsed before either script. There is no deadline earlier than both required assets becoming available. This input describes a reachable fetch ordering, not measured user latency or a requirement to use one attribute universally.
