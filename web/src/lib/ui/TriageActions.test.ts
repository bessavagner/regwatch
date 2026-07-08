import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import TriageActions from './TriageActions.svelte';
import * as resources from '../api/resources';
import type { Match } from '../api/types';

afterEach(() => vi.restoreAllMocks());
const match: Match = {
  id: 7, watch: 1, act: 1, snippet: 's', rank: 0.5, ai_summary: '', category: '',
  confidence: 0.5, state: 'new', created_at: '2026-07-01T00:00:00Z',
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
