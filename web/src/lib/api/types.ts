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
  // Which of the watch's terms fired, as the client typed them. Empty for
  // every match created before v0.20.0 -- the card hides the line, it does not
  // print an empty one.
  matched_terms: string[];
  rank: number;
  // null whenever enrichment never ran for this match.
  ai_summary: string | null;
  category: string;
  // Portuguese label for `category`, rendered by the API so a badge never
  // shows the storage enum while a lookup is in flight.
  category_label: string;
  // What the enricher could check in the act text. `signal_score` is their sum,
  // 0-3, and is what `ordering=signal` sorts on.
  names_party: boolean;
  has_amount: boolean;
  has_deadline: boolean;
  signal_score: number;
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
  // Every list endpoint sends these (config.pagination.CountedPageNumberPagination).
  // Optional on the base type because only the feed consumes them, which keeps
  // the ~30 existing list fixtures in Watches/Clients/Digests tests valid.
  page?: number;
  total_pages?: number;
  page_size?: number;
}

/** A page whose position is guaranteed -- what the feed needs to say "N of M". */
export interface Paged<T> extends Page<T> {
  page: number;
  total_pages: number;
  page_size: number;
}

export interface VocabularyItem {
  value: string;
  label: string;
}

export interface Vocabulary {
  categories: VocabularyItem[];
}
