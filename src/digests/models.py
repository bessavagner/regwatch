from django.db import models
from watches.models import Client


class Digest(models.Model):
    client = models.ForeignKey(Client, related_name="digests", on_delete=models.CASCADE)
    date = models.DateField()
    body = models.TextField()
    sent = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["client", "date"], name="uq_digest_client_date"),
        ]
