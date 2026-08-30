# RegWatch runbook

Operator procedures. Copy-paste as written; nothing here is memorised.

> Deploy and infrastructure procedures live in `deploy/RUNBOOK.md`.

## Reindex the Portuguese search vector

Run after deploying a change to how `Act.search_text` or `Act.search_vector_pt`
is built, or once after the column is first added, to backfill existing acts.
Rebuilds both columns: `search_text` (lowercased, accent-stripped, used by
substring/entity terms) and `search_vector_pt` (the `portuguese` tsvector used
by concept terms and by ranking).

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

Common failure: the job times out on a large backlog. Re-run it. Without
`--all` the command only touches acts whose vector is still null, so re-running
resumes rather than restarting. Use `--all` to force a full rebuild after
changing the *definition* of either column — as v0.20.0 did when it folded
`agency` in. Acts whose text has been pruned (`prune_act_text`) are skipped in
both modes and stay pruned; that is deliberate, not a miss.

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

## Add a secret to the deployment

Declare it in **`deploy/secrets.list`** and nowhere else. `provision.sh`,
`deploy-api.sh` and `.github/workflows/deploy.yml` all read that file through
`deploy/secrets-lib.sh`, so one line plus a tag push is the whole change.

```bash
echo 'MY_NEW_SECRET' >> deploy/secrets.list
printf '%s' 'the-value' | gcloud secrets create MY_NEW_SECRET \
  --replication-policy=automatic --data-file=-
gcloud secrets add-iam-policy-binding MY_NEW_SECRET \
  --member="serviceAccount:regwatch-run@regwatch-501619.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
git commit -am 'chore(deploy): mount MY_NEW_SECRET' && git push && git tag vX.Y.Z && git push origin vX.Y.Z
```

The Secret Manager entry and the IAM binding are still manual — the deploy
mounts secrets, it does not create them. A secret listed but not created makes
the deploy fail loudly on `--set-secrets`, which is the intended failure mode.

Verify what a job actually has mounted:

```bash
gcloud run jobs describe regwatch-run-daily --region=us-east4 \
  --format='value(spec.template.spec.template.spec.containers[0].env)' \
  | tr ',' '\n' | grep -oE "'name': '[A-Z_]+'" | sed "s/'name': '//;s/'//" | sort -u
```

**Why this file exists.** The list used to live only in `provision.sh`, a
one-shot script CI never re-runs, while the deploy updated just image and args.
On 2026-08-12 three secrets added to `provision.sh` were therefore never mounted,
and two of the failures were silent until a run died: a missing `OPENAI_API_KEY`
took down the entire daily run, and missing `INLABS_*` on the API service broke
the "Run on past editions" backfill endpoint. If you find yourself adding a
secret name to a second place, that is the bug coming back.

## Change an existing watch

Re-point a watch's terms, tighten its excludes, or stop it matching. Only the
fields you name are touched.

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args='^@^update_watch@--watch@14@--groups@entity:Crateús|Ipueiras;concept:convênio@--apply'
```

The same two separator rules as `create_watch` apply: `^@^` for gcloud's own
delimiter, and the singular-flag forms `--groups` / `--excludes` because gcloud
refuses a repeated flag inside `--args`.

**Always dry-run first.** Without `--apply` it prints before and after for every
field it would change:

```
watch 14 (Cactarus):
  groups:
    before [{"terms": [{"text": "Pentecoste", "kind": "entity"}]}]
    after  [{"terms": [{"text": "Crateús", "kind": "entity"}]}]
dry run, nothing written -- re-run with --apply
```

`--excludes` replaces the list; to empty it use `--clear-excludes`, since an
empty string cannot express "remove them all". `--inactive` stops a watch
matching without deleting it or its history — the right way to retire a watch
that turned out to be wrong.

**The common failure** is `nothing to change; name at least one of ...`, which
means every flag you passed was a no-op — usually `--excludes ""` where
`--clear-excludes` was meant.

## Evaluate a watch against past publications

Answers "would this watch have fired, and on what" before a new watch is left
running for a week. Matches only — it sends nothing to the LLM and needs no
provider credentials.

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=backfill_watches,--client,7,--date-from,2026-08-24,--date-to,2026-08-28,--apply
```

