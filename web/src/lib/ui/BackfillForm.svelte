<script lang="ts">
  import type { Watch } from '../api/types';
  import { backfillWatch, type BackfillBody, type BackfillResult } from '../api/resources';
  import { ApiError } from '../api/client';
  import { navigate } from '../router/router.svelte';
  import Button from './Button.svelte';

  let { watch, oncancel }: { watch: Watch; oncancel: () => void } = $props();

  const today = new Date().toISOString().slice(0, 10);

  let dateFrom = $state('');
  let dateTo = $state('');
  let fieldErrors = $state<Record<string, string[]>>({});
  let running = $state(false);
  let result = $state<BackfillResult | undefined>(undefined);

  function maxDateTo(): string {
    if (!dateFrom) return today;
    const capped = new Date(`${dateFrom}T00:00:00`);
    capped.setDate(capped.getDate() + 6);
    const cappedIso = capped.toISOString().slice(0, 10);
    return cappedIso < today ? cappedIso : today;
  }

  async function run(e: SubmitEvent) {
    e.preventDefault();
    fieldErrors = {};
    if (!dateFrom || !dateTo) {
      fieldErrors = { _: ['Both dates are required.'] };
      return;
    }
    const body: BackfillBody = { date_from: dateFrom, date_to: dateTo };
    running = true;
    result = undefined;
    try {
      result = await backfillWatch(watch.id, body);
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) fieldErrors = err.fields;
      else fieldErrors = { _: [err instanceof ApiError ? err.detail : 'backfill failed'] };
    } finally {
      running = false;
    }
  }

  function viewInFeed() {
    navigate(`/feed?client=${watch.client}&date_from=${dateFrom}&date_to=${dateTo}`);
  }
</script>

<form onsubmit={run} novalidate class="space-y-2">
  <label class="block text-sm">From
    <input type="date" class="mt-1 field" bind:value={dateFrom} max={today} required />
  </label>
  <label class="block text-sm">To
    <input type="date" class="mt-1 field" bind:value={dateTo} min={dateFrom || undefined} max={maxDateTo()} required />
  </label>
  {#if fieldErrors.date_from}<p role="alert" class="text-sm text-danger">{fieldErrors.date_from.join(' ')}</p>{/if}
  {#if fieldErrors.date_to}<p role="alert" class="text-sm text-danger">{fieldErrors.date_to.join(' ')}</p>{/if}
  {#if fieldErrors.non_field_errors}<p role="alert" class="text-sm text-danger">{fieldErrors.non_field_errors.join(' ')}</p>{/if}
  {#if fieldErrors._}<p role="alert" class="text-sm text-danger">{fieldErrors._.join(' ')}</p>{/if}
  {#if result}
    <p class="text-sm text-ink-2">
      {result.editions} editions, {result.acts} acts, {result.matches} matches, {result.enriched} enriched.
      {#if result.skipped_dates.length}Skipped: {result.skipped_dates.join(', ')}.{/if}
    </p>
  {/if}
  <div class="flex gap-2">
    {#if result}
      <Button onclick={viewInFeed}>View in feed</Button>
    {:else}
      <Button type="submit" loading={running}>Run</Button>
    {/if}
    <Button variant="ghost" onclick={oncancel}>Cancel</Button>
  </div>
</form>
