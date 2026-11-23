<script lang="ts">
	import { enhance } from '$app/forms';
	let { data } = $props();
</script>

<h1>{data.title}</h1>
<form method="POST" action="?/comment" use:enhance><button>Comment</button></form>
<form method="POST" action="?/like" use:enhance><button>Like</button></form>
