<script lang="ts">
  import { listWatches, listClients, updateWatch } from '../lib/api/resources';
  import { ApiError } from '../lib/api/client';
  import type { Client, Watch } from '../lib/api/types';
  import { navigate } from '../lib/router/router.svelte';
  import { SECTIONS } from '../lib/constants';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import Card from '../lib/ui/Card.svelte';
  import Button from '../lib/ui/Button.svelte';
  import Badge from '../lib/ui/Badge.svelte';
  import WatchForm from '../lib/ui/WatchForm.svelte';
  import BackfillForm from '../lib/ui/BackfillForm.svelte';

  // The row used to render a bare "seção" with no value for an all-sections
  // watch; map the stored code to the label the form offers.
  const sectionLabel = (code: string) =>
    SECTIONS.find((s) => s.value === code)?.label ?? code;

  let status = $state<'idle' | 'loading' | 'loaded' | 'empty' | 'error'>('idle');
  let watches = $state<Watch[]>([]);
  let clients = $state<Client[]>([]);
  let showForm = $state(false);
  let editing = $state<Watch | undefined>(undefined);
  let backfillingWatch = $state<Watch | undefined>(undefined);
  let toggleError = $state('');

  async function load() {
    status = 'loading';
    try {
      const [w, c] = await Promise.all([listWatches(), listClients()]);
      watches = w.results;
      clients = c.results;
      status = w.results.length ? 'loaded' : 'empty';
    } catch {
      status = 'error';
    }
  }

  $effect(() => { load(); });

  async function toggle(w: Watch) {
    try {
      const updated = await updateWatch(w.id, { active: !w.active });
      watches = watches.map((x) => (x.id === updated.id ? updated : x));
      toggleError = '';
    } catch (err) {
      toggleError = err instanceof ApiError ? err.detail : 'não foi possível atualizar a busca';
    }
  }

  function onsaved(w: Watch) {
    const exists = watches.some((x) => x.id === w.id);
    watches = exists ? watches.map((x) => (x.id === w.id ? w : x)) : [...watches, w];
    showForm = false;
    editing = undefined;
    if (status === 'empty') status = 'loaded';
  }
</script>

<section class="mx-auto max-w-2xl p-4">
  <div class="mb-3 flex items-center justify-between">
    <h1 class="text-xl">buscas</h1>
    <Button disabled={clients.length === 0} onclick={() => { editing = undefined; showForm = true; }}>nova busca</Button>
  </div>

  {#if status !== 'idle' && status !== 'loading' && clients.length === 0}
    <p class="mb-2 text-sm text-muted">
      cadastre um cliente primeiro —
      <a href="/clients" class="text-accent underline" onclick={(e) => { e.preventDefault(); navigate('/clients'); }}>clientes</a>.
    </p>
  {/if}

  {#if showForm && !editing}
    <div class="mb-3">
      <Card>
        <WatchForm {clients} {onsaved} />
      </Card>
    </div>
  {/if}

  {#if toggleError}<p role="alert" class="mb-2 text-sm text-danger">{toggleError}</p>{/if}

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="rows">
        {#each watches as w, i (w.id)}
          <li class="row reveal" style="--i: {i}">
            <div class="flex items-center justify-between gap-2">
              <div>
                <p class="as-typed text-xs text-muted">{w.client_name}</p>
                <p class="as-typed text-sm font-medium text-ink">{w.groups.map((g) => g.terms.map((t) => t.text).join(' / ')).join(' + ')}</p>
                <p class="mt-0.5 font-mono text-xs text-muted">
                  <span class="as-typed">{w.section ? sectionLabel(w.section) : 'todas as seções'}{w.exclude.length ? ` · exceto: ${w.exclude.join(', ')}` : ''}</span> ·
                  {#if w.match_count === 0}
                    <span class="text-danger">nenhuma ocorrência ainda — revise os termos</span>
                  {:else}
                    {w.match_count} ocorrências · última {w.last_match_at?.slice(0, 10)}
                  {/if}
                </p>
              </div>
              <div class="flex items-center gap-2">
                <Badge label={w.active ? 'ativa' : 'inativa'} tone={w.active ? 'green' : 'gray'} />
                <Button variant="ghost" onclick={() => { editing = w; showForm = true; }}>editar</Button>
                <Button variant="ghost" onclick={() => toggle(w)}>{w.active ? 'desativar' : 'ativar'}</Button>
                <Button variant="ghost" onclick={() => (backfillingWatch = backfillingWatch === w ? undefined : w)}>rodar em edições anteriores</Button>
              </div>
            </div>
            {#if showForm && editing === w}
              <div class="mt-2">
                <Card>
                  <WatchForm {clients} watch={editing} {onsaved} />
                </Card>
              </div>
            {/if}
            {#if backfillingWatch === w}
              <div class="mt-2">
                <BackfillForm watch={w} oncancel={() => (backfillingWatch = undefined)} />
              </div>
            {/if}
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-sm text-muted">nenhuma busca ainda — crie uma.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-sm text-danger">não foi possível carregar as buscas.</p>{/snippet}
  </AsyncState>
</section>
