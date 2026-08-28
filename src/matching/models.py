from django.db import models
from gazette.models import Act
from watches.models import Watch


class Match(models.Model):
    watch = models.ForeignKey(Watch, related_name="matches", on_delete=models.CASCADE)
    act = models.ForeignKey(Act, related_name="matches", on_delete=models.CASCADE)
    snippet = models.TextField(blank=True, default="")
    # Which of the watch's terms actually fired, in the watch's own order and
    # as the client typed them. Empty on every match created before v0.20.0:
    # the terms are unrecoverable for acts past the 7-day text retention window.
    matched_terms = models.JSONField(default=list)
    rank = models.FloatField(
        default=0.0,
        help_text="Advisory only: used to order results, not a guarantee of relevance.",
    )
    ai_summary = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=50, blank=True, default="")
    confidence = models.FloatField(null=True, blank=True)
    state = models.CharField(max_length=20, default="new")  # new | relevant | dismissed
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["watch", "act"], name="uq_match_watch_act"),
        ]
