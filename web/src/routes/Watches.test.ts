import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import Watches from './Watches.svelte';
import * as resources from '../lib/api/resources';
import type { Client, Watch } from '../lib/api/types';

afterEach(() => vi.restoreAllMocks());
const clients: Client[] = [{ id: 3, name: 'Beta', is_house: false, email: '' }];
const watch: Watch = {
  id: 1,
  client: 3,
  groups: [
    { terms: [{ text: 'sebrae', kind: 'entity' }, { text: 'sebrae/mg', kind: 'entity' }] },
    { terms: [{ text: 'contrato', kind: 'concept' }] },
  ],
  exclude: [],
  section: 'DO1',
  active: true,
  client_name: 'Acme',
  match_count: 12,
  last_match_at: '2026-08-11T09:14:00Z',
};

test('lists existing watches, rendering groups as OR-within / AND-across', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  render(Watches);
  await waitFor(() =>
    expect(screen.getByText('sebrae / sebrae/mg + contrato')).toBeInTheDocument(),
  );
});

test('toggling active PATCHes the watch', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  const spy = vi.spyOn(resources, 'updateWatch').mockResolvedValue({ ...watch, active: false });
  const user = userEvent.setup();
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /desativar/i })).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /desativar/i }));
  expect(spy).toHaveBeenCalledWith(1, { active: false });
});

test('a failed toggle surfaces an error instead of failing silently', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  vi.spyOn(resources, 'updateWatch').mockRejectedValue(new Error('boom'));
  const user = userEvent.setup();
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /desativar/i })).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /desativar/i }));
  await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
  expect(screen.getByRole('button', { name: /desativar/i })).toBeInTheDocument();
});

test('clicking "Run on past editions" reveals the backfill form', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  const user = userEvent.setup();
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /rodar em edições anteriores/i })).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /rodar em edições anteriores/i }));
  expect(screen.getByLabelText(/^de$/i)).toBeInTheDocument();
});

test('a watch row names its client and reports its match activity', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  render(Watches);

  await waitFor(() => expect(screen.getByText('Acme')).toBeInTheDocument());
  expect(screen.getByText(/12 ocorrências/)).toBeInTheDocument();
  expect(screen.getByText(/última 2026-08-11/)).toBeInTheDocument();
  // The row used to print a bare "seção 1"; it now uses the form's own label.
  expect(screen.getByText(/seção 1/)).toBeInTheDocument();
});

test('a watch that has never matched says so instead of looking healthy', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({
    count: 1, next: null, previous: null,
    results: [{ ...watch, match_count: 0, last_match_at: null }],
  });
  render(Watches);

  await waitFor(() => expect(screen.getByText(/nenhuma ocorrência ainda/i)).toBeInTheDocument());
});

test('with zero clients, "New watch" is disabled with a link to Clients', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /nova busca/i })).toBeDisabled());
  expect(screen.getByRole('link', { name: /clientes/i })).toHaveAttribute('href', '/clients');
});

test('clicking editar opens the form populated with that watch', async () => {
  const user = userEvent.setup();
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /editar/i })).toBeInTheDocument());

  await user.click(screen.getByRole('button', { name: /editar/i }));

  // The form is open and seeded from the row that was clicked.
  await waitFor(() =>
    expect(screen.getByRole('button', { name: /salvar/i })).toBeInTheDocument(),
  );
  const aliases = screen.getByLabelText(/variações do grupo 1/i) as HTMLTextAreaElement;
  expect(aliases.value).toContain('sebrae');
});

test('the edit form opens next to the row, not off at the top of the page', async () => {
  // "I clicked editar and nothing happened": with several watches the form
  // rendered above the list, out of view from the row that opened it.
  const user = userEvent.setup();
  const many = [1, 2, 3, 4, 5, 6].map((id) => ({ ...watch, id, client_name: `C${id}` }));
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 6, next: null, previous: null, results: many });
  render(Watches);
  await waitFor(() => expect(screen.getAllByRole('button', { name: /editar/i })).toHaveLength(6));

  await user.click(screen.getAllByRole('button', { name: /editar/i })[4]);

  const form = screen.getByRole('button', { name: /salvar/i }).closest('form');
  expect(form).not.toBeNull();
  // The form must live inside the row it is editing.
  const row = screen.getAllByRole('listitem')[4];
  expect(row.contains(form!)).toBe(true);
});
