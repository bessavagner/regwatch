import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import Watches from './Watches.svelte';
import * as resources from '../lib/api/resources';
import type { Client, Watch } from '../lib/api/types';

afterEach(() => vi.restoreAllMocks());
const clients: Client[] = [{ id: 3, name: 'Beta', is_house: false, email: '' }];
const watch: Watch = { id: 1, client: 3, terms: ['x'], exclude: [], section: '1', active: true };

test('lists existing watches', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listWatches').mockResolvedValue({ count: 1, next: null, previous: null, results: [watch] });
  render(Watches);
  await waitFor(() => expect(screen.getByText(/x/)).toBeInTheDocument());
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
