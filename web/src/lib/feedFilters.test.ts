import { expect, test } from 'vitest';
import { queryFromView, viewFromQuery } from './feedFilters';

test('reads every filter out of the query string', () => {
  const { filters } = viewFromQuery(
    '?client=3&state=new&section=DO1&category=tender&date_from=2026-07-01&date_to=2026-07-02&ordering=rank',
  );
  expect(filters).toEqual({
    client: '3', state: 'new', section: 'DO1', category: 'tender',
    date_from: '2026-07-01', date_to: '2026-07-02', ordering: 'rank',
  });
});

test('an absent query string is the unfiltered first page', () => {
  expect(viewFromQuery('')).toEqual({ filters: { ordering: '' }, page: 1 });
});

test('reads the page number', () => {
  expect(viewFromQuery('?page=4').page).toBe(4);
});

test('a junk or zero page falls back to page 1 rather than asking for page NaN', () => {
  expect(viewFromQuery('?page=abc').page).toBe(1);
  expect(viewFromQuery('?page=0').page).toBe(1);
  expect(viewFromQuery('?page=-2').page).toBe(1);
});

test('writes only the filters that are set', () => {
  const query = queryFromView({ filters: { state: 'relevant', ordering: '' }, page: 1 });
  expect(query).toBe('?state=relevant');
});

test('leaves page 1 out of the URL so the default view has a clean address', () => {
  expect(queryFromView({ filters: { ordering: '' }, page: 1 })).toBe('');
  expect(queryFromView({ filters: { ordering: '' }, page: 3 })).toBe('?page=3');
});

test('an empty view is an empty query string, not a bare question mark', () => {
  expect(queryFromView({ filters: {}, page: 1 })).toBe('');
});

test('round-trips a full view back to itself', () => {
  const view = {
    filters: {
      client: '3', state: 'new', section: 'DO1', category: 'tender',
      date_from: '2026-07-01', date_to: '2026-07-02', ordering: 'rank',
    },
    page: 2,
  };
  expect(viewFromQuery(queryFromView(view))).toEqual(view);
});
