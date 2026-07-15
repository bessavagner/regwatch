<script lang="ts">
  import { listDigests, listClients } from '../lib/api/resources';
  import type { Client, Digest } from '../lib/api/types';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import Badge from '../lib/ui/Badge.svelte';

  let status = $state<'idle' | 'loading' | 'loaded' | 'empty' | 'error'>('idle');
  let digests = $state<Digest[]>([]);
  let clients = $state<Client[]>([]);
  let client = $state('');

  async function load() {
    status = 'loading';
    try {
      const res = await listDigests(client || undefined);
      digests = res.results;
      status = res.results.length ? 'loaded' : 'empty';
    } catch {
      status = 'error';
    }
  }

  $effect(() => {
    listClients().then((r) => (clients = r.results)).catch(() => (clients = []));
  });
  $effect(() => { void client; load(); });

  const clientName = (id: number) => clients.find((c) => c.id === id)?.name ?? `#${id}`;
</script>

<section class="mx-auto max-w-2xl p-4">
  <div class="mb-3 flex items-center justify-between">
    <h1 class="text-xl">Digest history</h1>
    <label class="text-sm text-ink-2">Client
      <select class="ml-1 field inline-flex w-auto min-h-9" bind:value={client}>
        <option value="">all</option>
        {#each clients as c}<option value={c.id}>{c.name}</option>{/each}
      </select>
    </label>
  </div>

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="rows">
        {#each digests as d, i (d.id)}
          <li class="row reveal" style="--i: {i}">
            <div class="flex items-center justify-between gap-2">
              <p class="font-mono text-sm tabular-nums text-ink"><span>{d.date}</span> · <span class="as-typed">{clientName(d.client)}</span></p>
              <Badge label={d.sent ? 'sent' : 'not sent'} tone={d.sent ? 'green' : 'gray'} />
            </div>
            <pre class="as-typed mt-2 whitespace-pre-wrap font-mono text-sm text-muted">{d.body}</pre>
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-sm text-muted">No digests yet.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-sm text-danger">Could not load digests.</p>{/snippet}
  </AsyncState>
</section>
