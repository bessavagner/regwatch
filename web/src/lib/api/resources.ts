import { api } from './client';
import type { Client, Digest, Match, Page, Watch } from './types';

export interface MatchParams {
  client?: string;
  state?: string;
  section?: string;
  category?: string;
  date_from?: string;
  date_to?: string;
  ordering?: string;
  page?: number;
}

function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') search.set(k, String(v));
  }
  const s = search.toString();
  return s ? `?${s}` : '';
}

export const listMatches = (p: MatchParams = {}) =>
  api.get<Page<Match>>(`/api/matches${qs(p)}`);
export const listClients = () => api.get<Page<Client>>('/api/clients');
export const listWatches = (client?: string) =>
  api.get<Page<Watch>>(`/api/watches${qs({ client })}`);
export const listDigests = (client?: string) =>
  api.get<Page<Digest>>(`/api/digests${qs({ client })}`);
export const markRelevant = (id: number) => api.post<Match>(`/api/matches/${id}/relevant`);
export const dismissMatch = (id: number) => api.post<Match>(`/api/matches/${id}/dismiss`);

export interface WatchBody {
  client: number;
  terms: string[];
  exclude: string[];
  section: string;
  active: boolean;
}
export const createWatch = (body: WatchBody) => api.post<Watch>('/api/watches', body);
export const updateWatch = (id: number, body: Partial<WatchBody>) =>
  api.patch<Watch>(`/api/watches/${id}`, body);

export interface ClientBody {
  name: string;
  email: string;
  is_house: boolean;
}
export const createClient = (body: ClientBody) => api.post<Client>('/api/clients', body);
export const updateClient = (id: number, body: Partial<ClientBody>) =>
  api.patch<Client>(`/api/clients/${id}`, body);
