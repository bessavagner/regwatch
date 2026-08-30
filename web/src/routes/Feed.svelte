<script lang="ts">
  import {
    listMatches, listClients, listWatches, sendDigest, markRelevant, dismissMatch,
    bulkDismiss, type MatchParams, type BulkDismissBody,
  } from '../lib/api/resources';
  import type { Client, Match } from '../lib/api/types';
  import { ApiError } from '../lib/api/client';
  import { STATES, SECTIONS } from '../lib/constants';
  import { vocabulary, loadVocabulary } from '../lib/stores/vocabulary.svelte';
  import { queryFromView, viewFromQuery } from '../lib/feedFilters';
  import AsyncState from '../lib/ui/AsyncState.svelte';
  import MatchCard from '../lib/ui/MatchCard.svelte';
  import Button from '../lib/ui/Button.svelte';
  import TriageActions from '../lib/ui/TriageActions.svelte';
  import SignalDial from '../lib/ui/SignalDial.svelte';

  // Seed both the filters and the page from the address bar, so a shared or
  // bookmarked link opens the view it describes.
  const initialView = viewFromQuery(window.location.search);

  let status = $state<'idle' | 'loading' | 'loaded' | 'empty' | 'error'>('idle');
  let matches = $state<Match[]>([]);
  let count = $state(0);
  let totalPages = $state(1);
  // The server's page size, learned from the first response. Only the recount
  // in advanceAfterEmptying reads it, and that cannot run before a page has
  // loaded, so there is no reason to guess a default -- guessing 25 would
  // reintroduce the duplicated constant the new pagination class exists to avoid.
  let pageSize = $state(0);
  let page = $state(initialView.page);
  let hasNext = $state(false);
  let hasPrev = $state(false);
  let clients = $state<Client[]>([]);
  let clientsCount = $state(0);
  let watchesCount = $state(0);
  let actionError = $state('');
  let digestStatus = $state<'idle' | 'sending' | 'sent' | 'error'>('idle');

  // Keyboard triage. focused is an index into the rendered page, not a match id:
  // the list is re-fetched under it, so an id would go stale on every reload.
  let focused = $state(-1);
  // An array, not a Set: the order the operator picked in is the order the
  // request is sent in, which makes the confirmation legible.
  let selected = $state<number[]>([]);
  let pendingBulk = $state<
    { body: BulkDismissBody; visibleIds: number[]; label: string } | null
  >(null);

  let filters = $state<MatchParams>(initialView.filters);

  // Triage removed the last row on this page. Pagination is server-side over a
  // set that just shrank, so the rows that were on the next page have shifted
  // down into this one: reloading the current page number is what "advance"
  // means here, and asking for page + 1 would skip past a whole page of
  // matches. The one exception is a page that no longer exists -- empty the
  // last page and it stops being a page -- so step back to the last one that does.
  function advanceAfterEmptying() {
    const lastPage = Math.max(1, Math.ceil(count / Math.max(1, pageSize)));
    if (page > lastPage) {
      // Assigning page triggers the refetch effect. Replace rather than push:
      // the user did not navigate here, and a history entry they never chose
      // would make Back a no-op.
      page = lastPage;
      writeView('replace');
    } else {
      load();
    }
  }

  function applyUpdate(updated: Match) {
    matches = matches.map((m) => (m.id === updated.id ? updated : m));
    // Drop the card when it has left the set the server would return: either a
    // state filter is active and it no longer matches, or we are on the default
    // view, which excludes dismissed. Leaving it would show a row the next load
    // won't, which is a worse lie than never moving it.
    const goneFromSet = filters.state
      ? updated.state !== filters.state
      : updated.state === 'dismissed';
    if (goneFromSet) {
      matches = matches.filter((m) => m.id !== updated.id);
      // count is the size of the filtered set, not of this page: the match
      // really has left the set, so the header and the dial -- which both read
      // count -- must follow it down.
      count = Math.max(0, count - 1);
      if (matches.length === 0) advanceAfterEmptying();
    }
  }

  async function load() {
    status = 'loading';
    try {
      const res = await listMatches({ ...filters, page });
      matches = res.results;
      count = res.count;
      totalPages = res.total_pages;
      pageSize = res.page_size;
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
    loadVocabulary();
    listClients().then((r) => { clients = r.results; clientsCount = r.count; }).catch(() => (clients = []));
    listWatches().then((r) => (watchesCount = r.count)).catch(() => (watchesCount = 0));
  });

  // Back and forward restore the whole view. This assigns the state without
  // calling writeView -- the browser has already moved the history cursor, and
  // pushing here would strand the user in their own history.
  $effect(() => {
    const restore = () => {
      const view = viewFromQuery(window.location.search);
      filters = view.filters;
      page = view.page;
    };
    window.addEventListener('popstate', restore);
    return () => window.removeEventListener('popstate', restore);
  });

  // Refetch whenever a filter or the page changes.
  $effect(() => {
    // touch the reactive deps so the effect re-runs
    void [filters.client, filters.state, filters.section, filters.category, filters.date_from, filters.date_to, filters.ordering, page];
    load();
  });

  let canSendDigest = $derived(
    !!filters.client && !!filters.date_from && filters.date_from === filters.date_to,
  );

  async function sendDigestForDate() {
    if (!filters.client || !filters.date_from) return;
    digestStatus = 'sending';
    try {
      await sendDigest({ client: Number(filters.client), date: filters.date_from });
      digestStatus = 'sent';
    } catch (err) {
      digestStatus = 'error';
      actionError = err instanceof ApiError ? err.detail : 'não foi possível enviar o boletim';
    }
  }

  let focusedMatch = $derived(
    focused >= 0 && focused < matches.length ? matches[focused] : undefined,
  );
  let focusedAgency = $derived(focusedMatch?.act_detail.agency ?? '');

  // A checkbox is not a typing target: blocking the shortcuts after a click on
  // one would strand the hands between mouse and keyboard, which is the habit
  // this whole feature exists to remove.
  function isTypingTarget(target: EventTarget | null): boolean {
    const el = target as HTMLElement | null;
    if (!el || !el.tagName) return false;
    if (el.tagName === 'INPUT') return (el as HTMLInputElement).type !== 'checkbox';
    return el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable;
  }

  async function judge(fn: (id: number) => Promise<import('../lib/api/types').Match>) {
    const target = focusedMatch;
    if (!target) return;
    try {
      applyUpdate(await fn(target.id));
      // applyUpdate may have dropped the row; keep the cursor on the page.
      focused = Math.min(focused, matches.length - 1);
    } catch (err) {
      actionError = err instanceof ApiError ? err.detail : 'não foi possível concluir a ação';
    }
  }

  function toggleSelected(id: number) {
    selected = selected.includes(id) ? selected.filter((n) => n !== id) : [...selected, id];
    pendingBulk = null;
  }

  function onKeydown(e: KeyboardEvent) {
    // Leave the browser's own bindings alone, and let a text field have its letters.
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (isTypingTarget(e.target)) return;
    // The command palette is a modal: while it is up it owns the keyboard.
    if (document.querySelector('dialog[open]')) return;
    const key = e.key.toLowerCase();
    if (!['j', 'k', 'r', 'd', 'x'].includes(key)) return;
    if (matches.length === 0) return;
    e.preventDefault();
    if (key === 'j') focused = Math.min(focused + 1, matches.length - 1);
    else if (key === 'k') focused = Math.max(focused - 1, 0);
    else if (key === 'r') judge(markRelevant);
    else if (key === 'd') judge(dismissMatch);
    else if (key === 'x' && focusedMatch) toggleSelected(focusedMatch.id);
  }

  $effect(() => {
    window.addEventListener('keydown', onKeydown);
    return () => window.removeEventListener('keydown', onKeydown);
  });

  // Keep the focused row on screen. Optional call: jsdom has no scrollIntoView.
  $effect(() => {
    if (focused < 0) return;
    const el = document.querySelector(`li[data-row="${focused}"]`) as HTMLElement | null;
    el?.scrollIntoView?.({ block: 'nearest' });
  });

  function armSelectionDismiss() {
    const ids = [...selected];
    pendingBulk = {
      body: { ids },
      visibleIds: ids,
      label: `descartar ${ids.length} ocorrência${ids.length === 1 ? '' : 's'}`,
    };
  }

  function armAgencyDismiss() {
    const agency = focusedAgency;
    if (!agency) return;
    pendingBulk = {
      body: { agency },
      visibleIds: matches.filter((m) => m.act_detail.agency === agency).map((m) => m.id),
      label: `descartar todas de ${agency}`,
    };
  }

  async function confirmBulk() {
    const pending = pendingBulk;
    if (!pending) return;
    try {
      const { dismissed } = await bulkDismiss(pending.body, filters);
      applyBulkRemoval(pending.visibleIds, dismissed);
    } catch (err) {
      actionError = err instanceof ApiError ? err.detail : 'não foi possível descartar';
    } finally {
      pendingBulk = null;
    }
  }

  // The bulk twin of applyUpdate. The server may have dismissed rows that are
  // not on this page, so the visible rows and the count move by different
  // numbers: the rows we can see, and the total the server actually changed.
  function applyBulkRemoval(visibleIds: number[], dismissed: number) {
    selected = [];
    const leavesTheSet = filters.state ? filters.state !== 'dismissed' : true;
    if (leavesTheSet) {
      const gone = new Set(visibleIds);
      matches = matches.filter((m) => !gone.has(m.id));
      count = Math.max(0, count - dismissed);
    }
    focused = Math.min(focused, matches.length - 1);
    if (matches.length === 0) advanceAfterEmptying();
  }

  function writeView(mode: 'push' | 'replace') {
    const url = `${window.location.pathname}${queryFromView({ filters, page })}`;
    if (mode === 'push') window.history.pushState({}, '', url);
    else window.history.replaceState({}, '', url);
  }

  function setFilter<K extends keyof MatchParams>(key: K, value: MatchParams[K]) {
    filters = { ...filters, [key]: value };
    page = 1;
    digestStatus = 'idle';
    writeView('push');
  }

  function goToPage(next: number) {
    page = next;
    writeView('push');
  }
