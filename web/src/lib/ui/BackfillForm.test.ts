import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import BackfillForm from './BackfillForm.svelte';
import * as resources from '../api/resources';
import * as routerModule from '../router/router.svelte';
import type { Watch } from '../api/types';

afterEach(() => vi.restoreAllMocks());
const watch: Watch = { id: 1, client: 3, terms: ['x'], exclude: [], section: '1', active: true };

test('submitting runs the backfill and navigates to the feed pre-filtered to the watch and range', async () => {
  vi.spyOn(resources, 'backfillWatch').mockResolvedValue({
    editions: 1, acts: 1, matches: 1, enriched: 1, skipped_dates: [],
  });
  const navigateSpy = vi.spyOn(routerModule, 'navigate');
  const user = userEvent.setup();
  render(BackfillForm, { props: { watch, oncancel: () => {} } });

  await user.type(screen.getByLabelText(/from/i), '2026-07-01');
  await user.type(screen.getByLabelText(/to/i), '2026-07-02');
  await user.click(screen.getByRole('button', { name: /^run$/i }));

  expect(resources.backfillWatch).toHaveBeenCalledWith(1, { date_from: '2026-07-01', date_to: '2026-07-02' });
  await vi.waitFor(() =>
    expect(navigateSpy).toHaveBeenCalledWith('/feed?client=3&date_from=2026-07-01&date_to=2026-07-02'),
  );
});

test('a 400 range error is shown as a non-field error', async () => {
  const { ApiError } = await import('../api/client');
  vi.spyOn(resources, 'backfillWatch').mockRejectedValue(
    new ApiError(400, 'request failed', { non_field_errors: ['range must not exceed 7 days'] }),
  );
  const user = userEvent.setup();
  render(BackfillForm, { props: { watch, oncancel: () => {} } });
  await user.type(screen.getByLabelText(/from/i), '2026-07-01');
  await user.type(screen.getByLabelText(/to/i), '2026-07-10');
  await user.click(screen.getByRole('button', { name: /^run$/i }));
  expect(await screen.findByText(/must not exceed 7 days/i)).toBeInTheDocument();
});

test('clicking Cancel invokes oncancel', async () => {
  const oncancel = vi.fn();
  const user = userEvent.setup();
  render(BackfillForm, { props: { watch, oncancel } });
  await user.click(screen.getByRole('button', { name: /cancel/i }));
  expect(oncancel).toHaveBeenCalled();
});
