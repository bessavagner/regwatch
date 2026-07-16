export const STATES = [
  { value: 'new', label: 'new' },
  { value: 'relevant', label: 'relevant' },
  { value: 'dismissed', label: 'dismissed' },
];

// Values match the real INLABS pipeline edition codes (src/gazette/inlabs/fetch.py
// SECTIONS) that get written to Edition.section — the matcher compares them literally.
export const SECTIONS = [
  { value: 'DO1', label: 'seção 1' },
  { value: 'DO2', label: 'seção 2' },
  { value: 'DO3', label: 'seção 3' },
  { value: 'DO1E', label: 'seção 1 extra' },
  { value: 'DO2E', label: 'seção 2 extra' },
  { value: 'DO3E', label: 'seção 3 extra' },
];

// Seeded free-text categories (reconciled in Phase 5 tuning); the filter is a datalist.
export const CATEGORY_SEED: string[] = ['licitação', 'contrato', 'sanção', 'pessoal', 'norma'];
