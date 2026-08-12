# RegWatch runbook

Operator procedures. Copy-paste as written; nothing here is memorised.

> Deploy and infrastructure procedures live in `deploy/RUNBOOK.md`.

## Reindex the Portuguese search vector

Run after deploying a change to how `Act.search_vector_pt` is built, or once
after the column is first added, to backfill existing acts.

```bash
gcloud run jobs execute regwatch-migrate \
  --region us-east4 --project regwatch-501619 \
  --args=reindex_search,--batch-size,500 --wait
```

Prints one line per batch and a final total (counts are illustrative — the real
total is however many acts still have a null vector):

```
reindexed 500/25495
...
reindex_search: 25495 acts
```

Common failure: the job times out on a large backlog. Re-run it. The command
only touches acts whose vector is still null, so re-running resumes rather than
restarting. Use `--all` to force a full rebuild after changing the vector
definition.

## Roll back v0.14.0

v0.14.0 dropped `Act.search_vector`, the old `config="simple"` vector. Migration
`gazette.0005_drop_search_vector` reverses structurally, but **not
behaviourally** — reversing it re-creates the column empty, and the v0.13.0
matcher resolves every `entity` term against it. Skip the repopulation below and
every entity term silently matches nothing, for every client, with no error in
any log. Nothing self-heals: interactive backfill reuses already-ingested acts
without rebuilding vectors.

Roll the schema back one migration:

```bash
gcloud run jobs execute regwatch-migrate \
  --region us-east4 --project regwatch-501619 \
  --args=migrate,gazette,0004_pg_trgm_index --wait
```

Then **immediately** repopulate the column, or the rollback is worse than the
bug it is undoing. `search_text` is retained, so the vector is fully derivable —
read `DATABASE_URL` from Secret Manager and run:

```sql
UPDATE gazette_act SET search_vector = to_tsvector('simple', search_text);
```

Confirm none are left empty — this must return `0`:

```sql
SELECT count(*) FROM gazette_act WHERE search_vector IS NULL;
```

Common failure: rolling back further than `0004`. Reversing
`0004_pg_trgm_index` also runs `TrigramExtension()` backwards, which issues
`DROP EXTENSION pg_trgm` — a cluster-level object, not just a table. Stop at
`0004` unless you specifically intend that.

There is no point-in-time recovery and no automated backup on this project, so
take a `pg_dump` before any destructive migration (procedure in
`deploy/RUNBOOK.md`).

## Send digests through Gmail SMTP

This is how digests go out today. RegWatch owns no domain, so a transactional
API cannot be used: it refuses to send until a domain is verified. An
authenticated Gmail relay delivers now, signed by Google's DKIM.

Know what you are accepting: SMTP answers `250 OK` and tells you nothing after
that. **There are no bounce or complaint callbacks** — a full mailbox or a
spam-marking is invisible. Gmail also caps you at roughly 500 recipients/day and
rewrites `From` to the authenticated account unless the address is a verified
"Send mail as" alias. When RegWatch has its own domain, move to the section
below and flip `REGWATCH_EMAIL_SENDER` back.

**1. Mint a Gmail app password.** 2-Step Verification must already be on for the
account. Go to <https://myaccount.google.com/apppasswords>, create one named
`regwatch`, and copy the 16-character value. It is shown once. This is not your
account password, and it can be revoked on its own.

**2. Store the SMTP config.** Use `printf`, never `echo` — `echo` appends a
newline that Cloud Run injects verbatim into the env var, and no dashboard or
`.env` comparison will show it to you. Google displays the app password in
four space-separated groups; **strip the spaces**:

```bash
printf '%s' 'smtp.gmail.com'                  | gcloud secrets versions add SMTP_HOST     --data-file=- --project regwatch-501619
printf '%s' 'bessavagner@gmail.com'           | gcloud secrets versions add SMTP_USER     --data-file=- --project regwatch-501619
printf '%s' 'abcdefghijklmnop'                | gcloud secrets versions add SMTP_PASSWORD --data-file=- --project regwatch-501619
printf '%s' 'RegWatch <bessavagner@gmail.com>' | gcloud secrets versions add SMTP_FROM    --data-file=- --project regwatch-501619
```

