<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    variant = 'primary',
    type = 'button',
    disabled = false,
    onclick,
    children,
  }: {
    variant?: 'primary' | 'ghost';
    type?: 'button' | 'submit';
    disabled?: boolean;
    onclick?: () => void;
    children?: Snippet;
  } = $props();

  const base =
    'inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50';
  const styles = {
    primary: 'bg-brand-600 text-white hover:bg-brand-500',
    ghost: 'bg-transparent text-brand-600 hover:bg-brand-50',
  };
</script>

<button {type} {disabled} {onclick} class="{base} {styles[variant]}">
  {#if children}{@render children()}{/if}
</button>
