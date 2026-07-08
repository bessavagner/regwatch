import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import Feed from './Feed.svelte';
import * as resources from '../lib/api/resources';
import type { Match, Page } from '../lib/api/types';

afterEach(() => vi.restoreAllMocks());

function page(results: Match[], count = results.length): Page<Match> {
  return { count, next: null, previous: null, results };
}
const m = (id: number, state: Match['state'] = 'new'): Match => ({
  id, watch: 1, act: id, snippet: `snip-${id}`, rank: 0.5, ai_summary: '',
  category: '', confidence: 0.5, state, created_at: '2026-07-01T00:00:00Z',
});

test('loads and renders the match feed', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1), m(2)]));
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  expect(screen.getByText('snip-2')).toBeInTheDocument();
});

test('shows the empty state when there are no matches', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([]));
  render(Feed);
  await waitFor(() => expect(screen.getByText(/no matches/i)).toBeInTheDocument());
});

test('changing the state filter refetches with the state param', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  await user.selectOptions(screen.getByLabelText(/state/i), 'relevant');
  await waitFor(() =>
    expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ state: 'relevant' })),
  );
});

test('Next button advances the page and refetches', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue({ count: 30, next: '/api/matches?page=2', previous: null, results: [m(1)] });
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /next/i }));
  await waitFor(() => expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })));
});

test('marking a match relevant updates its card in place', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  vi.spyOn(resources, 'markRelevant').mockResolvedValue({ ...m(1), state: 'relevant' });
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /relevant/i }));
  await waitFor(() => expect(screen.getByText('relevant')).toBeInTheDocument());
});
