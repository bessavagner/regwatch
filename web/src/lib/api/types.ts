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
  client_name: string;
  groups: WatchGroup[];
  exclude: string[];
  section: string;
  active: boolean;
  match_count: number;
  last_match_at: string | null;
}

export interface ActDetail {
  id: number;
  title: string;
  agency: string;
  identifier: string;
  date: string;
  section: string;
  source_url: string;
  source_anchor: string;
}

export interface Match {
  id: number;
  watch: number;
  act: number;
  act_detail: ActDetail;
  client_id: number;
  client_name: string;
  snippet: string;
  rank: number;
  // null whenever enrichment never ran for this match.
  ai_summary: string | null;
  category: string;
  // Portuguese label for `category`, rendered by the API so a badge never
  // shows the storage enum while a lookup is in flight.
  category_label: string;
  confidence: number | null;
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

export interface VocabularyItem {
  value: string;
  label: string;
}

export interface Vocabulary {
  categories: VocabularyItem[];
}
