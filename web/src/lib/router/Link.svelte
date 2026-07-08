<script lang="ts">
  import type { Snippet } from 'svelte';
  import { navigate } from './router.svelte';

  let { to, class: cls = '', children }: { to: string; class?: string; children: Snippet } = $props();

  function onclick(e: MouseEvent) {
    e.preventDefault();
    navigate(to);
  }
</script>

<a href={to} {onclick} class={cls}>{@render children()}</a>
