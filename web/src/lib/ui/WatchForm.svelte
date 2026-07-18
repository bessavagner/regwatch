<script lang="ts">
  import { untrack } from 'svelte';
  import type { Client, Watch } from '../api/types';
  import { createWatch, updateWatch, type WatchBody } from '../api/resources';
  import { ApiError } from '../api/client';
  import { SECTIONS } from '../constants';
  import Button from './Button.svelte';

  let { clients, watch, onsaved }: { clients: Client[]; watch?: Watch; onsaved: (w: Watch) => void } = $props();

  // Local editable copy seeded once from props; intentionally not kept in sync
  // with prop changes (this is a one-shot form default, not a live mirror).
  let client = $state(untrack(() => watch?.client ?? clients[0]?.id ?? 0));
  let termsText = $state(untrack(() => (watch?.terms ?? []).join(', ')));
  let excludeText = $state(untrack(() => (watch?.exclude ?? []).join(', ')));
  let matchMode = $state<'all' | 'any'>(untrack(() => watch?.match_mode ?? 'all'));
  let section = $state(untrack(() => watch?.section ?? ''));
  let active = $state(untrack(() => watch?.active ?? true));
  let fieldErrors = $state<Record<string, string[]>>({});

  const split = (s: string) => s.split(',').map((t) => t.trim()).filter(Boolean);

  async function save(e: SubmitEvent) {
    e.preventDefault();
    fieldErrors = {};
    const body: WatchBody = {
      client: Number(client),
      terms: split(termsText),
      exclude: split(excludeText),
      match_mode: matchMode,
      section,
      active,
    };
    try {
      const result = watch ? await updateWatch(watch.id, body) : await createWatch(body);
      onsaved(result);
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) fieldErrors = err.fields;
      else fieldErrors = { _: [err instanceof ApiError ? err.detail : 'save failed'] };
    }
  }
</script>

<form onsubmit={save} class="space-y-2">
  <label class="block text-sm">Client
    <select class="mt-1 field" bind:value={client}>
      {#each clients as c}<option value={c.id}>{c.name}</option>{/each}
    </select>
  </label>
  <label class="block text-sm">Terms (comma-separated)
    <input class="mt-1 field" bind:value={termsText} />
  </label>
  {#if fieldErrors.terms}<p role="alert" class="text-sm text-danger">{fieldErrors.terms.join(' ')}</p>{/if}
  <label class="block text-sm">Match
    <select class="mt-1 field" bind:value={matchMode}>
      <option value="all">all terms must appear</option>
      <option value="any">any term may appear</option>
    </select>
  </label>
  {#if fieldErrors.match_mode}<p role="alert" class="text-sm text-danger">{fieldErrors.match_mode.join(' ')}</p>{/if}
  <label class="block text-sm">Exclude (comma-separated)
    <input class="mt-1 field" bind:value={excludeText} />
  </label>
  <label class="block text-sm">Section
    <select class="mt-1 field" bind:value={section}>
      <option value="">all sections</option>
      {#each SECTIONS as s}<option value={s.value}>{s.label}</option>{/each}
    </select>
  </label>
  <label class="flex items-center gap-2 text-sm"><input type="checkbox" class="accent-accent" bind:checked={active} /> Active</label>
  {#if fieldErrors.client}<p role="alert" class="text-sm text-danger">{fieldErrors.client.join(' ')}</p>{/if}
  {#if fieldErrors._}<p role="alert" class="text-sm text-danger">{fieldErrors._.join(' ')}</p>{/if}
  <Button type="submit">Save</Button>
</form>
