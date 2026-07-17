<script lang="ts">
  import { listWatches, listClients, updateWatch } from '../lib/api/resources';
  import { ApiError } from '../lib/api/client';
  import type { Client, Watch } from '../lib/api/types';
  import { navigate } from '../lib/router/router.svelte';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import Card from '../lib/ui/Card.svelte';
  import Button from '../lib/ui/Button.svelte';
  import Badge from '../lib/ui/Badge.svelte';
  import WatchForm from '../lib/ui/WatchForm.svelte';
  import BackfillForm from '../lib/ui/BackfillForm.svelte';

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
      toggleError = err instanceof ApiError ? err.detail : 'Could not update the watch';
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
    <h1 class="text-xl">Watches</h1>
    <Button disabled={clients.length === 0} onclick={() => { editing = undefined; showForm = true; }}>New watch</Button>
  </div>

  {#if status !== 'idle' && status !== 'loading' && clients.length === 0}
    <p class="mb-2 text-sm text-muted">
      Add a client first —
      <a href="/clients" class="text-accent underline" onclick={(e) => { e.preventDefault(); navigate('/clients'); }}>Clients</a>.
    </p>
  {/if}

  {#if showForm}
    <div class="mb-3">
      <Card>
        <WatchForm {clients} watch={editing} {onsaved} />
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
                <p class="as-typed text-sm font-medium text-ink">{w.terms.join(', ')}</p>
                <p class="mt-0.5 font-mono text-xs text-muted"><span class="as-typed">seção {w.section}{w.exclude.length ? ` · excl: ${w.exclude.join(', ')}` : ''}</span></p>
              </div>
              <div class="flex items-center gap-2">
                <Badge label={w.active ? 'active' : 'inactive'} tone={w.active ? 'green' : 'gray'} />
                <Button variant="ghost" onclick={() => { editing = w; showForm = true; }}>Edit</Button>
                <Button variant="ghost" onclick={() => toggle(w)}>{w.active ? 'Deactivate' : 'Activate'}</Button>
                <Button variant="ghost" onclick={() => (backfillingWatch = backfillingWatch === w ? undefined : w)}>Run on past editions</Button>
              </div>
            </div>
            {#if backfillingWatch === w}
              <div class="mt-2">
                <BackfillForm watch={w} oncancel={() => (backfillingWatch = undefined)} />
              </div>
            {/if}
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-sm text-muted">No watches yet — create one.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-sm text-danger">Could not load watches.</p>{/snippet}
  </AsyncState>
</section>
