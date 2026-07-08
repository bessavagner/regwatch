import { render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, expect, test, vi } from 'vitest';
import Digests from './Digests.svelte';
import * as resources from '../lib/api/resources';
import type { Client, Digest } from '../lib/api/types';

afterEach(() => vi.restoreAllMocks());
const clients: Client[] = [{ id: 3, name: 'Beta', is_house: false, email: '' }];
const digest: Digest = { id: 1, client: 3, date: '2026-07-02', body: 'digest body', sent: true };

test('lists digests with sent status', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 1, next: null, previous: null, results: clients });
  vi.spyOn(resources, 'listDigests').mockResolvedValue({ count: 1, next: null, previous: null, results: [digest] });
  render(Digests);
  await waitFor(() => expect(screen.getByText('2026-07-02')).toBeInTheDocument());
  expect(screen.getByText(/sent/i)).toBeInTheDocument();
});

test('shows the empty state', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listDigests').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  render(Digests);
  await waitFor(() => expect(screen.getByText(/no digests/i)).toBeInTheDocument());
});
