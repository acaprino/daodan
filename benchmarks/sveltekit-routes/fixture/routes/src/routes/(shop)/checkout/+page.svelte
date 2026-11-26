<script lang="ts">
	import { enhance } from '$app/forms';
</script>

<form method="POST" action="?/pay" use:enhance><button>Pay</button></form>
<form method="POST" action="?/cancel" use:enhance><button>Cancel</button></form>
