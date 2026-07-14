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
    <h1 class="text-lg font-semibold">Clients</h1>
    <Button onclick={() => { editing = undefined; showForm = true; }}>New client</Button>
  </div>

  {#if showForm}
    <Card>
      <ClientForm client={editing} {onsaved} />
    </Card>
  {/if}

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="mt-3 space-y-2">
        {#each clients as c (c.id)}
          <li>
            <Card>
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium">{c.name}</p>
                  <p class="text-xs text-muted">{c.email || 'no digest recipient'}</p>
                </div>
                <div class="flex items-center gap-2">
                  {#if c.is_house}<Badge label="house" tone="blue" />{/if}
                  <Button variant="ghost" onclick={() => { editing = c; showForm = true; }}>Edit</Button>
                </div>
              </div>
            </Card>
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-muted">No clients yet — create one.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-red-600">Could not load clients.</p>{/snippet}
  </AsyncState>
</section>
