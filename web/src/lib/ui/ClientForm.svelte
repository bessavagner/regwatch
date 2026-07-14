<script lang="ts">
  import { untrack } from 'svelte';
  import type { Client } from '../api/types';
  import { createClient, updateClient, type ClientBody } from '../api/resources';
  import { ApiError } from '../api/client';
  import Button from './Button.svelte';

  let { client, onsaved }: { client?: Client; onsaved: (c: Client) => void } = $props();

  // Local editable copy seeded once from props; intentionally not kept in sync
  // with prop changes (this is a one-shot form default, not a live mirror).
  let name = $state(untrack(() => client?.name ?? ''));
  let email = $state(untrack(() => client?.email ?? ''));
  let isHouse = $state(untrack(() => client?.is_house ?? false));
  let fieldErrors = $state<Record<string, string[]>>({});

  async function save(e: SubmitEvent) {
    e.preventDefault();
    fieldErrors = {};
    const body: ClientBody = { name, email, is_house: isHouse };
    try {
      const result = client ? await updateClient(client.id, body) : await createClient(body);
      onsaved(result);
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) fieldErrors = err.fields;
      else fieldErrors = { _: [err instanceof ApiError ? err.detail : 'save failed'] };
    }
  }
</script>

<form onsubmit={save} class="space-y-2">
  <label class="block text-sm">Name
    <input class="mt-1 w-full rounded border px-2 py-1" bind:value={name} />
  </label>
  {#if fieldErrors.name}<p role="alert" class="text-sm text-red-600">{fieldErrors.name.join(' ')}</p>{/if}
  <label class="block text-sm">Email (digest recipient — blank = no digest)
    <input class="mt-1 w-full rounded border px-2 py-1" bind:value={email} />
  </label>
  {#if fieldErrors.email}<p role="alert" class="text-sm text-red-600">{fieldErrors.email.join(' ')}</p>{/if}
  <label class="flex items-center gap-2 text-sm"><input type="checkbox" bind:checked={isHouse} /> House account</label>
  {#if fieldErrors._}<p role="alert" class="text-sm text-red-600">{fieldErrors._.join(' ')}</p>{/if}
  <Button type="submit">Save</Button>
</form>
