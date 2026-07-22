from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models


class Edition(models.Model):
    date = models.DateField()
    section = models.CharField(max_length=20)
    source_url = models.URLField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["date", "section"], name="uq_edition_date_section"),
        ]


class Act(models.Model):
    edition = models.ForeignKey(Edition, related_name="acts", on_delete=models.CASCADE)
    identifier = models.CharField(max_length=200)
    title = models.TextField()
    agency = models.TextField(blank=True, default="")
    raw_text = models.TextField()
    search_text = models.TextField()
    source_anchor = models.TextField(blank=True, default="")
    search_vector = SearchVectorField(null=True)      # config=simple; dropped in phase 3
    search_vector_pt = SearchVectorField(null=True)   # config=portuguese

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["edition", "identifier"], name="uq_act_edition_identifier"),
        ]
        indexes = [
            GinIndex(fields=["search_vector"]),
            GinIndex(fields=["search_vector_pt"], name="gazette_act_search_pt_gin"),
            GinIndex(
                name="gazette_act_search_text_trgm",
                fields=["search_text"],
                opclasses=["gin_trgm_ops"],
            ),
        ]
