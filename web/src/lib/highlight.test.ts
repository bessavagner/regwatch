import { expect, test } from 'vitest';
import { highlight } from './highlight';

test('marks the matched term inside the snippet', () => {
  const parts = highlight('obras de saneamento básico', ['saneamento']);
  expect(parts.map((p) => p.text).join('')).toBe('obras de saneamento básico');
  expect(parts.filter((p) => p.hit).map((p) => p.text)).toEqual(['saneamento']);
});

test('matches without regard to case or accents, and returns the original text', () => {
  const parts = highlight('Dispensa de LICITAÇÃO nesta data', ['licitação']);
  expect(parts.filter((p) => p.hit).map((p) => p.text)).toEqual(['LICITAÇÃO']);
});

test('matches a phrase across wrapped whitespace', () => {
  const parts = highlight('contrato com a BETA\n  CORP hoje', ['beta corp']);
  expect(parts.filter((p) => p.hit).map((p) => p.text)).toEqual(['BETA\n  CORP']);
});

test('returns one plain part when nothing matches', () => {
  expect(highlight('nada aqui', ['saneamento'])).toEqual([
    { text: 'nada aqui', hit: false },
  ]);
});

test('returns one plain part when there are no terms', () => {
  expect(highlight('nada aqui', [])).toEqual([{ text: 'nada aqui', hit: false }]);
});

test('does not treat a term as a regular expression', () => {
  const parts = highlight('valor de R$ 1.000 (mil reais)', ['r$ 1.000']);
  expect(parts.filter((p) => p.hit).map((p) => p.text)).toEqual(['R$ 1.000']);
});
