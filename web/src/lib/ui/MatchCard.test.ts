import { render, screen } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import MatchCard from './MatchCard.svelte';
import type { Match } from '../api/types';

const match: Match = {
  id: 1, watch: 2, act: 3, snippet: 'a relevant snippet', rank: 0.9,
  ai_summary: 'summary text', category: 'contrato', confidence: 0.8,
  state: 'new', created_at: '2026-07-01T10:00:00Z',
};

test('MatchCard shows snippet, summary, category and state', () => {
  render(MatchCard, { props: { match } });
  expect(screen.getByText('a relevant snippet')).toBeInTheDocument();
  expect(screen.getByText('summary text')).toBeInTheDocument();
  expect(screen.getByText(/contrato/i)).toBeInTheDocument();
  expect(screen.getByText(/new/i)).toBeInTheDocument();
});
