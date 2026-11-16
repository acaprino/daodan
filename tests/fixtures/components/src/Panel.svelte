<script lang="ts">
  let count = $state(0);
  function select(id: number) { count = id; }
  function title(s: string) { return s.trim(); }
  const items = [{ id: 1, name: "a" }];
</script>

<h1 onclick={() => select(2)}>{title("x")} {count}</h1>
{#each items as item (item.id)}
  <p>{title(item.name)}</p>
{/each}
