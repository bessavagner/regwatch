import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import Feed from './Feed.svelte';
import * as resources from '../lib/api/resources';
import type { Match, Paged } from '../lib/api/types';

afterEach(() => {
  vi.restoreAllMocks();
  window.history.pushState({}, '', '/feed');
});

function page(results: Match[], count = results.length): Paged<Match> {
  return { count, page: 1, total_pages: 1, page_size: 25, next: null, previous: null, results };
}
const m = (id: number, state: Match['state'] = 'new'): Match => ({
  id, watch: 1, act: id, snippet: `snip-${id}`, matched_terms: [], rank: 0.5, ai_summary: '',
  category: '', category_label: 'sem categoria', confidence: 0.5, state,
  names_party: false, has_amount: false, has_deadline: false, signal_score: 0,
  created_at: '2026-07-01T00:00:00Z',
  client_id: 1, client_name: 'Beta Corp',
  act_detail: {
    id, title: `Portaria ${id}`, agency: '', identifier: `id-${id}`,
    date: '2026-07-01', section: 'DO1',
    source_url: 'https://inlabs.in.gov.br/edition/DO1', source_anchor: `#a${id}`,
  },
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

test('seeds filters from the URL query string on mount', async () => {
  window.history.pushState({}, '', '/feed?client=3&date_from=2026-07-01&date_to=2026-07-01');
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue(page([]));
  render(Feed);
  await waitFor(() =>
    expect(spy).toHaveBeenCalledWith(
      expect.objectContaining({ client: '3', date_from: '2026-07-01', date_to: '2026-07-01' }),
    ),
  );
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
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue({ count: 30, page: 1, total_pages: 2, page_size: 25, next: '/api/matches?page=2', previous: null, results: [m(1)] });
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
  // Scoped to the badge <span> — the State filter's <option value="relevant"> also
  // renders the literal text "relevant" now that its label is lowercased to match
  // the app's typographic system, so an unscoped getByText is ambiguous.
  await waitFor(() => expect(screen.getByText('relevant', { selector: 'span' })).toBeInTheDocument());
});

test('the Send digest action is hidden unless exactly one client and one exact date are selected', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({
    count: 1, next: null, previous: null, results: [{ id: 3, name: 'Beta', is_house: false, email: '' }],
  });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  expect(screen.queryByRole('button', { name: /send digest/i })).not.toBeInTheDocument();
});

test('shows the Send digest action when filtered to one client and one exact date, and sends it', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({
    count: 1, next: null, previous: null, results: [{ id: 3, name: 'Beta', is_house: false, email: '' }],
  });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  const sendSpy = vi.spyOn(resources, 'sendDigest').mockResolvedValue({ id: 9, client: 3, date: '2026-07-01', body: 'x', sent: true });
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.selectOptions(screen.getByLabelText(/client/i), '3');
  await user.type(screen.getByLabelText(/^from$/i), '2026-07-01');
  await user.type(screen.getByLabelText(/^to$/i), '2026-07-01');

  await waitFor(() => expect(screen.getByRole('button', { name: /send digest/i })).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /send digest/i }));

  expect(sendSpy).toHaveBeenCalledWith({ client: 3, date: '2026-07-01' });
  await waitFor(() => expect(screen.getByRole('button', { name: /digest sent/i })).toBeInTheDocument());
});

test('changing a filter writes it to the query string', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.selectOptions(screen.getByLabelText(/state/i), 'relevant');
  await waitFor(() => expect(window.location.search).toBe('?state=relevant'));
});

test('browser back restores the previous filter set and refetches', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.selectOptions(screen.getByLabelText(/state/i), 'relevant');
  await waitFor(() => expect(window.location.search).toBe('?state=relevant'));

  // jsdom moves the history cursor but does not emit popstate for history.back(),
  // so dispatch it the way a real browser would.
  window.history.back();
  window.dispatchEvent(new PopStateEvent('popstate'));

  await waitFor(() => expect(window.location.search).toBe(''));
  await waitFor(() =>
    expect(spy).toHaveBeenLastCalledWith(expect.not.objectContaining({ state: 'relevant' })),
  );
});

test('every control shows the filter the URL asked for', async () => {
  window.history.pushState({}, '', '/feed?state=relevant&section=DO2&category=tender&date_from=2026-07-01&date_to=2026-07-02&ordering=rank');
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  vi.spyOn(resources, 'getVocabulary').mockResolvedValue({
    categories: [{ value: 'tender', label: 'licitação' }],
  });
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await waitFor(() =>
    expect((screen.getByLabelText(/category/i) as HTMLSelectElement).value).toBe('tender'),
  );
  expect((screen.getByLabelText(/state/i) as HTMLSelectElement).value).toBe('relevant');
  expect((screen.getByLabelText(/section/i) as HTMLSelectElement).value).toBe('DO2');
  expect((screen.getByLabelText(/order/i) as HTMLSelectElement).value).toBe('rank');
  expect((screen.getByLabelText(/^from$/i) as HTMLInputElement).value).toBe('2026-07-01');
  expect((screen.getByLabelText(/^to$/i) as HTMLInputElement).value).toBe('2026-07-02');
});

test('the client control shows the seeded client once its options arrive', async () => {
  window.history.pushState({}, '', '/feed?client=3');
  vi.spyOn(resources, 'listClients').mockResolvedValue({
    count: 1, next: null, previous: null,
    results: [{ id: 3, name: 'Beta', is_house: false, email: '' }],
  });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  await waitFor(() =>
    expect((screen.getByLabelText(/client/i) as HTMLSelectElement).value).toBe('3'),
  );
});