It prints the totals, then the line that matters — one row per watch, including
the ones that matched nothing:

```
per watch, 2026-08-24 -> 2026-08-28:
  watch 14      6 match(es)  [DO1] Pentecoste, Coreaú, ...
  watch 15      0 match(es)  [DO1] sistema eletrônico, ...
```

A zero is a result, not an error: it means the terms never fired, which is what
you want to learn before the watch has been live for a week.

**Where the acts come from matters for what the number means.** `backfill_watch`
uses stored editions when they exist and are unpruned, and re-fetches from
INlabs otherwise. `prune_act_text` *deletes* acts no watch matched, so for a date
older than the last prune cutoff the stored corpus only contains what the
watches of the day hit — evaluating a new watch against it would measure the old
watches' coverage. Check when prune last ran (`gcloud run jobs executions list
--job=regwatch-prune`) and subtract its `--days`: dates after that cutoff are
complete and free to evaluate; dates before it will re-fetch, which is correct
but re-ingests ~3,500 acts per day and grows storage until prune runs again.

**It clears stale matches first.** Editing a watch does not delete the rows its
old terms produced, so without this the per-watch count would mix two term sets
and report the pre-edit answer unchanged — exactly when you are using the number
to judge an edit. Untriaged rows only; a `relevant`/`dismissed` verdict is a
human decision and survives a term change. The count is reported as
`cleared N stale match(es) ...`.

**Dry-run first** — without `--apply` it names the range and the day count and
writes nothing.

**To include enrichment**, pass `--max-enrich N`. The default is 0, which skips
the provider entirely. Only raise it when the summaries themselves are what you
are judging; N is a hard cap on acts sent, shared across all clients.

**The common failure** is every date landing in `skipped (no edition or fetch
failed)`. Weekends and holidays have no DOU and are skipped normally; a run where
*weekdays* are skipped too is a fetch failure, and the INlabs diagnostic in the
log says which.

## Create a watch from the command line

The SPA has no watch builder yet (TASK-016). This creates one directly, and is
what provisions a client's watches until it does.

Groups are **ANDed**; the terms inside one group are **ORed**. A group is one
dimension of the query — the places, the funding words — so the optional
`KIND:` prefix applies to the whole group. `entity` (the default) matches as a
substring, which is what proper names want; `concept` is stemmed, so
`convênio` also matches `convênios`.

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args='^@^create_watch@--client@7@--groups@entity:Pentecoste|Coreaú;concept:convênio|termo de fomento@--section@DO1@--apply'
```

Two separator problems stack up here, so use exactly this shape:

- `gcloud` splits `--args` on commas and the terms contain them, so `^@^` at the
  front switches gcloud's own delimiter to `@`. Do **not** use `^|^`: it would
  eat the term separator and collapse each group into one long term.
- `gcloud` also rejects a flag repeated inside `--args`
  (`"--group" cannot be specified multiple times`), so over there use the
  singular-flag forms **`--groups`** and **`--excludes`**, which take every
  group (or phrase) in one argument separated by `;`.

Locally, where the delimiter problem does not arise:

```bash
DJANGO_SETTINGS_MODULE=config.settings_test uv run python manage.py create_watch \
  --client 7 \
  --group "entity:Pentecoste|Coreaú|Redenção" \
  --group "concept:convênio|termo de fomento" \
  --exclude "aviso de licitacao" \
  --section DO1 --apply
```

It prints `created watch <id> for <client> (N group(s), M exclude(s), section DO1)`.

**Dry-run by default** — without `--apply` it prints the parsed groups and writes
nothing. Always dry-run first: a wrong group silently changes what a client
receives every morning.

**The common failure** is `client <name> already has an identical watch (same
groups and section); nothing created`. That guard is deliberate — re-running a
provisioning command must not quietly double a client's digest volume. Change
the groups, or delete the existing watch first.

