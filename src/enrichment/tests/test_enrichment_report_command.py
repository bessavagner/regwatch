import datetime
import json
from io import StringIO

import pytest
from django.core.management import call_command

from accounts.models import Workspace
from gazette.models import Act, Edition
from matching.models import Match
from watches.models import Client, Watch


@pytest.fixture
def watch(db):
    ws = Workspace.objects.create(name="RepWS")
    client = Client.objects.create(workspace=ws, name="Rep")
    return Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "contrato", "kind": "concept"}]}]
    )


def _match(watch, date, summary, category, confidence, identifier):
    edition, _ = Edition.objects.get_or_create(
        date=date, section="1", defaults={"source_url": "https://r.test/s1"}
    )
    act = Act.objects.create(
        edition=edition, identifier=identifier, title="t", agency="g",
        raw_text="corpo", search_text="corpo", source_anchor=f"#{identifier}",
    )
    return Match.objects.create(
        watch=watch, act=act, rank=0.0, snippet="corpo",
        ai_summary=summary, category=category, confidence=confidence,
    )


@pytest.mark.django_db
def test_report_names_the_clusters_that_split(watch):
    day = datetime.date(2026, 8, 27)
    _match(watch, day, "Declarou de utilidade publica a entidade A", "regulation", 0.99, "a1")
    _match(watch, day, "Declarou de utilidade publica a entidade B", "regulation", 0.99, "a2")
    _match(watch, day, "Declarou de utilidade publica a entidade C", "other", 0.98, "a3")

    out = StringIO()
    call_command(
        "enrichment_report", "--date-from=2026-08-27", "--date-to=2026-08-27",
        "--json", stdout=out,
    )
    payload = json.loads(out.getvalue())

    assert payload["enriched_matches"] == 3
    assert payload["inconsistency_rate"] == 1.0
    assert payload["split_clusters"][0]["categories"] == {"regulation": 2, "other": 1}


@pytest.mark.django_db
def test_report_shows_confidence_has_no_spread(watch):
    day = datetime.date(2026, 8, 27)
    for i in range(4):
        _match(watch, day, f"Resumo distinto numero {i}", "tender", 0.99, f"b{i}")

    out = StringIO()
    call_command("enrichment_report", "--date-from=2026-08-27", "--date-to=2026-08-27",
                 "--json", stdout=out)
    payload = json.loads(out.getvalue())

    assert payload["confidence_modal_share"] == 1.0
    assert payload["confidence_histogram"] == {"0.99": 4}


@pytest.mark.django_db
def test_report_ignores_matches_outside_the_window_and_unenriched_ones(watch):
    _match(watch, datetime.date(2026, 8, 20), "Fora da janela", "tender", 0.99, "c1")
    _match(watch, datetime.date(2026, 8, 27), None, "", None, "c2")

    out = StringIO()
    call_command("enrichment_report", "--date-from=2026-08-27", "--date-to=2026-08-27",
                 "--json", stdout=out)
    assert json.loads(out.getvalue())["enriched_matches"] == 0
