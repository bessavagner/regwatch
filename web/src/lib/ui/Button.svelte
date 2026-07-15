<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    variant = 'primary',
    type = 'button',
    disabled = false,
    loading = false,
    onclick,
    children,
  }: {
    variant?: 'primary' | 'ghost';
    type?: 'button' | 'submit';
    disabled?: boolean;
    loading?: boolean;
    onclick?: () => void;
    children?: Snippet;
  } = $props();

  const base =
    'btn inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap rounded-control px-4 text-sm font-medium ' +
    'disabled:cursor-not-allowed disabled:opacity-50 ' +
    'focus-visible:outline-2 focus-visible:outline-focus focus-visible:outline-offset-2';
  const styles = {
    primary: 'bg-accent text-accent-ink border border-transparent hover:bg-accent/90',
    ghost: 'bg-transparent text-ink-2 border border-transparent hover:border-rule hover:bg-paper-2',
  };
</script>

<button {type} disabled={disabled || loading} aria-busy={loading} {onclick} class="{base} {styles[variant]}">
  {#if loading}<span class="spinner" aria-hidden="true"></span>{/if}
  {#if children}{@render children()}{/if}
</button>

<style>
  .btn {
    /* Browsers reset text-transform on <button> to `none` in the UA stylesheet —
       it doesn't inherit body's lowercase like a plain element would. */
    text-transform: lowercase;
    transition: background-color var(--dur-short) var(--ease-out),
                border-color var(--dur-short) var(--ease-out),
                transform 100ms var(--ease-out);
  }
  .btn:active:not(:disabled) { transform: translateY(1px); }

  .spinner {
    width: 0.85em;
    height: 0.85em;
    border-radius: 999px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    opacity: 0.7;
    animation: spin 700ms linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (prefers-reduced-motion: reduce) {
    .spinner { animation-duration: 1400ms; }
  }
</style>
