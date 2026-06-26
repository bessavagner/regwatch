import datetime
import pytest
from accounts.models import Workspace
from watches.models import Client, Watch
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from matching.models import Match


def _edition_with(text):
    return ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section="1",
        source_url="https://example.test/s1",
        items=(RawItem("a1", "Ato", "Org", text, "#a1"),),
    ))


@pytest.fixture
def watch(db):
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Beta")
    return Watch.objects.create(client=client, terms=["beta corp"])


@pytest.mark.django_db
def test_matches_when_terms_present(watch):
    edition = _edition_with("Licença concedida à BETA CORP nesta data.")
    matches = match_edition(edition)
    assert len(matches) == 1
    assert matches[0].watch == watch


@pytest.mark.django_db
def test_no_match_when_term_absent(watch):
    edition = _edition_with("Documento sem relação alguma.")
    assert match_edition(edition) == []


@pytest.mark.django_db
def test_exclude_term_suppresses_match(watch):
    watch.exclude = ["revogado"]
    watch.save()
    edition = _edition_with("BETA CORP teve o ato REVOGADO hoje.")
    assert match_edition(edition) == []


@pytest.mark.django_db
def test_matcher_is_idempotent(watch):
    edition = _edition_with("Ato sobre BETA CORP.")
    match_edition(edition)
    match_edition(edition)
    assert Match.objects.count() == 1


@pytest.mark.django_db
def test_section_filter(db):
    """Watch.section must be honoured: only watches whose section matches the
    edition's section (or whose section is empty) should produce matches."""
    ws = Workspace.objects.create(name="SectWS")
    client = Client.objects.create(workspace=ws, name="SectClient")
    w_wrong = Watch.objects.create(client=client, terms=["sectterm"], section="2")
    w_right = Watch.objects.create(client=client, terms=["sectterm"], section="1")
    w_any   = Watch.objects.create(client=client, terms=["sectterm"], section="")
    edition = _edition_with("Ato publicado por SECTTERM nesta data.")
    matches = match_edition(edition)
    matched_ids = {m.watch_id for m in matches}
    assert w_wrong.pk not in matched_ids, "watch with wrong section must be skipped"
    assert w_right.pk in matched_ids,    "watch with matching section must fire"
    assert w_any.pk   in matched_ids,    "watch with empty section must fire on any section"
