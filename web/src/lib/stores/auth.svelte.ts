import { api, ApiError } from '../api/client';
import type { Me } from '../api/types';

export async function loadMe(): Promise<void> {
  auth.status = 'loading';
  try {
    // GET /api/me also seeds the csrftoken cookie (@ensure_csrf_cookie).
    auth.me = await api.get<Me>('/api/me');
    auth.status = 'authed';
    auth.error = null;
  } catch {
    auth.me = null;
    auth.status = 'anon';
  }
}

async function login(username: string, password: string): Promise<void> {
  auth.error = null;
  try {
    await api.post<Me>('/api/auth/login', { username, password });
    await loadMe(); // seed csrf + confirm session
  } catch (err) {
    auth.status = 'anon';
    auth.me = null;
    auth.error = err instanceof ApiError ? err.detail : 'login failed';
  }
}

async function logout(): Promise<void> {
  try {
    await api.post('/api/auth/logout');
  } finally {
    auth.me = null;
    auth.status = 'anon';
  }
}

export const auth = $state<{
  status: 'idle' | 'loading' | 'authed' | 'anon';
  me: Me | null;
  error: string | null;
  login: (u: string, p: string) => Promise<void>;
  logout: () => Promise<void>;
  loadMe: () => Promise<void>;
}>({
  status: 'idle',
  me: null,
  error: null,
  login,
  logout,
  loadMe,
});
