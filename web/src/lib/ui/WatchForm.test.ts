import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import WatchForm from './WatchForm.svelte';
import * as resources from '../api/resources';
import type { Client, Watch } from '../api/types';
import { SECTIONS } from '../constants';

afterEach(() => vi.restoreAllMocks());
const clients: Client[] = [{ id: 3, name: 'Beta', is_house: false, email: '' }];

test('creating a watch splits comma terms and posts', async () => {
  const created: Watch = { id: 1, client: 3, terms: ['a', 'b'], exclude: [], match_mode: 'all', section: '1', active: true };
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

test('defaults a new watch to "all terms" and posts it that way untouched', async () => {
  const created: Watch = { id: 9, client: 3, terms: ['a'], exclude: [], match_mode: 'all', section: '', active: true };
  vi.spyOn(resources, 'createWatch').mockResolvedValue(created);
  const user = userEvent.setup();
  render(WatchForm, { props: { clients, onsaved: () => {} } });

  expect(screen.getByLabelText(/match/i)).toHaveValue('all');
  await user.type(screen.getByLabelText(/terms/i), 'a');
  await user.click(screen.getByRole('button', { name: /save/i }));

  expect(resources.createWatch).toHaveBeenCalledWith(expect.objectContaining({ match_mode: 'all' }));
});

test('switching to "any term" posts match_mode any', async () => {
  const created: Watch = { id: 9, client: 3, terms: ['a', 'b'], exclude: [], match_mode: 'any', section: '', active: true };
  vi.spyOn(resources, 'createWatch').mockResolvedValue(created);
  const user = userEvent.setup();
  render(WatchForm, { props: { clients, onsaved: () => {} } });

  await user.type(screen.getByLabelText(/terms/i), 'a, b');
  await user.selectOptions(screen.getByLabelText(/match/i), 'any');
  await user.click(screen.getByRole('button', { name: /save/i }));

  expect(resources.createWatch).toHaveBeenCalledWith(expect.objectContaining({ match_mode: 'any' }));
});

test('editing a watch preseeds its saved match_mode', () => {
  const watch: Watch = { id: 4, client: 3, terms: ['a', 'b'], exclude: [], match_mode: 'any', section: '', active: true };
  render(WatchForm, { props: { clients, watch, onsaved: () => {} } });
  expect(screen.getByLabelText(/match/i)).toHaveValue('any');
});

test('section options match the real pipeline edition codes', () => {
  render(WatchForm, { props: { clients, onsaved: () => {} } });
  const values = screen.getAllByRole('option', { name: /seção/i }).map((o) => (o as HTMLOptionElement).value);
  expect(values).toEqual(SECTIONS.map((s) => s.value));
  expect(values).toEqual(['DO1', 'DO2', 'DO3', 'DO1E', 'DO2E', 'DO3E']);
});

test('defaults a new watch to "all sections" and posts it that way untouched', async () => {
  const created: Watch = { id: 9, client: 3, terms: ['a'], exclude: [], match_mode: 'all', section: '', active: true };
  vi.spyOn(resources, 'createWatch').mockResolvedValue(created);
  const user = userEvent.setup();
  render(WatchForm, { props: { clients, onsaved: () => {} } });

  expect(screen.getByLabelText(/section/i)).toHaveValue('');
  await user.type(screen.getByLabelText(/terms/i), 'a');
  await user.click(screen.getByRole('button', { name: /save/i }));

  expect(resources.createWatch).toHaveBeenCalledWith(expect.objectContaining({ section: '' }));
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
