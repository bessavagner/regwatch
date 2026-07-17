<script lang="ts">
  import type { Watch } from '../api/types';
  import { backfillWatch, type BackfillBody } from '../api/resources';
  import { ApiError } from '../api/client';
  import { navigate } from '../router/router.svelte';
  import Button from './Button.svelte';

  let { watch, oncancel }: { watch: Watch; oncancel: () => void } = $props();

  const today = new Date().toISOString().slice(0, 10);

  let dateFrom = $state('');
  let dateTo = $state('');
  let fieldErrors = $state<Record<string, string[]>>({});

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
    try {
      await backfillWatch(watch.id, body);
      navigate(`/feed?client=${watch.client}&date_from=${dateFrom}&date_to=${dateTo}`);
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) fieldErrors = err.fields;
      else fieldErrors = { _: [err instanceof ApiError ? err.detail : 'backfill failed'] };
    }
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
  <div class="flex gap-2">
    <Button type="submit">Run</Button>
    <Button variant="ghost" onclick={oncancel}>Cancel</Button>
  </div>
</form>
