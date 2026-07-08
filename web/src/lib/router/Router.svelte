<script lang="ts">
  import type { Snippet } from 'svelte';
  import { route } from './router.svelte';

  let {
    routes,
    fallback,
    authed,
    isPublic,
    login,
  }: {
    routes: Record<string, Snippet>;
    fallback: Snippet;
    authed: boolean;
    isPublic: (path: string) => boolean;
    login: Snippet;
  } = $props();

  // Structural gate: an unauthenticated request for a non-public path renders
  // the login snippet, never the target route — no protected snippet can render
  // (and no on-mount fetch can fire) before the redirect $effect runs.
  const current = $derived(
    !authed && !isPublic(route.path) ? login : (routes[route.path] ?? fallback),
  );
</script>

{@render current()}
