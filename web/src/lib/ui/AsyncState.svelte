<script lang="ts">
  import type { Snippet } from 'svelte';
  let {
    state,
    loaded,
    empty,
    error,
  }: {
    state: 'idle' | 'loading' | 'loaded' | 'empty' | 'error';
    loaded: Snippet;
    empty?: Snippet;
    error?: Snippet;
  } = $props();
</script>

{#if state === 'loading' || state === 'idle'}
  <p class="p-4 text-sm text-muted">Loading…</p>
{:else if state === 'error'}
  {#if error}{@render error()}{:else}<p role="alert" class="p-4 text-sm text-danger">Something went wrong.</p>{/if}
{:else if state === 'empty'}
  {#if empty}{@render empty()}{:else}<p class="p-4 text-sm text-muted">Nothing here yet.</p>{/if}
{:else}
  {@render loaded()}
{/if}
