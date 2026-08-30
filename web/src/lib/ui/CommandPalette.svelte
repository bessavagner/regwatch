<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '../router/router.svelte';
  import type { Command } from '../commands';

  let { commands }: { commands: Command[] } = $props();

  let open = $state(false);
  let query = $state('');
  let selected = $state(0);
  let dialogEl: HTMLDialogElement;
  let inputEl: HTMLInputElement;

  const matching = $derived(
    commands.filter((c) => c.label.toLowerCase().includes(query.trim().toLowerCase())),
  );
  // Only routes take the roving selection: a shortcut has nothing to open, and
  // letting Enter land on one would make the palette lie about what it does.
  const filtered = $derived(
    matching.filter((c): c is Extract<Command, { kind: 'route' }> => c.kind === 'route'),
  );
  const shortcuts = $derived(
    matching.filter((c): c is Extract<Command, { kind: 'shortcut' }> => c.kind === 'shortcut'),
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
      placeholder="ir para…"
      aria-label="ir para a página"
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
  {/if}
  {#if shortcuts.length}
    <p class="cmdk-group">atalhos da triagem</p>
    <ul class="cmdk-list">
      {#each shortcuts as sc (sc.label)}
        <li class="cmdk-item">
          <span>{sc.label}</span>
          <span class="cmdk-item-key">{sc.keys}</span>
        </li>
      {/each}
    </ul>
  {/if}
  {#if !filtered.length && !shortcuts.length}
    <p class="cmdk-empty">nada encontrado.</p>
  {/if}
</dialog>
