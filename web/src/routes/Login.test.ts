import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import Login from './Login.svelte';
import { auth } from '../lib/stores/auth.svelte';

afterEach(() => {
  vi.restoreAllMocks();
  auth.me = null;
  auth.status = 'idle';
  auth.error = null;
});

test('submitting valid credentials calls auth.login', async () => {
  const spy = vi.spyOn(auth, 'login').mockResolvedValue();
  const user = userEvent.setup();
  render(Login);

  await user.type(screen.getByLabelText(/username/i), 'a@f.com');
  await user.type(screen.getByLabelText(/password/i), 'pw');
  await user.click(screen.getByRole('button', { name: /sign in/i }));

  expect(spy).toHaveBeenCalledWith('a@f.com', 'pw');
});

test('an auth error is shown', async () => {
  vi.spyOn(auth, 'login').mockImplementation(async () => {
    auth.error = 'invalid credentials';
    auth.status = 'anon';
  });
  const user = userEvent.setup();
  render(Login);
  await user.type(screen.getByLabelText(/username/i), 'a@f.com');
  await user.type(screen.getByLabelText(/password/i), 'x');
  await user.click(screen.getByRole('button', { name: /sign in/i }));
  expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
});
