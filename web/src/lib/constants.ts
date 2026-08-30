// Values are the stored English enum (decision-002): the API filters on them
// literally and Match.state is written from them. Only the labels are pt-BR.
export const STATES = [
  { value: 'new', label: 'nova' },
  { value: 'relevant', label: 'relevante' },
  { value: 'dismissed', label: 'descartada' },
];

const STATE_LABELS: Record<string, string> = Object.fromEntries(
  STATES.map((s) => [s.value, s.label]),
);

// A state that arrives from the server without a label here is shown as it came
// rather than blanked -- an unknown value is worth seeing, not hiding.
export const stateLabel = (value: string): string => STATE_LABELS[value] ?? value;

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
