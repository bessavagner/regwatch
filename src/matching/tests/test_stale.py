import datetime

import pytest

from accounts.models import Workspace
from gazette.models import Act, Edition
from matching.models import Match
from matching.stale import stale_match_ids
from watches.models import Client, Watch

DATE = datetime.date(2026, 8, 26)


def _act(identifier, text, date=DATE):
    edition, _ = Edition.objects.get_or_create(
        date=date, section="DO1", defaults={"source_url": "https://s.test/1"})
    return Act.objects.create(
        edition=edition, identifier=identifier, title="t", agency="g",
        raw_text=text, search_text=text, source_anchor=f"#{identifier}")


@pytest.fixture
def watch(db):
    ws = Workspace.objects.create(name="ST")
    client = Client.objects.create(workspace=ws, name="C")
    return Watch.objects.create(
        client=client, groups=[{"terms": [{"text": "convenio", "kind": "entity"}]}])


@pytest.mark.django_db
def test_a_match_the_current_terms_still_make_is_not_stale(watch):
    match = Match.objects.create(watch=watch, act=_act("a1", "convenio firmado"), rank=0.0)
    assert stale_match_ids(watch) == []
    assert Match.objects.filter(pk=match.pk).exists()


@pytest.mark.django_db
def test_a_match_the_current_terms_would_not_make_is_stale(watch):
    match = Match.objects.create(watch=watch, act=_act("a2", "outra coisa"), rank=0.0)
    assert stale_match_ids(watch) == [match.pk]


@pytest.mark.django_db
def test_a_triaged_match_is_never_stale(watch):
    # A human verdict outranks a term edit.
    Match.objects.create(
        watch=watch, act=_act("a3", "outra coisa"), rank=0.0, state="dismissed")
    assert stale_match_ids(watch) == []


@pytest.mark.django_db
def test_the_date_range_scopes_it(watch):
    old = Match.objects.create(
        watch=watch, act=_act("a4", "outra", datetime.date(2026, 7, 1)), rank=0.0)
    new = Match.objects.create(watch=watch, act=_act("a5", "outra"), rank=0.0)
    assert stale_match_ids(watch, date_from=DATE, date_to=DATE) == [new.pk]
    assert set(stale_match_ids(watch)) == {old.pk, new.pk}


@pytest.mark.django_db
def test_a_watch_that_can_never_match_holds_only_stale_rows(watch):
    match = Match.objects.create(watch=watch, act=_act("a6", "convenio"), rank=0.0)
    watch.groups = []
    watch.save(update_fields=["groups"])
    assert stale_match_ids(watch) == [match.pk]
