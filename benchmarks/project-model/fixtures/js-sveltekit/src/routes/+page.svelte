<script lang="ts">
  import { title } from "$lib";
  let { data } = $props();
</script>

<h1>{title(data.heading)}</h1>
