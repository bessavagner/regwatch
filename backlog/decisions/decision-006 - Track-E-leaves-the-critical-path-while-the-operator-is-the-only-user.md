---
id: decision-006
title: Track E leaves the critical path while the operator is the only user
date: '2026-08-28 10:52'
status: accepted
---
## Context



## Decision



## Consequences


## Context

The board was written on 2026-08-26, when RegWatch had five pilot clients and 950 matches
of which 947 were untriaged. Track E (TASK-014 to TASK-020) was justified by a single
chain of reasoning: labels are the missing input to every ranking decision, only the client
can judge relevance, therefore the client needs an account, an onboarding path and a signed
link from the digest into the app. TASK-018 states it plainly — deep links were "the only
realistic route to the labelled data that D5 and every future ranking change depend on".

On 2026-08-27 and 2026-08-28 the premise changed. All five pilot clients and their watches,
1,015 matches and 61 digests were deleted; the only remaining client is Cactarus, the house
client, with four watches measured at ~9.3 matches/day. The three human labels that ever
existed went with them (preserved in .backups/, not in the database).

## Decision

**Track E leaves the critical path. The daily loop run by the operator becomes the plan.**

The reader of the digest, the person who triages the feed and the person who changes the
code are now the same person, already authenticated. Every mechanism Track E was going to
build — an account, an onboarding walk, a signed deep link that skips the password prompt —
solves a distribution problem that no longer exists. What remains is a quality problem:
whether the feed is worth reading, which is TASK-021, TASK-008, TASK-035, TASK-024,
TASK-012, TASK-006, TASK-022 and TASK-007, grouped as milestone "The signal loop".

## Consequences

**What this buys.** Labels stop depending on a beta that has not started. The operator can
triage ~9 items/day in a console they already use, so TASK-030 becomes reachable by working
on the console instead of on signup. The two tasks that make triage judgeable — TASK-021
(persist why an act matched) and TASK-008 (centre the snippet) — get much more valuable,
because the Cactarus watches carry 14 and 12 terms and a match gives no clue which one fired.

**What this costs.** The beta is postponed, not cancelled, and the reasoning in decision-001
and decision-004 stands for when it resumes. TASK-014 to TASK-020 keep their descriptions
and their place on the board.

**What was rejected.** Keeping the pilot clients alive purely as a label source. The operator
chose to delete them; the analyses of 2026-08-20 and 2026-08-26 had already shown that in
three weeks the pilots produced three labels, so the source was not producing.

**The risk being taken.** One client's feed is a narrow basis for tuning relevance. Anything
learned from the Cactarus feed is learned about four watches over Ceara procurement, LGPD,
e-SUS and federal purchasing. Ranking changes justified on it should be re-checked when a
second client exists.
