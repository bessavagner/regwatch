<script lang="ts">
  import { listMatches, listClients, listWatches, type MatchParams } from '../lib/api/resources';
  import type { Client, Match } from '../lib/api/types';
  import { STATES, SECTIONS, CATEGORY_SEED } from '../lib/constants';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import MatchCard from '../lib/ui/MatchCard.svelte';
  import Button from '../lib/ui/Button.svelte';
  import TriageActions from '../lib/ui/TriageActions.svelte';
  import SignalDial from '../lib/ui/SignalDial.svelte';

  let status = $state<'idle' | 'loading' | 'loaded' | 'empty' | 'error'>('idle');
  let matches = $state<Match[]>([]);
  let count = $state(0);
  let page = $state(1);
  let hasNext = $state(false);
  let hasPrev = $state(false);
  let clients = $state<Client[]>([]);
  let clientsCount = $state(0);
  let watchesCount = $state(0);
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
    listClients().then((r) => { clients = r.results; clientsCount = r.count; }).catch(() => (clients = []));
    listWatches().then((r) => (watchesCount = r.count)).catch(() => (watchesCount = 0));
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
  <div class="hero">
    <p class="eyebrow mb-2 text-xs opacity-60">00 · signal</p>
    <div class="hero__body">
      <div>
        <h1 class="hero__title">built to <em>watch</em>,&nbsp;in real time.</h1>
        <p class="hero__lede">every new Diário Oficial da União publication, checked against your watches the moment it lands.</p>
      </div>
      <SignalDial value={count} />
    </div>
  </div>

  <div class="stat-row">
    <div class="stat">
      <span class="stat__value tabular-nums">{count}</span>
      <span class="stat__label">matches</span>
    </div>
    <div class="stat">
      <span class="stat__value tabular-nums">{watchesCount}</span>
      <span class="stat__label">watches</span>
    </div>
    <div class="stat">
      <span class="stat__value tabular-nums">{clientsCount}</span>
      <span class="stat__label">clients</span>
    </div>
  </div>

  <div class="mb-4 grid grid-cols-2 gap-3 rounded-card border border-rule bg-paper-2/50 p-3 sm:grid-cols-3">
    <label class="text-sm text-ink-2">Client
      <select class="mt-1 field" onchange={(e) => setFilter('client', e.currentTarget.value)}>
        <option value="">all</option>
        {#each clients as c}<option value={c.id}>{c.name}</option>{/each}
      </select>
    </label>
    <label class="text-sm text-ink-2">State
      <select class="mt-1 field" onchange={(e) => setFilter('state', e.currentTarget.value)}>
        <option value="">all</option>
        {#each STATES as s}<option value={s.value}>{s.label}</option>{/each}
      </select>
    </label>
    <label class="text-sm text-ink-2">Section
      <select class="mt-1 field" onchange={(e) => setFilter('section', e.currentTarget.value)}>
        <option value="">all</option>
        {#each SECTIONS as s}<option value={s.value}>{s.label}</option>{/each}
      </select>
    </label>
    <label class="text-sm text-ink-2">Category
      <input list="cats" class="mt-1 field" onchange={(e) => setFilter('category', e.currentTarget.value)} />
      <datalist id="cats">{#each CATEGORY_SEED as c}<option value={c}></option>{/each}</datalist>
    </label>
    <label class="text-sm text-ink-2">From
      <input type="date" class="mt-1 field" onchange={(e) => setFilter('date_from', e.currentTarget.value)} />
    </label>
    <label class="text-sm text-ink-2">To
      <input type="date" class="mt-1 field" onchange={(e) => setFilter('date_to', e.currentTarget.value)} />
    </label>
  </div>

  <div class="mb-3 flex items-center justify-between text-sm text-muted">
    <span class="font-mono tabular-nums">{count} match{count === 1 ? '' : 'es'}</span>
    <label>Order
      <select class="ml-1 field inline-flex w-auto min-h-9" onchange={(e) => setFilter('ordering', e.currentTarget.value)}>
        <option value="">most recent</option>
        <option value="rank">highest rank</option>
      </select>
    </label>
  </div>

  {#if actionError}<p role="alert" class="mb-2 text-sm text-danger">{actionError}</p>{/if}

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="rows">
        {#each matches as match, i (match.id)}
          <li class="row reveal" style="--i: {i}">
            <MatchCard {match}>
              {#snippet children()}
                <TriageActions {match} onchange={applyUpdate} onerror={(m) => (actionError = m)} />
              {/snippet}
            </MatchCard>
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-sm text-muted">No matches for these filters.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-sm text-danger">Could not load matches.</p>{/snippet}
  </AsyncState>

  <div class="mt-4 flex items-center justify-between">
    <Button variant="ghost" disabled={!hasPrev} onclick={() => (page -= 1)}>Prev</Button>
    <span class="font-mono text-sm tabular-nums text-muted">Page {page}</span>
    <Button variant="ghost" disabled={!hasNext} onclick={() => (page += 1)}>Next</Button>
  </div>
</section>
