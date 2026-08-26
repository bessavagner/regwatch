// The API sends calendar dates as plain YYYY-MM-DD. Formatting them in
// America/Sao_Paulo would be wrong twice over: `new Date('2026-08-26')` parses
// as UTC midnight, and rendering that at UTC-3 lands on the 25th. These are
// dates, not instants, so build and render them in UTC.
const BR_DATE = new Intl.DateTimeFormat('pt-BR', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
});

const PLAIN_DATE = /^(\d{4})-(\d{2})-(\d{2})/;

/** "2026-08-26" -> "26 de agosto de 2026". Anything else is returned as-is. */
export function brDate(value: string): string {
  const parts = PLAIN_DATE.exec(value);
  if (!parts) return value;
  const [, year, month, day] = parts;
  return BR_DATE.format(new Date(Date.UTC(Number(year), Number(month) - 1, Number(day))));
}
