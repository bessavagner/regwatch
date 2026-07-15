# Design — RegWatch

A locked design system for the RegWatch web dashboard (`web/`). Every page redesign
reads this file before emitting code. Do not regenerate per page — extend or amend
this file when the system needs to grow.

**Revision history:** v1 was Cobalt (modern-minimal) — correct restraint for daily
internal-tool use, but read as "plain" for demo purposes. v2 (current) moves to
Lumen (atmospheric) for attention-grabbing demos while keeping the same components,
routes, and information architecture. See § Revision note below for what carried over.

## Genre

**atmospheric** (was modern-minimal) — RegWatch's job is literally to *watch* for a
signal in a stream of noise (regulatory publications). Atmospheric's "instrument you'd
want to be seen using after dark" register fits that better than modern-minimal's
enterprise restraint, and is a decisive visual break from "plain dev layout."

## Macrostructure family

Still no marketing pages — every route is a functional app screen. Hallmark's 21
macrostructures are landing-page shapes; the pick below is a loose label for the
overall shape, not a literal template.

- **App pages** (Triage / Watches / Clients / Digests): **Workbench** (unchanged from
  v1) — Lumen's own affinity list includes Workbench "when the page has live product
  UI to show." Shape: compact page header → optional toolbar → a hairline-with-inner-
  emission list panel → pagination where applicable.
- **Triage only** carries Lumen's hero-scale signature moves (see § Apparatus below) —
  it's the landing page after login and the one place a first-impression "wow" moment
  belongs. Watches/Clients/Digests inherit the token system but not the hero
  apparatus/meter-strip/blueprint-grid moves — those are hero-specific, not app-wide.
- **Auth page** (Login): **Split Studio** (diptych) — deliberately a different
  macrostructure from Workbench (diversification), and the correct shape for a page
  whose job is "state the brand, then ask for one action." Left pane: mono eyebrow +
  lowercase serif headline with one verb-landmark ("start **watching**") + lede, on
  the same blueprint-grid + emit-wash canvas as Triage's hero. Right pane: the actual
  sign-in form in a `.panel`. No apparatus/stat-row here — there's no real data to
  show before authentication, and Lumen's own rule is never fabricate one. Collapses
  to a single column (brand above, form below) under 60rem.

## Theme

Catalog theme: **Lumen**, **Night Foundry** drop (atmospheric cluster). Cool-violet
near-black canvas, molten-brass accent that *emits*, Instrument Serif display,
hand-built apparatus instead of a generic glow/orb. Differs from v1's Cobalt on all
three diversification axes: paper band (dark vs. light), display style (classical-
serif-lowercase vs. grotesk-sans), accent hue (warm brass ~50° vs. cool electric-blue
~256°).

- `--color-paper`       oklch(13% 0.014 265)
- `--color-paper-2`     oklch(17% 0.016 265)
- `--color-paper-3`     oklch(21% 0.018 265)
- `--color-ink`         oklch(96% 0.006 262)
- `--color-ink-2`       oklch(84% 0.010 262)
- `--color-rule`        oklch(96% 0.006 262 / 0.10)
- `--color-rule-2`      oklch(96% 0.006 262 / 0.16)
- `--color-muted`       oklch(70% 0.012 262)
- `--color-accent`      oklch(76% 0.170 50)   /* molten brass — emits */
- `--color-accent-ink`  oklch(16% 0.020 50)   /* dark text on brass-filled buttons */
- `--color-accent-2`    oklch(68% 0.160 18)   /* coral chord — verb-landmark only, never buttons */
- `--color-glow`         oklch(80% 0.160 50 / 0.42)
- `--color-paper-emit`   oklch(76% 0.170 50 / 0.04)
- `--rule-blueprint`     oklch(96% 0.006 262 / 0.04)
- `--color-success`      oklch(72% 0.150 152)
- `--color-success-bg`   oklch(25% 0.040 152)
- `--color-danger`       oklch(70% 0.180 25)
- `--color-danger-bg`    oklch(28% 0.060 25)
- `--color-neutral-bg`   oklch(22% 0.014 262)
- `--color-neutral-text` oklch(78% 0.010 262)
- `--color-accent-2-bg`  oklch(28% 0.050 18)  /* "house"/pending badge tint — replaces v1's blue, Lumen has no blue */

**Disclosed adaptation from the theme spec:** Lumen's typography rule is lowercase
*everything* (headlines, body, nav, brand, person/entity names). Applied here to **UI
chrome I author** — nav labels, page titles, buttons, empty-state copy, mono labels.
**Not** applied to **live data** — client names, watch terms, regulatory snippet/AI-
summary text — since forcing real proper nouns and government-source text lowercase
for typographic purity would misrepresent the data. This is a scoped, disclosed
exception, not a silent drift from the theme.

## Apparatus (Triage hero only)

One hand-built instrument, per Lumen's "never a generic orb" rule: a **signal dial** —
a circular gauge with tick marks and an active arc, reading as an oscilloscope/analogue
meter. Represents "watching for a signal in the noise," RegWatch's core metaphor.
Leader-line callouts carry real values only (see Feed.svelte): match count, watch
count, client count — never invented numbers. Night Foundry physics: pulses (3%
intensity, 4s period), never rotates.

