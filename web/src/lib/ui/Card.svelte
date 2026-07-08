<script lang="ts">
  import type { Snippet } from 'svelte';
  let { children }: { children: Snippet } = $props();
</script>

<div class="rounded-card border border-gray-200 bg-white p-4 shadow-sm">
  {@render children()}
</div>
