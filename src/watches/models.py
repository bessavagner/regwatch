from django.db import models
from accounts.models import Workspace


class Client(models.Model):
    workspace = models.ForeignKey(Workspace, related_name="clients", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    is_house = models.BooleanField(default=False)
    email = models.EmailField(blank=True, default="")   # digest recipient; "" = don't send


class Watch(models.Model):
    MATCH_MODE_ALL = "all"
    MATCH_MODE_ANY = "any"
    MATCH_MODE_CHOICES = [
        (MATCH_MODE_ALL, "All terms must appear"),
        (MATCH_MODE_ANY, "Any term may appear"),
    ]

    client = models.ForeignKey(Client, related_name="watches", on_delete=models.CASCADE)
    terms = models.JSONField(default=list)       # required terms, combined per match_mode
    exclude = models.JSONField(default=list)      # excluded terms
    match_mode = models.CharField(max_length=3, choices=MATCH_MODE_CHOICES, default=MATCH_MODE_ALL)
    section = models.CharField(max_length=20, blank=True, default="")  # "" = all
    active = models.BooleanField(default=True)