Creating the secrets for the first time (they do not exist yet) needs one
`gcloud secrets create <NAME> --replication-policy=automatic` each, plus a
`secretAccessor` binding for `regwatch-run@regwatch-501619.iam.gserviceaccount.com`.
`deploy/provision.sh` does both, and is the source of truth for the full list.

**3. Point the jobs and the API at the SMTP sender, and mount the new secrets.**
CI only ever updates `--image` and `--args`, so this must be applied by hand —
`provision.sh` is not run by CI:

```bash
SECRETS=SMTP_HOST=SMTP_HOST:latest,SMTP_USER=SMTP_USER:latest,SMTP_PASSWORD=SMTP_PASSWORD:latest,SMTP_FROM=SMTP_FROM:latest
for job in regwatch-run-daily regwatch-heartbeat regwatch-migrate; do
  gcloud run jobs update "$job" --region us-east4 --project regwatch-501619 \
    --update-secrets="$SECRETS" \
    --update-env-vars=REGWATCH_EMAIL_SENDER=digests.smtp.SmtpEmailSender
done
gcloud run services update regwatch-api --region us-east4 --project regwatch-501619 \
  --update-secrets="$SECRETS" \
  --update-env-vars=REGWATCH_EMAIL_SENDER=digests.smtp.SmtpEmailSender
```

Use `--update-secrets` / `--update-env-vars`, **not** `--set-secrets` /
`--set-env-vars`: the `set-` forms replace the whole collection and would drop
`DATABASE_URL` and `SECRET_KEY`, leaving the job unable to start.

**4. Confirm end to end** on a date you know produced matches:

```bash
gcloud run jobs execute regwatch-run-daily \
  --region us-east4 --project regwatch-501619 --wait
```

Success is a summary line with a non-zero digest count, and mail in the inbox:

```
run_daily 2026-08-03: editions=3 acts=3187 matches=4 enriched=4 digests=1
```

Common failure: `SMTPAuthenticationError: 535 Username and Password not accepted`.
Almost always the app password was stored with its display spaces left in, or
with a trailing newline from `echo`. Re-add it with `printf` and no spaces.
Check what is actually stored — the count must be 16, not 19:

```bash
gcloud secrets versions access latest --secret=SMTP_PASSWORD --project regwatch-501619 | wc -c
```

A `wc -c` of 17 means a trailing newline slipped in; 19 means the spaces are
still there.

Second failure: sends succeed but nothing arrives. Check the recipient's spam
folder first — a `@gmail.com` sender mailing a corporate domain about regulatory
acts is exactly the shape a filter distrusts. This is the deliverability tax of
having no domain, and it is the reason to finish the section below.

## What the heartbeat now asserts

`check_heartbeat` used to pass whenever a `status="success"` row existed for the
date. That is a dead-man's switch on the *process*, not on the *product*: on
2026-08-11 the run exited zero, logged `success`, and delivered nothing. It now
asserts delivery, and fails with one of three messages.

**`heartbeat: no completed scheduled RunLog for <date>`**
The scheduled run never finished — it crashed, or Cloud Scheduler never fired
it. Neither `success` nor `partial` was recorded. Start with the job's own logs:

```bash
gcloud run jobs executions list --job=regwatch-run-daily --region=us-east4 --limit=5
gcloud logging read \
  'resource.type="cloud_run_job" AND severity>=ERROR' \
  --limit 20 --freshness=1d --format='value(timestamp,jsonPayload.message)'
```

Remember the 13:00 midday run is the safety net for a failed 08:05 run, and the
heartbeat only fires at 14:00 — so a failure here means *both* runs missed.

**`heartbeat: run for <date> was partial — <reason>`**
The run completed but delivered or enriched less than it matched. The reason is
copied verbatim from `RunLog.errors` and reads either `N matches not enriched`
or `N digests not sent` (or both, semicolon-separated).

For *digests not sent*, the cause is on the row — `Digest.send_error` now holds
the provider's own words. Read it, fix the cause, then:

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=resend_digests,--date-from=<date>,--date-to=<date>
```

For *matches not enriched*, both LLM providers refused. The refusal body is now
logged rather than swallowed:

```bash
gcloud logging read \
  'resource.type="cloud_run_job" AND (jsonPayload.logger="enrichment.fallback"
   OR textPayload:"refused the request")' \
  --limit 10 --freshness=1d --format='value(timestamp,jsonPayload.message)'