</script>

<section class="mx-auto max-w-2xl p-4">
  <div class="hero">
    <p class="eyebrow mb-2 text-xs opacity-60">00 · sinal</p>
    <div class="hero__body">
      <div>
        <h1 class="hero__title">faça a triagem do <em>sinal</em> de hoje.</h1>
        <p class="hero__lede">cada edição do Diário Oficial da União, conferida com as suas buscas duas vezes por dia útil — às 08:05 e às 13:00.</p>
      </div>
      <SignalDial value={count} />
    </div>
  </div>

  <div class="stat-row">
    <div class="stat">
      <span class="stat__value tabular-nums">{count}</span>
      <span class="stat__label">ocorrências</span>
    </div>
    <div class="stat">
      <span class="stat__value tabular-nums">{watchesCount}</span>
      <span class="stat__label">buscas</span>
    </div>
    <div class="stat">
      <span class="stat__value tabular-nums">{clientsCount}</span>
      <span class="stat__label">clientes</span>
    </div>
  </div>

  <div class="mb-4 grid grid-cols-2 gap-3 rounded-card border border-rule bg-paper-2/50 p-3 sm:grid-cols-3">
    <label class="text-sm text-ink-2">cliente
      <select class="mt-1 field" value={String(filters.client ?? '')} onchange={(e) => setFilter('client', e.currentTarget.value)}>
        <option value="">todos</option>
        <!-- String(c.id): Svelte matches the select's value against the raw
             option expression, so a numeric id would never equal a filter
             value read out of the query string. -->
        {#each clients as c}<option value={String(c.id)}>{c.name}</option>{/each}
      </select>
    </label>
    <label class="text-sm text-ink-2">situação
      <select class="mt-1 field" value={filters.state ?? ''} onchange={(e) => setFilter('state', e.currentTarget.value)}>
        <option value="">ativas</option>
        {#each STATES as s}<option value={s.value}>{s.label}</option>{/each}
      </select>
    </label>
    <label class="text-sm text-ink-2">seção
      <select class="mt-1 field" value={filters.section ?? ''} onchange={(e) => setFilter('section', e.currentTarget.value)}>
        <option value="">todas</option>
        {#each SECTIONS as s}<option value={s.value}>{s.label}</option>{/each}
      </select>
    </label>
    <label class="text-sm text-ink-2">categoria
      <select class="mt-1 field" value={filters.category ?? ''} onchange={(e) => setFilter('category', e.currentTarget.value)}>
        <option value="">todas</option>
        {#each vocabulary.categories as c}<option value={c.value}>{c.label}</option>{/each}
      </select>
    </label>
    <label class="text-sm text-ink-2">de
      <input type="date" class="mt-1 field" value={filters.date_from ?? ''} onchange={(e) => setFilter('date_from', e.currentTarget.value)} />
    </label>
    <label class="text-sm text-ink-2">até
      <input type="date" class="mt-1 field" value={filters.date_to ?? ''} onchange={(e) => setFilter('date_to', e.currentTarget.value)} />
    </label>
  </div>

  <div class="mb-3 flex items-center justify-between text-sm text-muted">
    <span class="font-mono tabular-nums">{count} ocorrência{count === 1 ? '' : 's'}</span>
    <label>ordenar
      <select class="ml-1 field inline-flex w-auto min-h-9" value={filters.ordering ?? ''} onchange={(e) => setFilter('ordering', e.currentTarget.value)}>
        <option value="">mais recentes</option>
        <option value="signal">mais sinais</option>
        <option value="rank">maior relevância</option>
      </select>
    </label>
  </div>

  {#if actionError}<p role="alert" class="mb-2 text-sm text-danger">{actionError}</p>{/if}

  {#if pendingBulk}
    <div class="bulk-bar" role="group" aria-label="confirmar descarte em lote">
      <span class="bulk-bar__label">{pendingBulk.label}?</span>
      <Button variant="primary" onclick={confirmBulk}>confirmar</Button>
      <Button variant="ghost" onclick={() => (pendingBulk = null)}>cancelar</Button>
    </div>
  {:else if selected.length || focusedAgency}
    <div class="bulk-bar" role="group" aria-label="ações em lote">
      {#if selected.length}
        <span class="bulk-bar__label">
          {selected.length} selecionada{selected.length === 1 ? '' : 's'}
        </span>
        <Button variant="ghost" onclick={armSelectionDismiss}>descartar selecionadas</Button>
        <Button variant="ghost" onclick={() => (selected = [])}>limpar seleção</Button>
      {/if}
      {#if focusedAgency}
        <Button variant="ghost" onclick={armAgencyDismiss}>descartar todas desta origem</Button>
      {/if}
    </div>
  {/if}

  {#if canSendDigest}
    <div class="mb-3">
      <Button variant="ghost" disabled={digestStatus === 'sending'} onclick={sendDigestForDate}>
        {digestStatus === 'sent' ? 'boletim enviado' : 'enviar boletim desta data'}
      </Button>
    </div>
  {/if}

  <AsyncState state={status}>
    {#snippet loaded()}
      <ul class="rows">
        {#each matches as match, i (match.id)}
          <li
            class="row row--triage reveal"
            class:is-focused={i === focused}
            class:is-selected={selected.includes(match.id)}
            style="--i: {i}"
            data-row={i}
            aria-current={i === focused ? 'true' : undefined}
          >
            <label class="row__select">
              <input
                type="checkbox"
                class="accent-accent"
                checked={selected.includes(match.id)}
                onchange={() => toggleSelected(match.id)}
              />
              <span class="sr-only">selecionar {match.act_detail.title}</span>
            </label>
            <div class="row__content">
              <MatchCard {match}>
                {#snippet children()}
                  <TriageActions {match} onchange={applyUpdate} onerror={(m) => (actionError = m)} />
                {/snippet}
              </MatchCard>
            </div>
          </li>
        {/each}
      </ul>
    {/snippet}
    {#snippet empty()}<p class="p-4 text-sm text-muted">nenhuma ocorrência para estes filtros.</p>{/snippet}
    {#snippet error()}<p role="alert" class="p-4 text-sm text-danger">não foi possível carregar as ocorrências.</p>{/snippet}
  </AsyncState>

  <div class="mt-4 flex items-center justify-between">
    <Button variant="ghost" disabled={!hasPrev} onclick={() => goToPage(page - 1)}>anterior</Button>
    <span class="font-mono text-sm tabular-nums text-muted">página {page} de {totalPages}</span>
    <Button variant="ghost" disabled={!hasNext} onclick={() => goToPage(page + 1)}>próxima</Button>
  </div>
</section>
