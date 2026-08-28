import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import TriageActions from './TriageActions.svelte';
import * as resources from '../api/resources';
import type { Match } from '../api/types';

afterEach(() => vi.restoreAllMocks());
const match: Match = {
  id: 7, watch: 1, act: 1, snippet: 's', matched_terms: [], rank: 0.5, ai_summary: '', category: '',
  category_label: 'sem categoria',
  confidence: 0.5, state: 'new', created_at: '2026-07-01T00:00:00Z',
  names_party: false, has_amount: false, has_deadline: false, signal_score: 0,
  client_id: 1, client_name: 'Beta Corp',
  act_detail: {
    id: 1, title: 'Portaria 1', agency: '', identifier: 'id-1',
    date: '2026-07-01', section: 'DO1',
    source_url: 'https://inlabs.in.gov.br/edition/DO1', source_anchor: '#a1',
  },
};

test('clicking Relevant calls the API and emits the updated match', async () => {
  vi.spyOn(resources, 'markRelevant').mockResolvedValue({ ...match, state: 'relevant' });
  const changed: Match[] = [];
  const user = userEvent.setup();
  render(TriageActions, { props: { match, onchange: (m: Match) => changed.push(m), onerror: () => {} } });
  await user.click(screen.getByRole('button', { name: /relevant/i }));
  expect(resources.markRelevant).toHaveBeenCalledWith(7);
  await vi.waitFor(() => expect(changed[0].state).toBe('relevant'));
});

test('a rejected write surfaces an error, not a silent no-op', async () => {
  vi.spyOn(resources, 'dismissMatch').mockRejectedValue(new Error('boom'));
  let errored = '';
  const user = userEvent.setup();
  render(TriageActions, { props: { match, onchange: () => {}, onerror: (msg: string) => (errored = msg) } });
  await user.click(screen.getByRole('button', { name: /dismiss/i }));
  await vi.waitFor(() => expect(errored).toBeTruthy());
});
