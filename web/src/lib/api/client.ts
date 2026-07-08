export class ApiError extends Error {
  status: number;
  detail: string;
  fields: Record<string, string[]>;

  constructor(status: number, detail: string, fields: Record<string, string[]> = {}) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.fields = fields;
  }
}

export function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : null;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  const init: RequestInit = { method, credentials: 'include', headers };

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }
  if (method !== 'GET' && method !== 'HEAD') {
    const token = getCookie('csrftoken');
    if (token) headers['X-CSRFToken'] = token;
  }

  const resp = await fetch(path, init);
  if (resp.status === 204) return undefined as T;

  const isJson = resp.headers.get('Content-Type')?.includes('application/json');
  // Clone before reading: some test mocks resolve the same Response instance
  // across calls, and a body stream can only be consumed once.
  const payload = isJson ? await resp.clone().json() : await resp.clone().text();

  if (!resp.ok) {
    if (isJson && payload && typeof payload === 'object') {
      const p = payload as Record<string, unknown>;
      if (typeof p.detail === 'string') throw new ApiError(resp.status, p.detail);
      throw new ApiError(resp.status, 'request failed', p as Record<string, string[]>);
    }
    throw new ApiError(resp.status, String(payload));
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
  del: (path: string) => request<void>('DELETE', path),
};
