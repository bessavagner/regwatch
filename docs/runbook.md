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
