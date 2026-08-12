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
  await waitFor(() => expect(screen.getByRole('button', { name: /deactivate/i })).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /deactivate/i }));
  expect(spy).toHaveBeenCalledWith(1, { active: false });
});

test('a failed toggle surfaces an error instead of failing silently', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  vi.spyOn(resources, 'updateWatch').mockRejectedValue(new Error('boom'));
  const user = userEvent.setup();
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /deactivate/i })).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /deactivate/i }));
  await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
  expect(screen.getByRole('button', { name: /deactivate/i })).toBeInTheDocument();
});

test('clicking "Run on past editions" reveals the backfill form', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  const user = userEvent.setup();
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /run on past editions/i })).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /run on past editions/i }));
  expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
});

test('a watch row names its client and reports its match activity', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  render(Watches);

  await waitFor(() => expect(screen.getByText('Acme')).toBeInTheDocument());
  expect(screen.getByText(/12 matches/)).toBeInTheDocument();
  expect(screen.getByText(/last 2026-08-11/)).toBeInTheDocument();
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

  await waitFor(() => expect(screen.getByText(/no matches yet/i)).toBeInTheDocument());
});

test('with zero clients, "New watch" is disabled with a link to Clients', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  render(Watches);
  await waitFor(() => expect(screen.getByRole('button', { name: /new watch/i })).toBeDisabled());
  expect(screen.getByRole('link', { name: /clients/i })).toHaveAttribute('href', '/clients');
});
