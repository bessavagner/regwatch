from django.db import models


class RunLog(models.Model):
    TRIGGER_CHOICES = [("scheduled", "scheduled"), ("backfill", "backfill")]

    date = models.DateField()
    status = models.CharField(max_length=20, default="running")  # running|success|partial|failed
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default="scheduled")
    # These six are totals for `date`, not for this run. The heartbeat reads
    # only the LATEST run of a date, so it needs the day's true state from
    # whichever run it lands on — a morning `partial` would otherwise be masked
    # by a quiet midday run that created nothing.
    editions = models.IntegerField(default=0)
    acts = models.IntegerField(default=0)
    matches = models.IntegerField(default=0)
    enriched = models.IntegerField(default=0)
    digests = models.IntegerField(default=0)
    digests_sent = models.IntegerField(default=0)

    # What THIS run actually did. Summing the totals above across runs
    # double-counts every day the midday run revisits (908 vs an actual 650
    # over 2026-08-13..20); sum these instead. They are also the only way to
    # tell "nothing new to do" from "ingest silently returned nothing".
    ingested_acts = models.IntegerField(default=0)
    created_matches = models.IntegerField(default=0)
    created_enriched = models.IntegerField(default=0)
    errors = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"RunLog({self.date}, {self.status})"
