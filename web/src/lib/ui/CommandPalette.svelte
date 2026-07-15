<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '../router/router.svelte';

  let { routes }: { routes: { path: string; label: string }[] } = $props();

  let open = $state(false);
  let query = $state('');
  let selected = $state(0);
  let dialogEl: HTMLDialogElement;
  let inputEl: HTMLInputElement;

  const filtered = $derived(
    routes.filter((r) => r.label.toLowerCase().includes(query.trim().toLowerCase())),
  );

  export function show() {
    open = true;
    query = '';
    selected = 0;
  }

  $effect(() => {
    if (open) {
      dialogEl?.showModal();
      queueMicrotask(() => inputEl?.focus());
    } else {
      dialogEl?.close();
    }
  });

  function close() {
    open = false;
  }

  function choose(path: string) {
    navigate(path);
    close();
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selected = Math.min(selected + 1, filtered.length - 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selected = Math.max(selected - 1, 0);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selected]) choose(filtered[selected].path);
    }
  }

  function onGlobalKeydown(e: KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (open) close();
      else show();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', onGlobalKeydown);
    return () => window.removeEventListener('keydown', onGlobalKeydown);
  });
</script>

<dialog
  bind:this={dialogEl}
  class="cmdk-dialog"
  onclose={close}
  onclick={(e) => {
    if (e.target === dialogEl) close();
  }}
>
  <div class="cmdk-input-row">
    <span class="font-mono text-xs text-muted" aria-hidden="true">⌘K</span>
    <input
      bind:this={inputEl}
      bind:value={query}
      oninput={() => (selected = 0)}
      onkeydown={onKeydown}
      type="text"
      class="cmdk-input"
      placeholder="Jump to…"
      aria-label="Jump to page"
    />
  </div>
  {#if filtered.length}
    <ul class="cmdk-list" role="listbox">
      {#each filtered as r, i (r.path)}
        <!-- Keyboard nav is handled by the input's onkeydown (roving via arrow keys + Enter);
             this row is a pointer-only affordance, per the combobox/listbox pattern. -->
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <li
          class="cmdk-item"
          role="option"
          aria-selected={i === selected}
          onmouseenter={() => (selected = i)}
          onclick={() => choose(r.path)}
        >
          <span>{r.label}</span>
          <span class="cmdk-item-key">↵</span>
        </li>
      {/each}
    </ul>
  {:else}
    <p class="cmdk-empty">No matches.</p>
  {/if}
</dialog>
