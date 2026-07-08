export const STATES = [
  { value: 'new', label: 'New' },
  { value: 'relevant', label: 'Relevant' },
  { value: 'dismissed', label: 'Dismissed' },
];

export const SECTIONS = [
  { value: '1', label: 'Seção 1' },
  { value: '2', label: 'Seção 2' },
  { value: '3', label: 'Seção 3' },
];

// Seeded free-text categories (reconciled in Phase 5 tuning); the filter is a datalist.
export const CATEGORY_SEED: string[] = ['licitação', 'contrato', 'sanção', 'pessoal', 'norma'];
