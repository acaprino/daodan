<script>
  let { on = false } = $props();
</script>

<div class="card {on ? 'on' : ''}" class:active={on}>
  <span class="label">x</span>
</div>

<style>
  .card { color: red; }
  .label { color: blue; }
  :global(.on) { color: green; }
  :global(html).dark .label { color: white; }
</style>