Second failure: `unknown term kind 'x'; use one of entity, concept`. A typo in
the prefix is rejected rather than falling through to `entity`, because that
would silently change the matching semantics of the whole group.

## Change the enrichment model

Enrichment runs OpenAI first and falls back to Anthropic (`FallbackLLMClient`).
The OpenAI default is **`gpt-5.6-luna`** — the cost-optimised tier of the current
generation, $0.20/MTok in and $1.20/MTok out, against $2/$12 for `terra` and
$5/$30 for the `sol` flagship. Summarising one act into one Portuguese sentence
plus a label is not frontier work, and the job does it up to 200 times a run, so
the cheap tier is the correct default and a flagship would be pure spend.

OpenAI renames and retires models faster than this repo is redeployed, so check
what your key can actually see before assuming a name still works:

```bash
env_value() { sed -n "s/^$1=//p" .env | head -1 | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"; }
curl -sS https://api.openai.com/v1/models -H "Authorization: Bearer $(env_value OPENAI_API_KEY)" \
  | python3 -c "import json,sys;[print(m['id']) for m in sorted(json.load(sys.stdin)['data'],key=lambda m:-m['created']) if m['id'].startswith('gpt-')]" \
  | head -20
```

Smoke-test a candidate against a real act before switching. This exercises the
same strict-`json_schema` path the pipeline uses, so a model that cannot do
structured outputs fails here rather than in production:

```bash
DJANGO_DEBUG=1 DJANGO_SETTINGS_MODULE=config.settings_test \
OPENAI_API_KEY="$(env_value OPENAI_API_KEY)" \
uv run python -c "
import os, sys; sys.path.insert(0,'src')
import django; django.setup()
from enrichment.openai_client import OpenAILLMClient
print(OpenAILLMClient(os.environ['OPENAI_API_KEY'], model='gpt-5.6-luna').summarize(
    'EXTRATO DE CONTRATO N 9/2026 entre IFCE Campus Crateus e BETA CORP LTDA.', ['beta corp']))
"
```

The reply must name a category from the rubric in `src/enrichment/prompt.py`. A
model that returns a label outside the six is coerced to `other` — if a smoke
test comes back `other` for an obvious licitação, the model is ignoring the
rubric and is the wrong model, not a prompt bug.

To switch, set the env var rather than editing the default — no redeploy of the
image is needed, just a Job/Service update:

```bash
gcloud run jobs update regwatch-run-daily --region=us-east4 \
  --update-env-vars=REGWATCH_OPENAI_MODEL=gpt-5.6-terra
```

Two failure modes to know. `model_not_found` in the logs means the name was
retired — pick one from the list above. And **reasoning tokens count against
`max_completion_tokens` (300)**: if you move to a reasoning-heavy model, a reply
can burn the whole budget on reasoning and come back `finish_reason=length` with
truncated JSON, which surfaces as `could not parse LLM reply into Summary`.
Check `usage.completion_tokens_details.reasoning_tokens` on a test call; it is 0
for `luna`.

## Measure enrichment quality

Read-only. Answers the two questions the D3/D5 acceptance criteria are written
against: do identical act types get the same category, and does the ranking
signal have any spread at all.

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=enrichment_report,--date-from,2026-08-21,--date-to,2026-08-28
```

```
2026-08-21 -> 2026-08-28 — 284 enriched match(es)

categories:
  regulation   118
  tender        79
  other         41
  ...

D3 — 23 cluster(s) of >= 3 act(s); inconsistency rate 29.30%
  'declarou de utilidade publica a' (12) -> {'regulation': 10, 'other': 2}

D5 — confidence modal share 96.10% across 3 distinct value(s)
  0.98   11
  0.99   273
