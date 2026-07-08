import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import WatchForm from './WatchForm.svelte';
import * as resources from '../api/resources';
import type { Client, Watch } from '../api/types';

afterEach(() => vi.restoreAllMocks());
const clients: Client[] = [{ id: 3, name: 'Beta', is_house: false, email: '' }];

test('creating a watch splits comma terms and posts', async () => {
  const created: Watch = { id: 1, client: 3, terms: ['a', 'b'], exclude: [], section: '1', active: true };
  vi.spyOn(resources, 'createWatch').mockResolvedValue(created);
  let saved: Watch | null = null;
  const user = userEvent.setup();
  render(WatchForm, { props: { clients, onsaved: (w: Watch) => (saved = w) } });

  await user.selectOptions(screen.getByLabelText(/client/i), '3');
  await user.type(screen.getByLabelText(/terms/i), 'a, b');
  await user.click(screen.getByRole('button', { name: /save/i }));

  expect(resources.createWatch).toHaveBeenCalledWith(
    expect.objectContaining({ client: 3, terms: ['a', 'b'] }),
  );
  await vi.waitFor(() => expect(saved).not.toBeNull());
});

test('a 400 field error is shown', async () => {
  const { ApiError } = await import('../api/client');
  vi.spyOn(resources, 'createWatch').mockRejectedValue(
    new ApiError(400, 'request failed', { terms: ['must not be empty'] }),
  );
  const user = userEvent.setup();
  render(WatchForm, { props: { clients, onsaved: () => {} } });
  await user.selectOptions(screen.getByLabelText(/client/i), '3');
  await user.click(screen.getByRole('button', { name: /save/i }));
  expect(await screen.findByText(/must not be empty/i)).toBeInTheDocument();
});
