from django.db import models
from accounts.models import Workspace


class Client(models.Model):
    workspace = models.ForeignKey(Workspace, related_name="clients", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    is_house = models.BooleanField(default=False)
    email = models.EmailField(blank=True, default="")   # digest recipient; "" = don't send


class Watch(models.Model):
    client = models.ForeignKey(Client, related_name="watches", on_delete=models.CASCADE)
    terms = models.JSONField(default=list)       # required terms (AND)
    exclude = models.JSONField(default=list)      # excluded terms
    section = models.CharField(max_length=20, blank=True, default="")  # "" = all
    active = models.BooleanField(default=True)
