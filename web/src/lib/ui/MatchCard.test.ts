import { render, screen } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import MatchCard from './MatchCard.svelte';
import type { Match } from '../api/types';

const match: Match = {
  id: 1, watch: 2, act: 3, snippet: 'a relevant snippet', rank: 0.9,
  ai_summary: 'summary text', category: 'tender', confidence: 0.8,
  state: 'new', created_at: '2026-07-01T10:00:00Z',
  client_id: 7, client_name: 'IFCE Crateús',
  act_detail: {
    id: 3,
    title: 'EXTRATO DE CONTRATO Nº 9/2026',
    agency: 'Ministério da Educação',
    identifier: 'id-3',
    date: '2026-08-11',
    section: 'DO3',
    source_url: 'https://inlabs.in.gov.br/edition/DO3',
    source_anchor: '#a1',
  },
};

test('MatchCard shows snippet, summary, category and state', () => {
  render(MatchCard, { props: { match } });
  expect(screen.getByText('summary text')).toBeInTheDocument();
  expect(screen.getByText(/tender/i)).toBeInTheDocument();
  expect(screen.getByText(/new/i)).toBeInTheDocument();
});

test('MatchCard shows the act title, client, date and section', () => {
  render(MatchCard, { props: { match } });
  expect(screen.getByText(/EXTRATO DE CONTRATO Nº 9\/2026/)).toBeInTheDocument();
  expect(screen.getByText(/IFCE Crateús/)).toBeInTheDocument();
  expect(screen.getByText(/2026-08-11/)).toBeInTheDocument();
});

test('MatchCard links to the source edition', () => {
  render(MatchCard, { props: { match } });
  const link = screen.getByRole('link', { name: /source/i }) as HTMLAnchorElement;
  expect(link.href).toContain('inlabs.in.gov.br');
  expect(link.rel).toContain('noopener');
});

test('MatchCard does not claim 0% confidence when enrichment never ran', () => {
  render(MatchCard, {
    props: { match: { ...match, ai_summary: null, category: '', confidence: null } },
  });
  expect(screen.queryByText(/confidence/i)).toBeNull();
  expect(screen.getByText(/resumo indisponível/i)).toBeInTheDocument();
  // The raw snippet stands in for the missing summary.
  expect(screen.getByText('a relevant snippet')).toBeInTheDocument();
});

// The model returns 0.98-0.99 for every category including `other`, so the
// number ranked and warned about nothing while looking like a verdict. It is
// still collected on the Match; it is just not shown.
test('MatchCard never renders confidence, however high', () => {
  render(MatchCard, { props: { match: { ...match, confidence: 0.99 } } });
  expect(screen.queryByText(/confidence/i)).toBeNull();
  expect(screen.queryByText(/99/)).toBeNull();
});