```

`--json` gives the same payload machine-readably, which is what to paste into a
`docs/analysis/` note. `--client N` narrows to one client; `--min-cluster N`
(default 3) sets how many acts a phrase needs before it counts as a cluster.

**The one failure mode:** a window with no enrichment in it reports
`0 enriched match(es)` and every rate as `0.00%` — that is an empty measurement,
not a perfect score. Check the window covers publication days.

## Re-enrich a sample after a prompt change

A prompt change only means something if the before and after are the *same*
acts. This re-runs enrichment over a date range and overwrites the stored
summary, category and signals.

```bash
# Always dry-run first: it prints how many acts would be sent, and sends nothing.
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=reenrich_matches,--date-from,2026-08-27,--date-to,2026-08-28

gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=reenrich_matches,--date-from,2026-08-27,--date-to,2026-08-28,--limit,150,--apply
```

**This costs money and overwrites client-visible summaries.** `--limit` (default
100) is the cap; there is no undo.

**The one failure mode:** far fewer acts than expected. Only the last 7 days of
act bodies are retained (see "Prune act text") — `prune_act_text` empties
`raw_text`, and an act with no body is skipped rather than re-guessed from its
title.

## Prune stale matches

A watch's definition can change after it has already produced matches — the
groups migration on 2026-07-21 rewrote every watch, and the matches made under
the old definitions stayed in the triage queue. On 2026-08-12 that was 51 of 122
matches (42% of the feed), none of which the current watch definitions would
produce. They mislead every precision judgement made from the feed.

`prune_stale_matches` re-evaluates each untriaged match against its watch's
**current** definition and removes the ones that no longer satisfy it.

**Always dry-run first.** With no flags it deletes nothing and prints per-watch
counts:

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=prune_stale_matches
```

```
watch 4 (IFCE): 51 stale
prune_stale_matches: would delete 51 match(es)
```

Read the per-watch counts and satisfy yourself they are the watches you expect.
A count covering nearly all of a watch's matches usually means the watch was
retargeted, not that the matches were wrong — decide which you meant. Only then:

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=prune_stale_matches,--apply
```

`--watch <id>` limits the run to a single watch.

**`--apply` deletes rows and there is no undo** — take a `pg_dump` first if the
count is large or surprising. Matches in state `relevant` or `dismissed` are
deliberately exempt at every count: a triaged verdict is a human decision, and
the command will never discard one even when the watch that produced it has been
retargeted beyond recognition.

## Find the phrases making a watch noisy

A watch matches on terms, but a term does more than one job in the DOU. On
2026-08-20, 31 of Meridiano's matches came from `saneamento` and only ~6 were
sanitation works. The rest split between the legal sense — in Brazilian legal
Portuguese `saneamento` means *curing a procedural defect*, as in "providências
necessárias ao **saneamento do certame**" — and acts that merely carry
"Secretaria Municipal de Saúde e **Saneamento**" in a signature block.

`exclude` on the watch already fixes this; twelve phrases removed 17 of the 31
with no real matches lost. The hard part is knowing *which* phrases, which is
what this command answers:

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=watch_term_contexts,--watch,6
```

```
watch 6 (Meridiano Infraestrutura) — 200 matched act(s) with text

  term 'saneamento' (concept) — literal in 31 act(s)
    preceded by:
         7  saude e saneamento
         4  municipal de saneamento
         3  parentais e saneamento
         2  necessarias ao saneamento
    followed by:
         3  saneamento para as
         2  saneamento e a
```

Read the clusters, decide which are noise, and add those phrases to the watch's
exclude list. Left and right context are counted **separately** on purpose: a
two-sided window fragments on the dates and process numbers that follow most
DOU phrases, so the recurring half never adds up. Phrases seen once are not
shown — one occurrence is an anecdote, not a pattern worth excluding.

`--window N` widens the context (default 2 words); `--top N` shows more
clusters per term (default 10).

**Two things it will not show you.** Concept terms match through the Portuguese
stemmer, so an act can match `licitação` while containing only `licitações`;
those report as "no literal occurrences (matched via stemming)". And acts past
the 7-day text retention window have no body left — the header says how many
were skipped, so a small corpus is never mistaken for a quiet term.

