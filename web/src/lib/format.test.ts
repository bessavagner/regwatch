import { describe, expect, it } from 'vitest';
import { brDate } from './format';

describe('brDate', () => {
  it('writes the date the way Brazilians do', () => {
    expect(brDate('2026-08-26')).toBe('26 de agosto de 2026');
  });

  it('does not slip a day backwards in Brasilia time', () => {
    // A plain YYYY-MM-DD parsed as UTC midnight and rendered in America/Sao_Paulo
    // lands on the previous day. The gazette date is a calendar date, not an
    // instant, so it must render as itself.
    expect(brDate('2026-01-01')).toBe('1 de janeiro de 2026');
  });

  it('passes anything that is not a plain date straight through', () => {
    expect(brDate('')).toBe('');
    expect(brDate('nao e uma data')).toBe('nao e uma data');
  });
});
