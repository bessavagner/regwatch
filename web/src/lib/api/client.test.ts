import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { api, ApiError, getCookie } from './client';

beforeEach(() => {
  document.cookie = 'csrftoken=tok123; path=/';
});
afterEach(() => {
  vi.restoreAllMocks();
  document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
});

test('getCookie reads a named cookie', () => {
  expect(getCookie('csrftoken')).toBe('tok123');
  expect(getCookie('missing')).toBeNull();
});

test('post sends X-CSRFToken and credentials, parses JSON', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ id: 1 }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);

  const data = await api.post<{ id: number }>('/api/x', { a: 1 });
  expect(data).toEqual({ id: 1 });

  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toBe('/api/x');
  expect(init.credentials).toBe('include');
  expect(init.headers['X-CSRFToken']).toBe('tok123');
  expect(init.method).toBe('POST');
});

test('a 400 throws ApiError with field errors', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ terms: ['must not be empty'] }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  );
  await expect(api.post('/api/watches', {})).rejects.toMatchObject({
    status: 400,
    fields: { terms: ['must not be empty'] },
  });
  await expect(api.post('/api/watches', {})).rejects.toBeInstanceOf(ApiError);
});
