<script lang="ts">
  import { untrack } from 'svelte';
  import type { Client, Watch, WatchGroup, WatchTermKind } from '../api/types';
  import { createWatch, updateWatch, type WatchBody } from '../api/resources';
  import { ApiError } from '../api/client';
  import { SECTIONS } from '../constants';
  import Button from './Button.svelte';

  let { clients, watch, onsaved }: { clients: Client[]; watch?: Watch; onsaved: (w: Watch) => void } = $props();

  // kindTouched tracks whether the user has changed this row's kind selector;
  // originalKinds remembers each pre-existing alias's kind so an untouched
  // selector doesn't silently coerce mixed-kind groups on save (see toRows/save).
  type Row = { aliases: string; kind: WatchTermKind; kindTouched: boolean; originalKinds: Map<string, WatchTermKind> };

  const newRow = (): Row => ({ aliases: '', kind: 'entity', kindTouched: false, originalKinds: new Map() });

  const toRows = (groups: WatchGroup[] | undefined): Row[] => {
    const rows = (groups ?? []).map((g) => ({
      aliases: g.terms.map((t) => t.text).join('\n'),
      kind: (g.terms[0]?.kind ?? 'entity') as WatchTermKind,
      kindTouched: false,
      originalKinds: new Map(g.terms.map((t) => [t.text, t.kind])),
    }));
    return rows.length ? rows : [newRow()];
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
  // Aliases split on newline, never on comma: official Brazilian names embed
  // commas ("Instituto Federal de Educação, Ciência e Tecnologia do Ceará"),
  // and a comma split silently turned one institution into two aliases.
  const splitLines = (s: string) => s.split('\n').map((t) => t.trim()).filter(Boolean);

  const addGroup = () => { rows = [...rows, newRow()]; };
  const removeGroup = (i: number) => { rows = rows.filter((_, n) => n !== i); };

  async function save(e: SubmitEvent) {
    e.preventDefault();
    fieldErrors = {};
    const groups: WatchGroup[] = rows
      .map((r) => ({
        terms: splitLines(r.aliases).map((text) => ({
          text,
          kind: r.kindTouched ? r.kind : (r.originalKinds.get(text) ?? r.kind),
        })),
      }))
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
      else fieldErrors = { _: [err instanceof ApiError ? err.detail : 'não foi possível salvar'] };
    }
  }
</script>

<form onsubmit={save} class="space-y-2">
  <label class="block text-sm">cliente
    <select class="mt-1 field" bind:value={client}>
      {#each clients as c}<option value={c.id}>{c.name}</option>{/each}
    </select>
  </label>

  <p class="text-sm">todos os grupos precisam bater. cada linha dentro de um grupo é uma outra forma de escrever a mesma coisa.</p>
  {#each rows as row, i}
    <div class="flex items-end gap-2">
      <label class="block flex-1 text-sm">variações do grupo {i + 1} (uma por linha)
        <textarea class="mt-1 field" rows="3" bind:value={row.aliases}></textarea>
      </label>
      <label class="block text-sm">tipo de busca do grupo {i + 1}
        <select class="mt-1 field" bind:value={row.kind} onchange={() => { row.kindTouched = true; }}>
          <option value="entity">nome (exato)</option>
          <option value="concept">palavra (com flexão)</option>
        </select>
      </label>
      {#if rows.length > 1}
        <Button type="button" onclick={() => removeGroup(i)}>remover grupo {i + 1}</Button>
      {/if}
    </div>
  {/each}
  <Button type="button" onclick={addGroup}>adicionar grupo</Button>
  {#if fieldErrors.groups}<p role="alert" class="text-sm text-danger">{fieldErrors.groups.join(' ')}</p>{/if}

  <label class="block text-sm">excluir (separado por vírgulas)
    <input class="mt-1 field" bind:value={excludeText} />
  </label>
  <label class="block text-sm">seção
    <select class="mt-1 field" bind:value={section}>
      <option value="">todas as seções</option>
      {#each SECTIONS as s}<option value={s.value}>{s.label}</option>{/each}
    </select>
  </label>
  <label class="flex items-center gap-2 text-sm"><input type="checkbox" class="accent-accent" bind:checked={active} /> ativa</label>
  {#if fieldErrors.client}<p role="alert" class="text-sm text-danger">{fieldErrors.client.join(' ')}</p>{/if}
  {#if fieldErrors._}<p role="alert" class="text-sm text-danger">{fieldErrors._.join(' ')}</p>{/if}
  <Button type="submit">salvar</Button>
</form>
