from django.db import models
from watches.models import Client


class Digest(models.Model):
    client = models.ForeignKey(Client, related_name="digests", on_delete=models.CASCADE)
    date = models.DateField()
    body = models.TextField()
    sent = models.BooleanField(default=False)
    send_error = models.TextField(blank=True, default="")
    send_attempts = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["client", "date"], name="uq_digest_client_date"),
        ]
