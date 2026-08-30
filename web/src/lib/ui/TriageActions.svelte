<script lang="ts">
  import type { Match } from '../api/types';
  import { markRelevant, dismissMatch } from '../api/resources';
  import { ApiError } from '../api/client';
  import Button from './Button.svelte';

  let {
    match,
    onchange,
    onerror,
  }: { match: Match; onchange: (m: Match) => void; onerror: (msg: string) => void } = $props();

  let busy = $state(false);

  async function act(fn: (id: number) => Promise<Match>) {
    busy = true;
    try {
      const updated = await fn(match.id);
      onchange(updated);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : 'não foi possível concluir a ação';
      onerror(msg);
    } finally {
      busy = false;
    }
  }
</script>

<div class="flex gap-2">
  <Button variant="primary" disabled={busy} onclick={() => act(markRelevant)}>relevante</Button>
  <Button variant="ghost" disabled={busy} onclick={() => act(dismissMatch)}>arquivar</Button>
</div>