Excludes are evaluated with entity (substring) semantics over the whole act, so
prefer a phrase specific enough not to appear in an act you want. `saneamento
do certame` is safe; a bare `saude` is not.

## Prune act text (Supabase size)

On 2026-08-20 the Supabase database hit 762 MB against the free plan's 500 MB.
`gazette_act` was 749 MB of it — 98% — for 51 days of DOU. The growth rate was
~14.7 MB/day, so the plan limit came back every six weeks regardless of what was
paid for it.

Almost none of that storage was doing work. **649 of 87,035 acts had ever
produced a match (0.75%).** `raw_text`, `search_text` and `search_vector_pt`
have a one-day working life: `match_edition` filters a single edition, the
enricher reads `raw_text` once, and the 280-char snippet is copied onto the
`Match`. The API (`matching/api.py`) serializes only `title, agency, identifier,
date, section, source_url, source_anchor` — no screen has ever read an act body.

`prune_act_text` drops act text past a retention window:

- older than the window and **never matched** → the row is deleted
- older than the window and **has matches** → the row is kept, and only
  `raw_text` / `search_text` / `search_vector_pt` are cleared

Matched rows are never deleted: `Match.act` is `on_delete=CASCADE`, so deleting
one would silently take a client's triaged history with it.

**Always dry-run first.** With no `--apply` it writes nothing:

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=prune_act_text,--days,7
```

```
cutoff 2026-08-13 (keeping 7 day(s) of text)
  delete (never matched): 72772 act(s)
  strip  (has matches)  : 212 act(s)
  text payload affected : 267 MB
prune_act_text: dry run, nothing written
```

Then apply, and reclaim the space in the same run:

```bash
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=prune_act_text,--days,7,--apply,--reclaim
```

**`--reclaim` is not optional if you are trying to get under a plan limit.**
Clearing the columns returns the space to Postgres, not to the disk Supabase
meters. `--reclaim` runs `VACUUM (FULL, ANALYZE)` plus a `REINDEX` of both GIN
indexes, which is what actually shrinks the files. It takes an ACCESS EXCLUSIVE
lock on `gazette_act` — run it outside the 08:05 and 13:00 windows. It is safe
on a nearly-empty table because `VACUUM FULL` writes a new compacted copy, so
it needs free space for the *result*, not for the original.

The first run took 762 MB → **155 MB**, and left all 650 matches, their
snippets, their summaries and all 41 digests intact.

**Pruning marks the edition, and backfill respects the mark.** A pruned
`Edition` row survives with `text_pruned_at` set. `backfill_watch` skips those
rows and re-fetches the day from INlabs, because matching a stripped edition
from storage would find nothing and report success. `ingest_edition` clears the
mark when the text comes back, so pruning is always reversible from upstream —
that is why dropping the bodies is safe at all.

**Choosing the window.** Steady state is roughly `days x 14.7 MB`, plus about
1 MB/year for the identity of acts that matched. 7 days is ~105 MB. The digest
retry window (`REGWATCH_DIGEST_RETRY_DAYS`, default 7) does *not* constrain it:
`retry_unsent_digests` re-sends the stored `Digest.body` and never re-reads an
act. The real cost of a short window is that backfilling a **new** watch over
pruned dates has to re-download those days from INlabs.

Run it weekly. Without a schedule the database climbs back over the limit in
about six weeks.

**Check the trigger can actually fire.** The `regwatch-prune` Cloud Scheduler
job was created on 2026-08-20 but the scheduler service account was never
granted `roles/run.invoker` on it, so every weekly attempt returned
`PERMISSION_DENIED` and produced **no execution at all** — which the
failed-execution alert policies cannot see. It went unnoticed for six days,
during which the database went 155 MB → 285 MB. To confirm a trigger is healthy:

```bash
gcloud scheduler jobs describe regwatch-prune \
  --location us-east4 --project regwatch-501619 --format='value(status.code)'
```

Empty output means the last attempt succeeded; `7` means PERMISSION_DENIED. Fix
with:

```bash
gcloud run jobs add-iam-policy-binding regwatch-prune \
  --region=us-east4 --project=regwatch-501619 \
  --member="serviceAccount:regwatch-scheduler@regwatch-501619.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

