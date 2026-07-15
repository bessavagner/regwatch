<script lang="ts">
  import type { Match } from '../api/types';
  import Badge from './Badge.svelte';

  let { match, children }: { match: Match; children?: import('svelte').Snippet } = $props();
  const tone = $derived(
    match.state === 'relevant' ? 'green' : match.state === 'dismissed' ? 'red' : 'blue',
  );
</script>

<div class="flex items-start justify-between gap-2">
  <p class="as-typed text-sm font-medium text-ink">{match.snippet}</p>
  <Badge label={match.state} tone={tone} />
</div>
{#if match.ai_summary}
  <p class="as-typed mt-2 text-sm text-muted">{match.ai_summary}</p>
{/if}
<div class="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted">
  {#if match.category}<Badge label={match.category} tone="gray" />{/if}
  <span class="font-mono tabular-nums">confidence {Math.round(match.confidence * 100)}%</span>
</div>
{#if children}<div class="mt-3">{@render children()}</div>{/if}
