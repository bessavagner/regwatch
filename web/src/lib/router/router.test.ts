import { afterEach, expect, test } from 'vitest';
import { route, navigate } from './router.svelte';

afterEach(() => {
  window.history.pushState({}, '', '/');
  route.path = '/';
});

test('navigate strips any query string from route.path so route lookup still matches', () => {
  navigate('/feed?client=3&date_from=2026-07-01&date_to=2026-07-01');
  expect(route.path).toBe('/feed');
});

test('navigate pushes the full URL, including the query string, onto history', () => {
  navigate('/feed?client=3');
  expect(window.location.pathname).toBe('/feed');
  expect(window.location.search).toBe('?client=3');
});

test('navigate to a plain path without a query string still works', () => {
  navigate('/watches');
  expect(route.path).toBe('/watches');
  expect(window.location.search).toBe('');
});
