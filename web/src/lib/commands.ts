// What the command palette can show. A discriminated union rather than two
// props: routes are chosen and navigated to, shortcuts are only ever read, and
// the palette has to be able to tell them apart while filtering one list.
export type Command =
  | { kind: 'route'; label: string; path: string }
  | { kind: 'shortcut'; label: string; keys: string };

// The triage keys live here, not in Feed.svelte, so the palette is the one
// place they are described — a shortcut nobody can find is a shortcut nobody
// uses, which is how triage stayed mouse-only.
export const TRIAGE_SHORTCUTS: Command[] = [
  { kind: 'shortcut', label: 'próxima ocorrência', keys: 'J' },
  { kind: 'shortcut', label: 'ocorrência anterior', keys: 'K' },
  { kind: 'shortcut', label: 'marcar como relevante', keys: 'R' },
  { kind: 'shortcut', label: 'arquivar', keys: 'D' },
  { kind: 'shortcut', label: 'selecionar para ação em lote', keys: 'X' },
];