test('with no filters every control reads all', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  expect((screen.getByLabelText(/state/i) as HTMLSelectElement).value).toBe('');
  expect((screen.getByLabelText(/section/i) as HTMLSelectElement).value).toBe('');
  expect((screen.getByLabelText(/^from$/i) as HTMLInputElement).value).toBe('');
});

test('says which page of how many', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue({
    count: 429, page: 1, total_pages: 18, page_size: 25,
    next: '/api/matches?page=2', previous: null, results: [m(1)],
  });
  render(Feed);
  await waitFor(() => expect(screen.getByText('Page 1 of 18')).toBeInTheDocument());
});

test('the page indicator follows the Next button', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue({
    count: 429, page: 1, total_pages: 18, page_size: 25,
    next: '/api/matches?page=2', previous: null, results: [m(1)],
  });
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('Page 1 of 18')).toBeInTheDocument());
  await user.click(screen.getByRole('button', { name: /next/i }));
  await waitFor(() => expect(screen.getByText('Page 2 of 18')).toBeInTheDocument());
  expect(window.location.search).toBe('?page=2');
});

test('an empty feed is page 1 of 1, never page 1 of 0', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([], 0));
  render(Feed);
  await waitFor(() => expect(screen.getByText(/no matches/i)).toBeInTheDocument());
  expect(screen.getByText('Page 1 of 1')).toBeInTheDocument();
});

test('triaging a match out of the active filter lowers the count and the dial', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1), m(2)], 2));
  vi.spyOn(resources, 'markRelevant').mockResolvedValue({ ...m(1), state: 'relevant' });
  const user = userEvent.setup();
  window.history.pushState({}, '', '/feed?state=new');
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  expect(screen.getByText('2 matches')).toBeInTheDocument();

  // One Relevant button per card, so take the first.
  await user.click(screen.getAllByRole('button', { name: /^relevant$/i })[0]);

  await waitFor(() => expect(screen.getByText('1 match')).toBeInTheDocument());
  expect(screen.getByLabelText('1 matches tracked')).toBeInTheDocument();
});

test('triaging within the active filter leaves the count alone', async () => {
  // No state filter: the match stays in the set, so the total has not changed.
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1), m(2)], 2));
  vi.spyOn(resources, 'markRelevant').mockResolvedValue({ ...m(1), state: 'relevant' });
  const user = userEvent.setup();
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.click(screen.getAllByRole('button', { name: /^relevant$/i })[0]);
  await waitFor(() => expect(screen.getByText('relevant', { selector: 'span' })).toBeInTheDocument());
  expect(screen.getByText('2 matches')).toBeInTheDocument();
});

test('emptying a page that still has matches behind it reloads it', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  // One visible row, 26 in the filtered set: there is a page behind this one.
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue({
    count: 26, page: 1, total_pages: 2, page_size: 25,
    next: '/api/matches?page=2', previous: null, results: [m(1)],
  });
  vi.spyOn(resources, 'markRelevant').mockResolvedValue({ ...m(1), state: 'relevant' });
  const user = userEvent.setup();
  window.history.pushState({}, '', '/feed?state=new');
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());
  const before = spy.mock.calls.length;

  await user.click(screen.getAllByRole('button', { name: /^relevant$/i })[0]);

  // count drops to 25, which is still one full page, so page 1 reloads.
  await waitFor(() => expect(spy.mock.calls.length).toBeGreaterThan(before));
  expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ page: 1, state: 'new' }));
});

test('emptying the last page steps back to the page before it', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  // Page 2 of 2, holding the single 26th match.
  const spy = vi.spyOn(resources, 'listMatches').mockResolvedValue({
    count: 26, page: 2, total_pages: 2, page_size: 25,
    next: null, previous: '/api/matches', results: [m(1)],
  });
  vi.spyOn(resources, 'markRelevant').mockResolvedValue({ ...m(1), state: 'relevant' });
  const user = userEvent.setup();
  window.history.pushState({}, '', '/feed?state=new&page=2');
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.click(screen.getAllByRole('button', { name: /^relevant$/i })[0]);

  // count drops to 25 -- one page -- so page 2 no longer exists.
  await waitFor(() => expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ page: 1 })));
  await waitFor(() => expect(window.location.search).toBe('?state=new'));
});

test('emptying the only page just shows the empty state', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  // The set really does shrink: page 1 is still page 1, so it reloads, and the
  // server now has nothing left under state=new to return.
  vi.spyOn(resources, 'listMatches')
    .mockResolvedValue(page([], 0))
    .mockResolvedValueOnce(page([m(1)], 1));
  vi.spyOn(resources, 'markRelevant').mockResolvedValue({ ...m(1), state: 'relevant' });
  const user = userEvent.setup();
  window.history.pushState({}, '', '/feed?state=new');
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await user.click(screen.getAllByRole('button', { name: /^relevant$/i })[0]);
  await waitFor(() => expect(screen.getByText(/no matches/i)).toBeInTheDocument());
});

test('the order control offers sorting by signal and puts it in the URL', async () => {
  vi.spyOn(resources, 'listClients').mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  const list = vi.spyOn(resources, 'listMatches').mockResolvedValue(page([m(1)]));
  render(Feed);
  await waitFor(() => expect(screen.getByText('snip-1')).toBeInTheDocument());

  await userEvent.selectOptions(screen.getByLabelText(/order/i), 'signal');
  await waitFor(() =>
    expect(list).toHaveBeenLastCalledWith(expect.objectContaining({ ordering: 'signal' })),
  );
  expect(window.location.search).toContain('ordering=signal');
});
