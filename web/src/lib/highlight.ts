/**
 * Split a string into plain and matched runs so a term can be marked without
 * `{@html}` -- the snippet is gazette text we did not author, and Svelte's
 * escaping is the only thing standing between it and the DOM.
 *
 * Folding is done one code point at a time so that an offset into the folded
 * string is an offset into the original: `'á'.normalize('NFKD')` is two units,
 * and a naive fold would shift every subsequent index.
 */
export interface Part {
  text: string;
  hit: boolean;
}

function foldChar(ch: string): string {
  const base = ch.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '');
  return base.length === ch.length ? base : ch;
}

function fold(s: string): string {
  return Array.from(s).map(foldChar).join('');
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function highlight(text: string, terms: string[]): Part[] {
  const patterns = (terms ?? [])
    .map((term) =>
      fold(term)
        .split(/\s+/)
        .filter(Boolean)
        .map(escapeRe)
        // Whitespace-flexible, same as the server-side snippet cutter.
        .join('\\s+'),
    )
    .filter(Boolean);

  if (!text || patterns.length === 0) {
    return [{ text: text ?? '', hit: false }];
  }

  const re = new RegExp(patterns.join('|'), 'g');
  const folded = fold(text);
  const parts: Part[] = [];
  let last = 0;
  for (const m of folded.matchAll(re)) {
    const start = m.index ?? 0;
    const end = start + m[0].length;
    if (start > last) parts.push({ text: text.slice(last, start), hit: false });
    parts.push({ text: text.slice(start, end), hit: true });
    last = end;
  }
  if (last < text.length) parts.push({ text: text.slice(last), hit: false });
  return parts;
}
