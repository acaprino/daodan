<script lang="ts">
	let { children } = $props();
</script>

<nav><a href="/">Home</a> <a href="/about">About</a></nav>
{@render children()}