The alert policy `deploy/policy-scheduler-trigger-denied.json` now watches for
this across *all* scheduler jobs, so a future missing binding pages instead of
going quiet. Note the growth rate above (~14.7 MB/day) counts act text only —
measured against the whole database, including the trigram and GIN indexes over
that text, it is closer to **32 MB per publication day**.

## Back up the database to this machine

The Supabase project is on the Free plan: **no Point-in-Time Recovery, no
automated daily backups**. Until that changes, a dump on this machine is the
only copy of anything that cannot be regenerated. Acts can be re-scraped and
summaries re-enriched for pennies; a human triage label on
`matching_match.state` exists nowhere else.

```bash
scripts/backup-db.sh          # -> .backups/regwatch-<timestamp>.sql.gz, keeps 10
KEEP=30 scripts/backup-db.sh  # keep 30 instead
```

What it prints on success:

```
dumping to .backups/regwatch-2026-08-30T17-21-21.sql.gz ...
verifying ...
ok: 26M, 101 rows in matching_match
```

It refuses to keep a dump that is empty or that is missing any of
`matching_match`, `watches_watch`, `watches_client`, `digests_digest` — a dump
that restores nothing is worse than no dump, because it gets trusted.

**When to run it.** Before any destructive migration or bulk operation, and on
any day you spend time triaging. Understand what this is: a snapshot as of the
moment it runs, so the most you can lose is everything since the last one. It
is not PITR and does not pretend to be.

**Common failure:** `unexpected spaces found in "..."`. The password inside
`SUPABASE_DB_URL` is not percent-encoded, so libpq rejects the URL. The script
already works around this by splitting the URL and passing the password as
`PGPASSWORD`; if you see this from a *manual* `pg_dump`, that is why — and note
that the error prints part of the password, so avoid running it that way.

## Prove a backup actually restores

A dump nobody has restored is a guess.

```bash
scripts/restore-drill.sh                          # newest backup
scripts/restore-drill.sh .backups/regwatch-....sql.gz
```

It starts a throwaway `postgres:17` on port 55432, restores into it, compares
the row count in the dump against the row count that came back for every core
table, and removes the container on exit either way.

```
TABLE                        DUMP   RESTORED   RESULT
matching_match                101        101   ok
watches_watch                   7          7   ok
...
restore drill PASSED — every table came back with the row count the dump carried
```

**Expected noise:** errors mentioning `supabase_vault`, `auth`, or `storage`.
Those are Supabase's managed schemas and do not exist in a plain Postgres
image; they have nothing to do with the application's tables. They are written
to `/tmp/restore-drill.err` rather than the console for exactly that reason.

**Common failure:** port 55432 already in use, usually a drill container left
behind by an interrupted run. `docker rm -f $(docker ps -q --filter
name=regwatch-restore-drill)`.

## Tell a quiet day from a broken pipeline

Since v0.28.0 a client hears from RegWatch on **every day the DOU publishes**,
whether or not anything matched. Silence used to mean two things at once —
"nothing concerned you" and "RegWatch is down" — and the reader had no way to
tell which. It now means exactly one thing: **nothing ran.**

**What the reader gets on an empty day**

Subject line is unchanged (`RegWatch — 26 de junho de 2026`). The body is the
`digests/quiet.txt` template:

```
RegWatch — Cactarus — 26 de junho de 2026

Suas buscas foram executadas e não encontraram nada hoje.

Nenhuma ação é necessária. Este aviso existe para que o silêncio não seja
confundido com uma falha: enquanto o RegWatch estiver funcionando, você recebe
uma mensagem em todo dia em que o Diário Oficial da União publicar.
```

A digest with matches now leads with `O que suas buscas encontraram hoje:`
before the list. That header is the quickest way to tell the two apart at a
glance, and it is what the tests assert on.

**Three days, not two** (`backlog/decisions/decision-007`)