Above the apparatus: mono eyebrow (`00 · SIGNAL`), lowercase Instrument Serif headline
with exactly one verb in `--color-accent-2` + drawn underline (e.g. "built to
**watch**, in real time."). Below: a three-stat row (matches / watches / clients — all
real, fetched, never fewer than three or the row is skipped per Lumen's rule).
Blueprint grid + emit wash background, contained via `overflow: clip` so the halo
doesn't bleed into the list below.

## Typography

- Display: **Instrument Serif** 400, normal (never italic — Lumen retires the italic
  pivot; the verb landmark is colour + underline), **lowercase** — page titles,
  apparatus headline.
- Body: **Geist** 400/500 — all UI chrome text (lowercase), unchanged live-data text.
- Mono: **JetBrains Mono** 400/500, **UPPERCASE** — eyebrows, callouts, meter labels,
  badges, counts, dates. The two-register split (lowercase prose / uppercase mono) is
  the typographic signature — carried over and sharpened from v1's mono-label habit.
- Tabular numerics on every count, date, confidence percentage.

## Spacing

4-point named scale — unchanged from v1, see `tokens.css`.

## Motion

- Easings: `--ease-out` / `--ease-in` / `--ease-in-out`, plus `--ease-soft` for card
  hover (Lumen-specific, gentler).
- Apparatus: pulse only (3% intensity, 4s period), never rotates. Reduced motion:
  freezes at max intensity.
- Verb-landmark underline: draws in once (320ms, 900ms delay) on first paint, then
  static.
- Cards: `translateY(-4px)` + inner-glow brighten (6% → 12% accent opacity) on hover,
  220ms `--ease-soft`.
- List rows: fade + rise on first load only (unchanged from v1), capped ~400ms total.
- ⌘K palette: instant open, arrow-key highlight transition only (120ms) — unchanged.
- Reduced-motion fallback: all pulses/reveals collapse to final state instantly.

## Microinteractions stance

Unchanged from v1: silent success, optimistic triage actions with rollback + Undo,
instant focus rings, 800ms/0ms tooltip delay split (hover/focus).

## CTA voice

- Primary: solid `--color-accent` (brass) fill, `--color-accent-ink` (dark) text, 8px
  radius. Never a pill.
- Secondary / ghost: transparent, `--color-ink-2` text, hairline border on hover.
- Verb-landmark colour (`--color-accent-2`, coral) is reserved for the apparatus
  headline only — never buttons, never more than one word per page.

## Per-page allowances

- Triage: the only page carrying apparatus/meter-strip/blueprint-grid enrichment.
- Watches/Clients/Digests/Login: token system only (dark paper, Instrument Serif
  titles, hairline-with-inner-emission cards, mono labels) — no enrichment.

## What pages MUST share

- Dark violet paper + molten-brass accent + Instrument Serif page titles.
- The lowercase-chrome / UPPERCASE-mono two-register typographic split.
- The hairline-with-inner-emission card/row treatment (1px rule + 4–6% accent radial,
  brightening to 10–12% on hover) — replaces v1's flat hairline-only rows.
- The 8-state discipline on every interactive control.

## What pages MAY differ on

- Toolbar composition (unchanged from v1).
- Whether a create/edit form panel sits above the list (Watches, Clients) or not
  (Digests, Triage).

## Nav

**N5 Floating pill** (was: Cobalt's bordered top bar) — Lumen/atmospheric's genre
default. Detached from the viewport edge, blur backdrop, sits over the dark canvas so
the emit-wash glows through it. Wordmark (`regwatch`, lowercase Instrument Serif) +
four route links + bordered ⌘K pill + ghost "log out." Active route: brass underline.
Working ⌘K/Ctrl+K command palette carried over unchanged (retokened).

No footer — unchanged reasoning from v1 (authed internal tool).

## Exports

Canonical source is `web/tokens.css`. Formats below are derived from it.

### Tailwind v4 `@theme`

```css
@theme {
  --color-paper:   oklch(13% 0.014 265);
  --color-ink:     oklch(96% 0.006 262);
  --color-accent:  oklch(76% 0.17 50);
  --font-display:  "Instrument Serif", serif;
  --font-body:     "Geist", sans-serif;
  --spacing-md:    1rem;
  --text-md:       1.25rem;
  --ease-out:      cubic-bezier(0.16, 1, 0.3, 1);
}
```

### DTCG `tokens.json`

```json
{
  "color": {
    "paper":  { "$value": "oklch(13% 0.014 265)", "$type": "color" },
    "ink":    { "$value": "oklch(96% 0.006 262)", "$type": "color" },
    "accent": { "$value": "oklch(76% 0.17 50)", "$type": "color" }
  },
  "font": {
    "display": { "$value": "Instrument Serif", "$type": "fontFamily" },
    "body":    { "$value": "Geist", "$type": "fontFamily" }
  },
  "space": {
    "md": { "$value": "1rem", "$type": "dimension" }
  }
}
```

### shadcn/ui CSS variables

```css
:root {
  --background:         13%  0.014 265;
  --foreground:         96%  0.006 262;
  --primary:            76%  0.170 50;
  --primary-foreground: 16%  0.020 50;
  --muted:               22% 0.014 262;
  --muted-foreground:    70% 0.012 262;
  --border:              96% 0.006 262 / 0.10;
  --input:               96% 0.006 262 / 0.16;
  --ring:                76% 0.170 50;
  --radius:              8px;
}
```

## Revision note (v1 → v2)

Carried over unchanged: routes/components (no deletions), ⌘K palette behaviour, list
pagination, form validation/error patterns, 8-state control discipline, 4pt spacing
scale, badge semantics (success/danger/neutral, now re-tuned for dark), microinteraction
stance. Changed: genre, theme, all colour tokens, display font, nav archetype, card
treatment (hairline-only → hairline + inner emission), one new hero enrichment
(Triage's apparatus + stat row) sourced from real counts already available to the app.
