<script lang="ts">
  import type { Snippet } from 'svelte';
  import { route } from './router.svelte';

  let { routes, fallback }: { routes: Record<string, Snippet>; fallback: Snippet } = $props();

  const current = $derived(routes[route.path] ?? fallback);
</script>

{@render current()}
