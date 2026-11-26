<script lang="ts">
	let { data } = $props();
</script>

<ul>{#each data.posts as post}<li>{post}</li>{/each}</ul>
