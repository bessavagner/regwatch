<script lang="ts">
  import { listClients } from '../lib/api/resources';
  import type { Client } from '../lib/api/types';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import Card from '../lib/ui/Card.svelte';
  import Button from '../lib/ui/Button.svelte';
  import Badge from '../lib/ui/Badge.svelte';
  import ClientForm from '../lib/ui/ClientForm.svelte';

  let status = $state<'idle' | 'loading' | 'loaded' | 'empty' | 'error'>('idle');
  let clients = $state<Client[]>([]);
  let showForm = $state(false);
  let editing = $state<Client | undefined>(undefined);

  async function load() {
    status = 'loading';
    try {
      const c = await listClients();
      clients = c.results;
      status = c.results.length ? 'loaded' : 'empty';
    } catch {
      status = 'error';
    }
  }

  $effect(() => { load(); });

  function onsaved(c: Client) {
    const exists = clients.some((x) => x.id === c.id);
    clients = exists ? clients.map((x) => (x.id === c.id ? c : x)) : [...clients, c];
    showForm = false;
    editing = undefined;
    if (status === 'empty') status = 'loaded';
  }
</script>

<section class="mx-auto max-w-2xl p-4">
  <div class="mb-3 flex items-center justify-between">
    <h1 class="text-xl">clientes</h1>
    <Button onclick={() => { editing = undefined; showForm = true; }}>novo cliente</Button>
  </div>

  {#if showForm && !editing}
    <div class="mb-3">
      <Card>
        <ClientForm {onsaved} />
      </Card>
    </div>
  {/if}

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="rows">
        {#each clients as c, i (c.id)}
          <li class="row reveal" style="--i: {i}">
            <div class="flex items-center justify-between gap-2">
              <div>
                <p class="as-typed text-sm font-medium text-ink">{c.name}</p>
                <p class="as-typed mt-0.5 text-xs text-muted">{c.email || 'sem destinatário de boletim'}</p>
              </div>
              <div class="flex items-center gap-2">
                {#if c.is_house}<Badge label="interno" tone="blue" />{/if}
                <Button variant="ghost" onclick={() => { editing = c; showForm = true; }}>editar</Button>
              </div>
            </div>
            {#if showForm && editing === c}
              <div class="mt-2">
                <Card>
                  <ClientForm client={editing} {onsaved} />
                </Card>
              </div>
            {/if}
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-sm text-muted">nenhum cliente ainda — crie um.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-sm text-danger">não foi possível carregar os clientes.</p>{/snippet}
  </AsyncState>
</section>
