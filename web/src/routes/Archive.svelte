<script lang="ts">
  import { listMatches, reopenMatch, deleteMatches } from '../lib/api/resources';
  import type { Match } from '../lib/api/types';
  import { ApiError } from '../lib/api/client';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import MatchCard from '../lib/ui/MatchCard.svelte';
  import Button from '../lib/ui/Button.svelte';

  let status = $state<'idle' | 'loading' | 'loaded' | 'empty' | 'error'>('idle');
  let matches = $state<Match[]>([]);
  let selected = $state<number[]>([]);
  let confirming = $state(false);
  let actionError = $state('');

  async function load() {
    status = 'loading';
    try {
      // The archive is not a set of its own: it is exactly what the feed hides.
      const res = await listMatches({ state: 'dismissed' });
      matches = res.results;
      status = res.results.length ? 'loaded' : 'empty';
    } catch {
      status = 'error';
    }
  }

  $effect(() => { load(); });

  function drop(ids: number[]) {
    const gone = new Set(ids);
    matches = matches.filter((m) => !gone.has(m.id));
    selected = selected.filter((id) => !gone.has(id));
    if (matches.length === 0) status = 'empty';
  }

  async function restore(match: Match) {
    actionError = '';
    try {
      await reopenMatch(match.id);
      drop([match.id]);
    } catch (err) {
      actionError = err instanceof ApiError ? err.detail : 'não foi possível restaurar';
    }
  }

  function toggle(id: number) {
    selected = selected.includes(id) ? selected.filter((n) => n !== id) : [...selected, id];
    confirming = false;
  }

  async function confirmDelete() {
    actionError = '';
    const ids = [...selected];
    try {
      await deleteMatches(ids);
      drop(ids);
    } catch (err) {
      actionError = err instanceof ApiError ? err.detail : 'não foi possível excluir';
    } finally {
      confirming = false;
    }
  }
</script>

<section class="mx-auto max-w-2xl p-4">
  <div class="mb-3 flex items-center justify-between">
    <h1 class="text-xl">arquivo</h1>
  </div>

  <p class="mb-3 text-sm text-muted">
    o que você arquivou continua aqui. arquivar nunca apaga nada — só some da
    triagem. excluir, sim, apaga de vez.
  </p>

  {#if actionError}<p role="alert" class="mb-2 text-sm text-danger">{actionError}</p>{/if}

  {#if confirming}
    <div class="bulk-bar" role="group" aria-label="confirmar exclusão definitiva">
      <span class="bulk-bar__label">
        excluir {selected.length} ocorrência{selected.length === 1 ? '' : 's'} de vez?
        isso não pode ser desfeito
      </span>
      <Button variant="primary" onclick={confirmDelete}>confirmar</Button>
      <Button variant="ghost" onclick={() => (confirming = false)}>cancelar</Button>
    </div>
  {:else if selected.length}
    <div class="bulk-bar" role="group" aria-label="ações do arquivo">
      <span class="bulk-bar__label">
        {selected.length} selecionada{selected.length === 1 ? '' : 's'}
      </span>
      <Button variant="ghost" onclick={() => (confirming = true)}>excluir definitivamente</Button>
      <Button variant="ghost" onclick={() => (selected = [])}>limpar seleção</Button>
    </div>
  {/if}

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="rows">
        {#each matches as match, i (match.id)}
          <li
            class="row row--triage reveal"
            class:is-selected={selected.includes(match.id)}
            style="--i: {i}"
          >
            <label class="row__select">
              <input
                type="checkbox"
                class="accent-accent"
                checked={selected.includes(match.id)}
                onchange={() => toggle(match.id)}
              />
              <span class="sr-only">selecionar {match.act_detail.title}</span>
            </label>
            <div class="row__content">
              <MatchCard {match}>
                {#snippet children()}
                  <Button variant="ghost" onclick={() => restore(match)}>restaurar</Button>
                {/snippet}
              </MatchCard>
            </div>
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-sm text-muted">o arquivo está vazio.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-sm text-danger">não foi possível carregar o arquivo.</p>{/snippet}
  </AsyncState>
</section>
