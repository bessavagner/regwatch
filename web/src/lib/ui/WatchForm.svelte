<script lang="ts">
  import { untrack } from 'svelte';
  import type { Client, Watch, WatchGroup, WatchTermKind } from '../api/types';
  import { createWatch, updateWatch, type WatchBody } from '../api/resources';
  import { ApiError } from '../api/client';
  import { SECTIONS } from '../constants';
  import Button from './Button.svelte';

  let { clients, watch, onsaved }: { clients: Client[]; watch?: Watch; onsaved: (w: Watch) => void } = $props();

  type Row = { aliases: string; kind: WatchTermKind };

  const toRows = (groups: WatchGroup[] | undefined): Row[] => {
    const rows = (groups ?? []).map((g) => ({
      aliases: g.terms.map((t) => t.text).join(', '),
      kind: (g.terms[0]?.kind ?? 'entity') as WatchTermKind,
    }));
    return rows.length ? rows : [{ aliases: '', kind: 'entity' }];
  };

  // Local editable copy seeded once from props; intentionally not kept in sync
  // with prop changes (this is a one-shot form default, not a live mirror).
  let client = $state(untrack(() => watch?.client ?? clients[0]?.id ?? 0));
  let rows = $state<Row[]>(untrack(() => toRows(watch?.groups)));
  let excludeText = $state(untrack(() => (watch?.exclude ?? []).join(', ')));
  let section = $state(untrack(() => watch?.section ?? ''));
  let active = $state(untrack(() => watch?.active ?? true));
  let fieldErrors = $state<Record<string, string[]>>({});

  const split = (s: string) => s.split(',').map((t) => t.trim()).filter(Boolean);

  const addGroup = () => { rows = [...rows, { aliases: '', kind: 'entity' }]; };
  const removeGroup = (i: number) => { rows = rows.filter((_, n) => n !== i); };

  async function save(e: SubmitEvent) {
    e.preventDefault();
    fieldErrors = {};
    const groups: WatchGroup[] = rows
      .map((r) => ({ terms: split(r.aliases).map((text) => ({ text, kind: r.kind })) }))
      .filter((g) => g.terms.length > 0);
    const body: WatchBody = {
      client: Number(client),
      groups,
      exclude: split(excludeText),
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

  <p class="text-sm">All groups must match. Aliases inside a group are alternatives.</p>
  {#each rows as row, i}
    <div class="flex items-end gap-2">
      <label class="block flex-1 text-sm">Aliases for group {i + 1} (comma-separated)
        <input class="mt-1 field" bind:value={row.aliases} />
      </label>
      <label class="block text-sm">Match kind for group {i + 1}
        <select class="mt-1 field" bind:value={row.kind}>
          <option value="entity">name (exact)</option>
          <option value="concept">word (stemmed)</option>
        </select>
      </label>
      {#if rows.length > 1}
        <Button type="button" onclick={() => removeGroup(i)}>Remove group {i + 1}</Button>
      {/if}
    </div>
  {/each}
  <Button type="button" onclick={addGroup}>Add group</Button>
  {#if fieldErrors.groups}<p role="alert" class="text-sm text-danger">{fieldErrors.groups.join(' ')}</p>{/if}

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
