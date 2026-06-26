from django.conf import settings
from django.db import models


class Workspace(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Membership(models.Model):
    workspace = models.ForeignKey(Workspace, related_name="members", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("workspace", "user")
