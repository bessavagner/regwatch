import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import ClientForm from './ClientForm.svelte';
import * as resources from '../api/resources';
import type { Client } from '../api/types';

afterEach(() => vi.restoreAllMocks());

test('creating a client posts name, email, and is_house', async () => {
  const created: Client = { id: 5, name: 'Acme Corp', email: 'acme@example.com', is_house: false };
  vi.spyOn(resources, 'createClient').mockResolvedValue(created);
  let saved: Client | null = null;
  const user = userEvent.setup();
  render(ClientForm, { props: { onsaved: (c: Client) => (saved = c) } });

  await user.type(screen.getByLabelText(/name/i), 'Acme Corp');
  await user.type(screen.getByLabelText(/email/i), 'acme@example.com');
  await user.click(screen.getByRole('button', { name: /save/i }));

  expect(resources.createClient).toHaveBeenCalledWith({
    name: 'Acme Corp',
    email: 'acme@example.com',
    is_house: false,
  });
  await vi.waitFor(() => expect(saved).not.toBeNull());
});

test('editing a client PATCHes when a client prop is passed', async () => {
  const existing: Client = { id: 5, name: 'Acme Corp', email: '', is_house: false };
  const updated: Client = { ...existing, name: 'Acme Corporation', is_house: true };
  vi.spyOn(resources, 'updateClient').mockResolvedValue(updated);
  const user = userEvent.setup();
  render(ClientForm, { props: { client: existing, onsaved: () => {} } });

  await user.clear(screen.getByLabelText(/name/i));
  await user.type(screen.getByLabelText(/name/i), 'Acme Corporation');
  await user.click(screen.getByLabelText(/house account/i));
  await user.click(screen.getByRole('button', { name: /save/i }));

  expect(resources.updateClient).toHaveBeenCalledWith(5, {
    name: 'Acme Corporation',
    email: '',
    is_house: true,
  });
});

test('a 400 field error is shown', async () => {
  const { ApiError } = await import('../api/client');
  vi.spyOn(resources, 'createClient').mockRejectedValue(
    new ApiError(400, 'request failed', { name: ['this field may not be blank.'] }),
  );
  const user = userEvent.setup();
  render(ClientForm, { props: { onsaved: () => {} } });
  await user.click(screen.getByRole('button', { name: /save/i }));
  expect(await screen.findByText(/may not be blank/i)).toBeInTheDocument();
});
