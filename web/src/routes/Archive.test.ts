import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import Archive from './Archive.svelte';
import * as resources from '../lib/api/resources';
import type { Match, Paged } from '../lib/api/types';

afterEach(() => vi.restoreAllMocks());

const archived = (id: number): Match => ({
  id, watch: 1, act: id, snippet: `snip-${id}`, matched_terms: [], rank: 0.5, ai_summary: '',
  category: '', category_label: 'sem categoria', state: 'dismissed',
  names_party: false, has_amount: false, has_deadline: false, signal_score: 0,
  created_at: '2026-07-01T00:00:00Z', client_id: 1, client_name: 'Cactarus',
  act_detail: {
    id, title: `Portaria ${id}`, agency: 'Org', identifier: `id-${id}`,
    date: '2026-07-01', section: 'DO1',
    source_url: 'https://inlabs.in.gov.br/edition/DO1', source_anchor: `#a${id}`,
  },
});

function page(results: Match[]): Paged<Match> {
  return { count: results.length, page: 1, total_pages: 1, page_size: 25, next: null, previous: null, results };
}

test('it lists only archived matches', async () => {
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue(page([archived(1), archived(2)]));
  render(Archive);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  // The archive is exactly ?state=dismissed — it must not invent its own set.
  expect(spy).toHaveBeenCalledWith(expect.objectContaining({ state: 'dismissed' }));
});

test('an empty archive says so', async () => {
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([]));
  render(Archive);
  await waitFor(() => expect(screen.getByText(/arquivo está vazio/i)).toBeInTheDocument());
});

test('restoring a match takes it out of the archive', async () => {
  const user = userEvent.setup();
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([archived(1), archived(2)]));
  const spy = vi.spyOn(resources, 'reopenMatch').mockResolvedValue({ ...archived(1), state: 'new' });
  render(Archive);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.click(screen.getAllByRole('button', { name: /restaurar/i })[0]);

  await waitFor(() => expect(spy).toHaveBeenCalledWith(1));
  await waitFor(() => expect(screen.queryByText('snip-1')).not.toBeInTheDocument());
});

test('deleting requires selecting, then confirming', async () => {
  const user = userEvent.setup();
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([archived(1), archived(2)]));
  const spy = vi.spyOn(resources, 'deleteMatches').mockResolvedValue({ deleted: 1 });
  render(Archive);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  // Nothing selected: no destructive action is even offered.
  expect(screen.queryByRole('button', { name: /excluir/i })).not.toBeInTheDocument();

  await user.click(screen.getAllByRole('checkbox')[0]);
  await user.click(screen.getByRole('button', { name: /excluir definitivamente/i }));
  // Arming is not doing.
  expect(spy).not.toHaveBeenCalled();

  await user.click(screen.getByRole('button', { name: /confirmar/i }));
  await waitFor(() => expect(spy).toHaveBeenCalledWith([1]));
  await waitFor(() => expect(screen.queryByText('snip-1')).not.toBeInTheDocument());
});

test('the confirmation says how many rows will be lost, and that it cannot be undone', async () => {
  const user = userEvent.setup();
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([archived(1), archived(2)]));
  render(Archive);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.click(screen.getAllByRole('checkbox')[0]);
  await user.click(screen.getAllByRole('checkbox')[1]);
  await user.click(screen.getByRole('button', { name: /excluir definitivamente/i }));

  expect(screen.getByText(/2 ocorrências/i)).toBeInTheDocument();
  expect(screen.getByText(/não pode ser desfeito/i)).toBeInTheDocument();
});

test('a failed delete is reported and keeps the rows', async () => {
  const user = userEvent.setup();
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([archived(1)]));
  vi.spyOn(resources, 'deleteMatches').mockRejectedValue(new Error('boom'));
  render(Archive);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.click(screen.getAllByRole('checkbox')[0]);
  await user.click(screen.getByRole('button', { name: /excluir definitivamente/i }));
  await user.click(screen.getByRole('button', { name: /confirmar/i }));

  await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
  expect(screen.getByText('snip-1')).toBeInTheDocument();
});
