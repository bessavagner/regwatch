export interface Workspace {
  id: number;
  name: string;
}

export interface Me {
  id: number;
  username: string;
  email: string;
  workspace: Workspace | null;
}

export interface Client {
  id: number;
  name: string;
  is_house: boolean;
  email: string;
}

export type WatchTermKind = 'entity' | 'concept';

export interface WatchTerm {
  text: string;
  kind: WatchTermKind;
}

export interface WatchGroup {
  terms: WatchTerm[];
}

export interface Watch {
  id: number;
  client: number;
  groups: WatchGroup[];
  exclude: string[];
  section: string;
  active: boolean;
}

export interface Match {
  id: number;
  watch: number;
  act: number;
  snippet: string;
  rank: number;
  ai_summary: string;
  category: string;
  confidence: number;
  state: 'new' | 'relevant' | 'dismissed';
  created_at: string;
}

export interface Digest {
  id: number;
  client: number;
  date: string;
  body: string;
  sent: boolean;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