```

A `falling back to the secondary provider` warning without a `partial` status is
healthy — that is the fallback doing its job.

**`heartbeat: N undelivered digest(s) for <date>`**
The run recorded clean counts but a digest for that date is still `sent=False` —
typically a retry that failed after the run wrote its counters. Same fix as
above: read `send_error`, then `resend_digests`.

## Rotate the Gmail app password

Do this when `SMTPAuthenticationError: (535, '5.7.8 Username and Password not
accepted')` appears in the `run_daily` logs, or after any change to the Google
account password — **Google silently revokes every app password when the account
password changes**, and the only symptom is a 535 on the next scheduled run.
Between 2026-08-05 and 2026-08-11 that revocation went unnoticed and cost six
digests.

**1. Mint a replacement.** At <https://myaccount.google.com/apppasswords>, revoke
the old `regwatch` entry and create a new one. Put the 16-character value into
`.env` as `SMTP_PASSWORD` (Gmail accepts it with or without the display spaces).
`.env` is gitignored and stays that way — never paste the value into a tracked
file, a commit message, or a log line.

**2. Push new secret versions from `.env`.** Run this under **bash**, not zsh:
`${!name}` is bash indirect expansion, and zsh spells it `${(P)name}`.

```bash
bash -c '
set -a; . ./.env; set +a
for s in SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD SMTP_STARTTLS SMTP_FROM OPENAI_API_KEY; do
  printf "%s" "${!s}" | gcloud secrets versions add "$s" --data-file=- 2>/dev/null \
    || printf "%s" "${!s}" | gcloud secrets create "$s" --replication-policy=automatic --data-file=-
done
'
```

`printf "%s"` rather than `echo` is deliberate: a trailing newline inside
`SMTP_PASSWORD` is itself a cause of 535.

Verify without printing any value:

```bash
for s in SMTP_PASSWORD OPENAI_API_KEY; do
  printf '%s: %s bytes\n' "$s" "$(gcloud secrets versions access latest --secret=$s | wc -c)"
done
```

Expected: `SMTP_PASSWORD: 16 bytes` (19 if you kept the display spaces, which
also works) and a non-zero `OPENAI_API_KEY`. A count of 17 means a newline
slipped in — redo step 2.

**3. Deploy, then confirm the credential.** Push a `vX.Y.Z` tag to trigger the
pipeline (see "Roll back v0.14.0" above for the tag mechanics), then:

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait
gcloud logging read \
  'resource.type="cloud_run_job" AND jsonPayload.logger="digests.notifier"' \
  --limit 5 --freshness=1h --format='value(timestamp,jsonPayload.message)'
```

Expected: no `digest send failed` entries. Any that appear now carry the
provider's own words, and the same text is stored on `Digest.send_error`.

**4. Drain whatever the outage stranded.**

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=resend_digests,--date-from=2026-08-05,--date-to=2026-08-11
```

Expected output: `resend_digests 2026-08-05..2026-08-11: resent 6 of 6`. Confirm
in the dashboard that no digest still reads "not sent", **and confirm the mail
actually arrived** — SMTP answers `250 OK` and tells you nothing afterwards.

From v0.15.0 on, `run_daily` sweeps the previous `REGWATCH_DIGEST_RETRY_DAYS`
days (default 7) on every run, so a fixed credential drains its own backlog
without this command. Reach for `resend_digests` when the outage ran longer than
the window, or when you want a specific client re-sent (`--client <id>`).

## Verify a sending domain in Resend

Do this when RegWatch has a domain of its own. It is the exit from the Gmail
relay above: a verified domain buys aligned SPF/DKIM, bounce and complaint
webhooks, and a `From` that carries the product's name instead of a personal
Gmail address.

`digests/resend.py` and its tests are kept for exactly this — the sender is
selected by the `REGWATCH_EMAIL_SENDER` env var, so switching back is a config
change, not a rewrite. Until this is done, `RESEND_FROM` is Resend's sandbox
address `onboarding@resend.dev`, which may only email the address that owns the
Resend account; every other recipient is rejected with `403 Forbidden`.

You need a domain you control and access to its DNS. The API key already in
Secret Manager is enough to drive the whole flow.

**1. Register the domain with Resend.** Substitute your domain and region:

```bash
KEY=$(gcloud secrets versions access latest --secret=RESEND_API_KEY --project regwatch-501619)
curl -s -X POST https://api.resend.com/domains \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"name":"regwatch.com.br","region":"sa-east-1"}' | jq
```

The response carries the domain `id` and a `records` array — typically a DKIM
`TXT` on `resend._domainkey`, an SPF `TXT` on `send`, and an `MX` on `send`:

```json
{
  "id": "d91cd9bd-1176-453e-8fc1-35364d380206",
  "name": "regwatch.com.br",
  "status": "not_started",
  "records": [
    {"record": "DKIM", "name": "resend._domainkey", "type": "TXT", "value": "p=MIGfMA0GCSq..."},
    {"record": "SPF",  "name": "send", "type": "TXT", "value": "v=spf1 include:amazonses.com ~all"},
    {"record": "SPF",  "name": "send", "type": "MX",  "value": "feedback-smtp.sa-east-1.amazonses.com", "priority": 10}
  ]
}
```

**2. Add every record above at your DNS provider, exactly as given.** This is
the only manual step and the only one that can take time to propagate.

**3. Ask Resend to verify**, using the `id` from step 1:

```bash
curl -s -X POST https://api.resend.com/domains/d91cd9bd-1176-453e-8fc1-35364d380206/verify \
  -H "Authorization: Bearer $KEY" | jq
```

Poll until `status` is `verified` — minutes to a few hours depending on your TTL:

```bash
curl -s https://api.resend.com/domains -H "Authorization: Bearer $KEY" \
  | jq '.data[] | {name, status}'
```

```
{ "name": "regwatch.com.br", "status": "verified" }
```

**4. Point `RESEND_FROM` at the verified domain.** Use `printf`, never `echo` —
`echo` appends a newline, which Cloud Run injects verbatim into the env var and
which no dashboard or `.env` comparison will show you:

```bash
printf '%s' 'RegWatch <digest@regwatch.com.br>' \
  | gcloud secrets versions add RESEND_FROM --data-file=- --project regwatch-501619
```

No redeploy is needed: the jobs mount the secret as `RESEND_FROM:latest`, so the
next execution picks up the new version.

Then switch the sender back off SMTP, on every job and the API:

```bash
for job in regwatch-run-daily regwatch-heartbeat regwatch-migrate; do
  gcloud run jobs update "$job" --region us-east4 --project regwatch-501619 \
    --update-env-vars=REGWATCH_EMAIL_SENDER=digests.resend.ResendEmailSender
done
gcloud run services update regwatch-api --region us-east4 --project regwatch-501619 \
  --update-env-vars=REGWATCH_EMAIL_SENDER=digests.resend.ResendEmailSender
```

Update `ENV_FLAGS` in `deploy/provision.sh` to match, or the next provisioning
run silently reverts you to SMTP.

**5. Confirm end to end** by running the pipeline for a date you know produced
matches:

```bash
gcloud run jobs execute regwatch-run-daily \
  --region us-east4 --project regwatch-501619 --wait
```

Success is a summary line with a non-zero digest count:

```
run_daily 2026-08-03: editions=3 acts=3187 matches=4 enriched=4 digests=1
```

Common failure: `status` stays `pending` or flips back to `failure` because the
DNS records were added under the wrong parent — providers that auto-append the
zone turn `resend._domainkey` into `resend._domainkey.regwatch.com.br.regwatch.com.br`.
Check with `dig +short TXT resend._domainkey.regwatch.com.br` before re-verifying.

Second failure to know: a send can still be refused after the domain verifies,
if `RESEND_FROM` uses a different domain than the verified one. The refusal is
logged with Resend's own explanation and the `from` address that was used —
grep the run logs for `Resend refused the send`. A failed send no longer aborts
the run: the digest row is kept unsent and retried on the next execution.
