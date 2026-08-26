from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models


class Edition(models.Model):
    date = models.DateField()
    section = models.CharField(max_length=20)
    source_url = models.URLField()
    # Set when prune_act_text strips this edition's act bodies. The rows survive
    # for the matches that reference them, but the edition can no longer be
    # re-matched from storage, so backfill must re-fetch it from INlabs.
    text_pruned_at = models.DateTimeField(null=True, blank=True)

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
    search_vector_pt = SearchVectorField(null=True)   # config=portuguese

    @property
    def dou_url(self) -> str:
        """A public, reader-facing link to this act in the DOU.

        source_anchor is INlabs' pdfPage: a pesquisa.in.gov.br page view of the
        exact page the act ran on, open to anyone. It arrives as http and
        in.gov.br 301s to https, so we upgrade it here rather than send readers
        through a redirect that mail clients and corporate filters flag.

        Edition.source_url is deliberately NOT the fallback -- that is the
        authenticated INlabs zip endpoint, which serves a login wall and then an
        archive, not a readable act. When the anchor is missing we fall back to
        the day's edition on in.gov.br: the right section and date, if not the
        right page.
        """
        if self.source_anchor:
            if self.source_anchor.startswith("http://"):
                return "https://" + self.source_anchor[len("http://"):]
            return self.source_anchor
        # Editions carry INlabs' pubName ("DO1", "DO1E"); leiturajornal wants it
        # lowercased. Older rows stored the bare section number.
        section = self.edition.section.strip().lower()
        if not section.startswith("do"):
            section = f"do{section}"
        return (
            "https://www.in.gov.br/leiturajornal"
            f"?data={self.edition.date:%d-%m-%Y}&secao={section}"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["edition", "identifier"], name="uq_act_edition_identifier"),
        ]
        indexes = [
            GinIndex(fields=["search_vector_pt"], name="gazette_act_search_pt_gin"),
            GinIndex(
                name="gazette_act_search_text_trgm",
                fields=["search_text"],
                opclasses=["gin_trgm_ops"],
            ),
        ]
