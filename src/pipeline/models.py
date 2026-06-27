from django.db import models


class RunLog(models.Model):
    date = models.DateField()
    status = models.CharField(max_length=20, default="running")  # running|success|partial|failed
    editions = models.IntegerField(default=0)
    acts = models.IntegerField(default=0)
    matches = models.IntegerField(default=0)
    enriched = models.IntegerField(default=0)
    digests = models.IntegerField(default=0)
    errors = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"RunLog({self.date}, {self.status})"
