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

Prints one line per batch and a final total:

```
reindexed 500/22068
...
reindex_search: 22068 acts
```

Common failure: the job times out on a large backlog. Re-run it. The command
only touches acts whose vector is still null, so re-running resumes rather than
restarting. Use `--all` to force a full rebuild after changing the vector
definition.
