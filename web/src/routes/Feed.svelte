<script lang="ts">
  import { listMatches, listClients, type MatchParams } from '../lib/api/resources';
  import type { Client, Match } from '../lib/api/types';
  import { STATES, SECTIONS, CATEGORY_SEED } from '../lib/constants';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import MatchCard from '../lib/ui/MatchCard.svelte';
  import Button from '../lib/ui/Button.svelte';
  import TriageActions from '../lib/ui/TriageActions.svelte';

  let status = $state<'idle' | 'loading' | 'loaded' | 'empty' | 'error'>('idle');
  let matches = $state<Match[]>([]);
  let count = $state(0);
  let page = $state(1);
  let hasNext = $state(false);
  let hasPrev = $state(false);
  let clients = $state<Client[]>([]);
  let actionError = $state('');

  let filters = $state<MatchParams>({ ordering: '' });

  function applyUpdate(updated: Match) {
    matches = matches.map((m) => (m.id === updated.id ? updated : m));
    // If a state filter is active and no longer matches, drop it from view.
    if (filters.state && updated.state !== filters.state) {
      matches = matches.filter((m) => m.id !== updated.id);
    }
  }

  async function load() {
    status = 'loading';
    try {
      const res = await listMatches({ ...filters, page });
      matches = res.results;
      count = res.count;
      status = res.results.length ? 'loaded' : 'empty';
      hasNext = res.next !== null;
      hasPrev = res.previous !== null;
    } catch {
      status = 'error';
      hasNext = false;
      hasPrev = false;
    }
  }

  $effect(() => {
    listClients().then((r) => (clients = r.results)).catch(() => (clients = []));
  });

  // Refetch whenever a filter or the page changes.
  $effect(() => {
    // touch the reactive deps so the effect re-runs
    void [filters.client, filters.state, filters.section, filters.category, filters.date_from, filters.date_to, filters.ordering, page];
    load();
  });

  function setFilter<K extends keyof MatchParams>(key: K, value: MatchParams[K]) {
    filters = { ...filters, [key]: value };
    page = 1;
  }
</script>

<section class="mx-auto max-w-2xl p-4">
  <h1 class="mb-3 text-lg font-semibold">Triage</h1>

  <div class="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
    <label class="text-sm">Client
      <select class="mt-1 w-full rounded border px-2 py-1" onchange={(e) => setFilter('client', e.currentTarget.value)}>
        <option value="">All</option>
        {#each clients as c}<option value={c.id}>{c.name}</option>{/each}
      </select>
    </label>
    <label class="text-sm">State
      <select class="mt-1 w-full rounded border px-2 py-1" onchange={(e) => setFilter('state', e.currentTarget.value)}>
        <option value="">All</option>
        {#each STATES as s}<option value={s.value}>{s.label}</option>{/each}
      </select>
    </label>
    <label class="text-sm">Section
      <select class="mt-1 w-full rounded border px-2 py-1" onchange={(e) => setFilter('section', e.currentTarget.value)}>
        <option value="">All</option>
        {#each SECTIONS as s}<option value={s.value}>{s.label}</option>{/each}
      </select>
    </label>
    <label class="text-sm">Category
      <input list="cats" class="mt-1 w-full rounded border px-2 py-1" onchange={(e) => setFilter('category', e.currentTarget.value)} />
      <datalist id="cats">{#each CATEGORY_SEED as c}<option value={c}></option>{/each}</datalist>
    </label>
    <label class="text-sm">From
      <input type="date" class="mt-1 w-full rounded border px-2 py-1" onchange={(e) => setFilter('date_from', e.currentTarget.value)} />
    </label>
    <label class="text-sm">To
      <input type="date" class="mt-1 w-full rounded border px-2 py-1" onchange={(e) => setFilter('date_to', e.currentTarget.value)} />
    </label>
  </div>

  <div class="mb-3 flex items-center justify-between text-sm text-muted">
    <span>{count} match{count === 1 ? '' : 'es'}</span>
    <label>Order
      <select class="ml-1 rounded border px-2 py-1" onchange={(e) => setFilter('ordering', e.currentTarget.value)}>
        <option value="">Most recent</option>
        <option value="rank">Highest rank</option>
      </select>
    </label>
  </div>

  {#if actionError}<p role="alert" class="mb-2 text-sm text-red-600">{actionError}</p>{/if}

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="space-y-3">
        {#each matches as match (match.id)}
          <li>
            <MatchCard {match}>
              {#snippet children()}
                <TriageActions {match} onchange={applyUpdate} onerror={(m) => (actionError = m)} />
              {/snippet}
            </MatchCard>
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-muted">No matches for these filters.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-red-600">Could not load matches.</p>{/snippet}
  </AsyncState>

  <div class="mt-4 flex items-center justify-between">
    <Button variant="ghost" disabled={!hasPrev} onclick={() => (page -= 1)}>Prev</Button>
    <span class="text-sm text-muted">Page {page}</span>
    <Button variant="ghost" disabled={!hasNext} onclick={() => (page += 1)}>Next</Button>
  </div>
</section>
