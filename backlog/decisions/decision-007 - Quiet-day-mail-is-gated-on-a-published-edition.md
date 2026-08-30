---
id: decision-007
title: Quiet-day mail is gated on a published edition
date: '2026-08-30 15:16'
status: accepted
---
## Context

`build_and_send_digests` builds its `by_client` map by iterating *matches*, so a
client with no matches on a date never enters the map: no `Digest` row is
written and no email is sent. Silence therefore means both "the DOU published
and nothing concerned you" and "RegWatch is broken", and the reader cannot tell
which. That is TASK-012.

It is also why TASK-028 had nothing to alert on. `check_heartbeat` already fails
on `status == "partial"` and on any `Digest` row for the date with `sent=False`,
and `deploy/policy-heartbeat-failed.json` already pages when that job fails. The
alerting was built; the row it inspects was never written.

TASK-012's acceptance criterion says "every client with an email address gets a
message every publication day". That names two kinds of day. There are three:

| Day | Before | After |
|---|---|---|
| Matches found | digest sent | unchanged |
| DOU published, nothing matched | silence | quiet-day message |
| DOU did not publish (weekend, holiday) | silence | still silence |

## Decision

The quiet-day message is gated on `Edition.objects.filter(date=date).exists()`.

A client hears from us on a date when an edition was ingested for that date and
they have at least one **active** watch. Both halves are load-bearing:

- **No edition, no message.** Sending "your watches found nothing today" on a
  Sunday or a national holiday is not reassurance, it is noise — and a reader
  who learns to ignore the message has lost exactly the signal B3 exists to
  give them. "Publication day" in the acceptance criterion means a day the DOU
  published, not a day the clock advanced.
- **No active watch, no message.** Nothing ran, so "the watches ran and found
  nothing" would be false.

A quiet digest is only written for a client with an email address. A client with
matches and no email still gets its row built and left unsent, as before — that
is a fault worth surfacing. A client with *no* matches and no email gets
nothing: writing a row we can never deliver would leave it `sent=False` forever
and fail `check_heartbeat` every single day, which would destroy the
dead-man's-switch this change exists to feed.

The quiet body is a separate template, `digests/quiet.txt`, not a conditional
branch inside `daily.txt`. Nothing is added to the schema: a quiet digest is
distinguishable by having no matches for its client and date, and the message
itself is what the reader needs to be able to tell the difference.

## Consequences

- `run_daily`'s `log.digests` and `log.digests_sent` now count quiet digests.
  This is the point: a delivery that fails on a quiet day is now visible as a
  `partial` run instead of being indistinguishable from a day with nothing to
  say.
- `check_heartbeat` gains real coverage of delivery without any change to
  `check_heartbeat` itself.
- `POST /api/digests/send/` no longer 404s for a client with no matches on a
  date that published; it sends the quiet digest. The 404 now means "that date
  published nothing", which is the honest reading of an empty result.
- Mail volume rises to roughly one message per client per weekday. With one
  client that is nothing; it is worth revisiting before the list is large.
- Cost: an operator who wants "tell me only when something happened" cannot get
  it. That is deliberate — it is the setting that produced the ambiguity.

Implemented by TASK-012 and verified by TASK-028.
