import type { MatchParams } from './api/resources';

// Every filter the feed round-trips through the query string. `ordering` is
// here with the rest: its control has the same unbound-and-unshared defect,
// and it sits in the same group on screen.
export const FILTER_KEYS = [
  'client', 'state', 'section', 'category', 'date_from', 'date_to', 'ordering',
] as const;

export interface FeedView {
  filters: MatchParams;
  page: number;
}

/** The view a URL describes. Unset filters are absent; the page defaults to 1. */
export function viewFromQuery(search: string): FeedView {
  const params = new URLSearchParams(search);
  const filters: MatchParams = { ordering: '' };
  for (const key of FILTER_KEYS) {
    const value = params.get(key);
    if (value) filters[key] = value;
  }
  // Number('') is 0 and Number('abc') is NaN; both are falsy, so both land on
  // page 1 rather than asking the API for page NaN.
  const page = Number(params.get('page'));
  return { filters, page: page > 0 ? Math.floor(page) : 1 };
}

/** The URL a view describes: '' or a string starting with '?'. */
export function queryFromView({ filters, page }: FeedView): string {
  const params = new URLSearchParams();
  for (const key of FILTER_KEYS) {
    const value = filters[key];
    if (value) params.set(key, String(value));
  }
  // Page 1 is the default, so the unfiltered feed has a clean address.
  if (page > 1) params.set('page', String(page));
  const query = params.toString();
  return query ? `?${query}` : '';
}
