---
id: TASK-036
title: B6 · Brand the HTML digest in the RegWatch identity
status: To Do
assignee: []
created_date: '2026-08-28 11:33'
labels:
  - 'track:digest'
  - 'size:M'
dependencies:
  - TASK-025
priority: medium
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The digest is plain text and unbranded while the app has a locked design system (design.md: Lumen / Night Foundry, cool-violet near-black canvas, molten-brass accent, Instrument Serif display). The email is the only surface a client sees every day and the only one carrying no identity at all. Note this cannot be done by reusing web/src/app.css: the tokens are oklch inside a Tailwind @theme block, and email clients support neither oklch nor CSS custom properties nor reliable webfonts. The work is to derive an email-safe subset of design.md -- sRGB hex equivalents of the token palette, table layout, inline styles, system font stacks with Instrument Serif only as a progressive enhancement -- and to decide the dark-canvas question deliberately, since Gmail and Outlook invert dark palettes unpredictably and most clients open on white. Depends on TASK-025, which adds the HTML alternative part; there is nothing to style until that lands.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Email palette derived from design.md and expressed as sRGB hex; no oklch, no CSS custom properties, no required webfont
- [ ] #2 Table-based layout with inline styles, verified in Gmail, Outlook and Apple Mail
- [ ] #3 The plain-text part remains the fallback and remains readable on its own
- [ ] #4 Dark-mode rendering is a stated decision, not left to client inversion
- [ ] #5 design.md gains an Email section recording the adaptation, per its own amend-do-not-regenerate rule
<!-- AC:END -->
