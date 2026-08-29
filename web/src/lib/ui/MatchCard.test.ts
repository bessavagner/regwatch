import { render, screen } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import MatchCard from './MatchCard.svelte';
import type { Match } from '../api/types';

const match: Match = {
  id: 1, watch: 2, act: 3, snippet: 'a relevant snippet', rank: 0.9,
  matched_terms: ['saneamento'],
  ai_summary: 'summary text', category: 'tender', category_label: 'licitação',
  names_party: true, has_amount: true, has_deadline: false, signal_score: 2,
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
  expect(screen.getByText(/licitação/i)).toBeInTheDocument();
  expect(screen.getByText(/new/i)).toBeInTheDocument();
});

test('MatchCard shows the act title, client, date and section', () => {
  render(MatchCard, { props: { match } });
  expect(screen.getByText(/EXTRATO DE CONTRATO Nº 9\/2026/)).toBeInTheDocument();
  expect(screen.getByText(/IFCE Crateús/)).toBeInTheDocument();
  expect(screen.getByText(/11 de agosto de 2026/)).toBeInTheDocument();
});

test('MatchCard links to the source edition', () => {
  render(MatchCard, { props: { match } });
  const link = screen.getByRole('link', { name: /source/i }) as HTMLAnchorElement;
  expect(link.href).toContain('inlabs.in.gov.br');
  expect(link.rel).toContain('noopener');
});

test('MatchCard falls back to the raw snippet when enrichment never ran', () => {
  render(MatchCard, {
    props: { match: { ...match, ai_summary: null, category: '' } },
  });
  expect(screen.getByText(/resumo indisponível/i)).toBeInTheDocument();
  // The raw snippet stands in for the missing summary.
  expect(screen.getByText('a relevant snippet')).toBeInTheDocument();
});

test('shows the category in Portuguese, never the storage enum', () => {
  render(MatchCard, { match });
  expect(screen.getByText('licitação')).toBeInTheDocument();
  expect(screen.queryByText('tender')).not.toBeInTheDocument();
});

test('MatchCard says which term matched', () => {
  render(MatchCard, { props: { match } });
  expect(screen.getByText(/encontrado por/i)).toBeInTheDocument();
  expect(screen.getByText('saneamento')).toBeInTheDocument();
});

test('MatchCard says nothing when no term was recorded', () => {
  render(MatchCard, { props: { match: { ...match, matched_terms: [] } } });
  expect(screen.queryByText(/encontrado por/i)).toBeNull();
});

test('marks the matched term inside the fallback snippet', () => {
  render(MatchCard, {
    props: {
      match: {
        ...match,
        ai_summary: null,
        snippet: 'autorizar as obras de saneamento básico',
        matched_terms: ['saneamento'],
      },
    },
  });
  const marked = document.querySelector('mark');
  expect(marked).not.toBeNull();
  expect(marked!.textContent).toBe('saneamento');
});

test('renders the snippet as text, never as markup', () => {
  render(MatchCard, {
    props: {
      match: {
        ...match,
        ai_summary: null,
        snippet: 'contrato <img src=x onerror=1> firmado',
        matched_terms: ['contrato'],
      },
    },
  });
  expect(document.querySelector('img')).toBeNull();
  expect(screen.getByText(/onerror=1/)).toBeInTheDocument();
});

test('MatchCard names the signals that fired, and only those', () => {
  render(MatchCard, { props: { match } });
  expect(screen.getByText(/parte nomeada/i)).toBeInTheDocument();
  expect(screen.getByText(/^valor$/i)).toBeInTheDocument();
  expect(screen.queryByText(/^prazo$/i)).not.toBeInTheDocument();
});
