import datetime
from io import StringIO

import pytest
from django.core.management import call_command

from accounts.models import Workspace
from enrichment import fallback
from enrichment.llm import Summary
from gazette.models import Act, Edition
from matching.models import Match
from watches.models import Client, Watch


@pytest.fixture
def two_matches(db):
    ws = Workspace.objects.create(name="ReWS")
    client = Client.objects.create(workspace=ws, name="Re")
    watch = Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "contrato", "kind": "concept"}]}]
    )
    edition = Edition.objects.create(
        date=datetime.date(2026, 8, 27), section="1", source_url="https://re.test/s1"
    )
    kept = Act.objects.create(
        edition=edition, identifier="k1", title="t", agency="g",
        raw_text="corpo do ato", search_text="corpo do ato", source_anchor="#k1",
    )
    # prune_act_text empties raw_text past the 7-day retention window.
    pruned = Act.objects.create(
        edition=edition, identifier="p1", title="t", agency="g",
        raw_text="", search_text="", source_anchor="#p1",
    )
    return (
        Match.objects.create(watch=watch, act=kept, rank=0.0, snippet="corpo"),
        Match.objects.create(watch=watch, act=pruned, rank=0.0, snippet=""),
    )


@pytest.mark.django_db
def test_dry_run_counts_only_matches_whose_text_survived(two_matches):
    out = StringIO()
    call_command("reenrich_matches", "--date-from=2026-08-27", "--date-to=2026-08-27",
                 stdout=out)
    text = out.getvalue()
    assert "1 match(es) with retained text" in text
    assert "dry run" in text


@pytest.mark.django_db
def test_dry_run_sends_nothing(two_matches, monkeypatch):
    def explode():
        raise AssertionError("a dry run must not construct an LLM client")

    monkeypatch.setattr(fallback.FallbackLLMClient, "from_env", staticmethod(explode))
    call_command("reenrich_matches", "--date-from=2026-08-27", "--date-to=2026-08-27",
                 stdout=StringIO())


@pytest.mark.django_db
def test_apply_re_enriches_the_retained_match(two_matches, monkeypatch):
    kept, pruned = two_matches

    class _Fake:
        def summarize(self, act_text, terms):
            return Summary(summary="Resumo novo.", category="tender")

    monkeypatch.setattr(
        fallback.FallbackLLMClient, "from_env", staticmethod(lambda: _Fake())
    )
    call_command("reenrich_matches", "--date-from=2026-08-27", "--date-to=2026-08-27",
                 "--apply", stdout=StringIO())

    kept.refresh_from_db()
    pruned.refresh_from_db()
    assert kept.ai_summary == "Resumo novo."
    assert pruned.ai_summary is None


@pytest.mark.django_db
def test_limit_caps_the_spend(two_matches, monkeypatch):
    sent = []

    class _Counting:
        def summarize(self, act_text, terms):
            sent.append(act_text)
            return Summary(summary="s", category="other")

    monkeypatch.setattr(
        fallback.FallbackLLMClient, "from_env", staticmethod(lambda: _Counting())
    )
    call_command("reenrich_matches", "--date-from=2026-08-27", "--date-to=2026-08-27",
                 "--limit=0", "--apply", stdout=StringIO())
    assert sent == []
