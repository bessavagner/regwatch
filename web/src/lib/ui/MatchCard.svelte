<script lang="ts">
  import type { Match } from '../api/types';
  import Card from './Card.svelte';
  import Badge from './Badge.svelte';

  let { match, children }: { match: Match; children?: import('svelte').Snippet } = $props();
  const tone = $derived(
    match.state === 'relevant' ? 'green' : match.state === 'dismissed' ? 'red' : 'blue',
  );
</script>

<Card>
  <div class="flex items-start justify-between gap-2">
    <p class="text-sm font-medium">{match.snippet}</p>
    <Badge label={match.state} tone={tone} />
  </div>
  {#if match.ai_summary}
    <p class="mt-2 text-sm text-muted">{match.ai_summary}</p>
  {/if}
  <div class="mt-2 flex flex-wrap gap-2 text-xs text-muted">
    {#if match.category}<Badge label={match.category} tone="gray" />{/if}
    <span>confidence {Math.round(match.confidence * 100)}%</span>
  </div>
  {#if children}<div class="mt-3">{@render children()}</div>{/if}
</Card>
