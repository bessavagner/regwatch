import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import Clients from './Clients.svelte';
import * as resources from '../lib/api/resources';
import type { Client } from '../lib/api/types';

afterEach(() => vi.restoreAllMocks());
const clients: Client[] = [{ id: 3, name: 'Beta', is_house: false, email: 'beta@example.com' }];

test('lists existing clients', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  render(Clients);
  await waitFor(() => expect(screen.getByText('Beta')).toBeInTheDocument());
});

test('shows an empty state with zero clients', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  render(Clients);
  await waitFor(() => expect(screen.getByText(/no clients yet/i)).toBeInTheDocument());
});

test('creating a client shows the form and appends the result to the list', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  const created: Client = { id: 9, name: 'Gamma', is_house: false, email: '' };
  vi.spyOn(resources, 'createClient').mockResolvedValue(created);
  const user = userEvent.setup();
  render(Clients);
  await waitFor(() => expect(screen.getByText('Beta')).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /new client/i }));
  await user.type(screen.getByLabelText(/name/i), 'Gamma');
  await user.click(screen.getByRole('button', { name: /save/i }));
  await waitFor(() => expect(screen.getByText('Gamma')).toBeInTheDocument());
});

test('a load failure surfaces an error', async () => {
  vi.spyOn(resources, 'listClients').mockRejectedValue(new Error('boom'));
  render(Clients);
  await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
});
