<script lang="ts">
  import type { Match } from '../api/types';
  import { brDate } from '../format';
  import Badge from './Badge.svelte';

  let { match, children }: { match: Match; children?: import('svelte').Snippet } = $props();
  const tone = $derived(
    match.state === 'relevant' ? 'green' : match.state === 'dismissed' ? 'red' : 'blue',
  );
</script>

<div class="flex items-start justify-between gap-2">
  <div class="min-w-0">
    <p class="as-typed truncate text-sm font-medium text-ink">{match.act_detail.title}</p>
    <p class="as-typed mt-0.5 text-xs text-muted">
      {match.client_name} · {brDate(match.act_detail.date)} · {match.act_detail.section}
      {#if match.act_detail.agency} · {match.act_detail.agency}{/if}
    </p>
  </div>
  <Badge label={match.state} tone={tone} />
</div>

{#if match.ai_summary}
  <p class="as-typed mt-2 text-sm text-muted">{match.ai_summary}</p>
{:else}
  <p class="mt-2 text-sm text-muted">resumo indisponível — mostrando o texto do ato</p>
  <p class="as-typed mt-1 text-sm text-muted">{match.snippet}</p>
{/if}

{#if match.matched_terms.length}
  <p class="mt-2 text-xs text-muted">
    encontrado por <span class="as-typed font-medium text-ink"
      >{match.matched_terms.join(', ')}</span
    >
  </p>
{/if}

<div class="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
  {#if match.category}<Badge label={match.category_label} tone="gray" />{/if}
  {#if match.act_detail.source_url}
    <a
      class="underline"
      href={match.act_detail.source_url}
      target="_blank"
      rel="noopener noreferrer">source</a
    >
  {/if}
</div>
{#if children}<div class="mt-3">{@render children()}</div>{/if}
