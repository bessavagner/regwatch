import { afterEach, expect, test, vi } from 'vitest';
import { auth } from './auth.svelte';

afterEach(() => {
  vi.restoreAllMocks();
  auth.me = null;
  auth.status = 'idle';
  auth.error = null;
});

test('login stores the me payload and marks authed', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      // POST /api/auth/login
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 1, username: 'a@f.com', email: 'a@f.com', workspace: { id: 9, name: 'Acme' } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      // GET /api/me (seeds csrf)
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 1, username: 'a@f.com', email: 'a@f.com', workspace: { id: 9, name: 'Acme' } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
  );

  await auth.login('a@f.com', 'pw');
  expect(auth.status).toBe('authed');
  expect(auth.me?.workspace?.name).toBe('Acme');
});

test('bad credentials set an error and stay anon', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'invalid credentials' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  );
  await auth.login('a@f.com', 'wrong');
  expect(auth.status).toBe('anon');
  expect(auth.error).toBe('invalid credentials');
});