| Day | What is sent |
|---|---|
| DOU published, something matched | the match digest |
| DOU published, nothing matched | the quiet message |
| DOU did not publish (weekend, holiday) | **nothing at all** |

A quiet message is only built for a client that has at least one **active**
watch *and* an email address. A client with no email gets no quiet row on
purpose: it could never be delivered, so it would sit `sent=False` for ever and
fail `check_heartbeat` every single day, destroying the switch this behaviour
exists to feed.

**Diagnosing "I got nothing today"**

Work down this list; the first one that is true is the answer.

```bash
# 1. Did the DOU publish at all? No editions == nothing is wrong.
gcloud run jobs execute regwatch-run-daily --region=us-east4 --wait \
  --args=shell_plus,-c,"from gazette.models import Edition; print(Edition.objects.filter(date='2026-06-26').count())"

# 2. Did the run happen, and what did it conclude?
gcloud run jobs execute regwatch-heartbeat --region=us-east4 --wait \
  --args=check_heartbeat,--date,2026-06-26
```

- **`heartbeat OK: ... delivered 1`** and still no mail → the message was sent
  and the problem is downstream (spam folder, forwarding). Check
  `Digest.sent=True` for the date, then the Gmail SMTP section above.
- **`heartbeat: N undelivered digest(s)`** → it was built but not delivered.
  Read `Digest.send_error`, then `resend_digests`.
- **`heartbeat: no completed scheduled RunLog`** → nothing ran. Both the 08:05
  and the 13:00 runs missed. See the next section.
- **The date has zero editions** → a holiday or a weekend. Correct behaviour;
  nothing to fix.

**Common failure:** reading a *quiet* message as a broken pipeline. It is the
opposite — it is the pipeline reporting for duty. The failure mode to worry
about is now receiving *nothing* on a weekday.

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

**2. Push new secret versions from `.env`.**

**Do not `source` / `.` the `.env` file to do this.** Several values in it —
`SMTP_PASSWORD` among them — contain characters the shell treats as syntax
(`&`, `*`, `:`), so sourcing fails on those exact lines and leaves the variable
*unset*. The push then silently stores an empty secret, and the next run fails
with the same 535 you were trying to fix. Verified on 2026-08-12: of the seven
values below, `SMTP_PASSWORD` was one of four that would not source.

Read each value out of the file instead of executing it:

```bash
env_value() {  # print a raw value from .env without letting the shell evaluate it
  sed -n "s/^$1=//p" .env | head -1 | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"
}
for s in SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD SMTP_STARTTLS SMTP_FROM OPENAI_API_KEY; do
  printf '%s' "$(env_value "$s")" | gcloud secrets versions add "$s" --data-file=- 2>/dev/null \
    || printf '%s' "$(env_value "$s")" | gcloud secrets create "$s" --replication-policy=automatic --data-file=-
done
```

This works in both zsh and bash. `printf '%s'` rather than `echo` is deliberate:
a trailing newline inside `SMTP_PASSWORD` is itself a cause of 535, and `$(...)`
already strips the one `sed` emits.

Before pushing, confirm every value actually came out non-empty — this prints
byte counts, never the values:

```bash
for s in SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD SMTP_STARTTLS SMTP_FROM OPENAI_API_KEY; do
  printf '%s: %s bytes\n' "$s" "$(printf '%s' "$(env_value "$s")" | wc -c)"
done
```

Any `0 bytes` means the key is missing or misspelled in `.env` — fix it before
running the push loop, not after.

Then verify what actually landed in Secret Manager, again without printing any
value:

```bash
for s in SMTP_PASSWORD OPENAI_API_KEY; do
  printf '%s: %s bytes\n' "$s" "$(gcloud secrets versions access latest --secret=$s | wc -c)"
done
```

Expected: `SMTP_PASSWORD: 16 bytes` (19 if you kept the display spaces, which
also works) and a non-zero `OPENAI_API_KEY`. A count of 17 or 20 means a newline
slipped in, and `0` means the value never made it out of `.env` — redo step 2.

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
