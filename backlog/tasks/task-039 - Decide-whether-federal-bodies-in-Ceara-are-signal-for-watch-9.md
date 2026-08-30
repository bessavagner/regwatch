---
id: TASK-039
title: Decide whether federal bodies in Ceara are signal for watch 9
status: To Do
assignee: []
created_date: '2026-08-30 14:57'
labels:
  - 'track:signal'
  - 'size:S'
dependencies: []
priority: medium
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Watch 9 (Cactarus, DO3) currently returns 22 acts over 2026-08-24 -> 08-28. Seventeen are municipal procurement from the 13 target municipalities. The other five come from federal or state bodies that are physically in Ceara and happen to name a target municipality: two Universidade Federal do Ceara acts (an AVISO DE LICITACAO and an EXTRATO DE TERMOS ADITIVOS), a DNIT Superintendencia Regional no Ceara permissao especial de uso, a Justica Federal Secao Judiciaria do Ceara extrato de termo aditivo, and an MCom Secretaria de Radiodifusao edital.

This is the residual question left over from TASK-035 (D8). It is a product call, not a code one: does Cactarus want federal spend landing in the region, or only municipal procurement in the 13 towns? Nothing is broken either way - the watch works as configured.

Measured cost of narrowing: swapping the 'Ceara' term for an agency entity term on 'Prefeituras/Estado do Ceara' yields exactly those 17 municipal acts and drops all 5 federal ones (both=17, only_current=5, only_new=0). So the narrowing is available and precise if the answer is 'noise' - but it is a strict loss of recall, not a precision/recall trade.

Do NOT drop the 'Ceara' group entirely as a way of narrowing: that widens to 48 acts with Hidrolandia/GO, Porangatu/GO, Nova Independencia/SP, Itaporanga/PB and Perobal/PR in the results. Full measurement in TASK-035's implementation notes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The client has said whether federal/state acts in Ceara belong in watch 9
- [ ] #2 Watch 9 config reflects that answer, or is deliberately left unchanged with the reason recorded
<!-- AC:END -->
