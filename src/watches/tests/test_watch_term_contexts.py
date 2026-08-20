import datetime

import pytest
from django.core.management import call_command

from accounts.models import Workspace
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from gazette.models import Act
from matching.matcher import match_edition
from watches.models import Client, Watch

DATE = datetime.date(2026, 8, 18)


def _act(ident, body):
    return RawItem(ident, "AVISO DE LICITAÇÃO", "Org", body, f"#{ident}")


@pytest.fixture
def noisy(db):
    """One watch whose term is doing two different jobs in the corpus."""
    ws = Workspace.objects.create(name="Acme")
    client = Client.objects.create(workspace=ws, name="Meridiano", email="m@example.test")
    watch = Watch.objects.create(
        client=client,
        groups=[{"terms": [{"text": "saneamento", "kind": "entity"}]}],
    )
    edition = ingest_edition(RawEdition(
        date=DATE, section="DO1", source_url="https://x.test/DO1",
        items=(
            _act("a1", "Contratação para execução de obras de saneamento no município."),
            _act("a2", "Demandas da Secretaria Municipal de Saúde e Saneamento do município."),
            _act("a3", "Atende à Secretaria Municipal de Saúde e Saneamento e às demais."),
            _act("a4", "Providências necessárias ao saneamento do certame. Nova data."),
        ),
    ))
    match_edition(edition)
    return watch


@pytest.mark.django_db
def test_reports_the_recurring_phrase_around_a_noisy_term(noisy, capsys):
    call_command("watch_term_contexts", "--watch", str(noisy.pk), "--window", "2")
    out = capsys.readouterr().out

    assert "4 matched act(s) with text" in out
    # The department-name cluster is what an author would turn into an exclude.
    assert "saude e saneamento" in out
    assert "preceded by:" in out


@pytest.mark.django_db
def test_singletons_are_not_reported_as_patterns(noisy, capsys):
    """One occurrence is an anecdote, not a cluster worth excluding."""
    call_command("watch_term_contexts", "--watch", str(noisy.pk), "--window", "2")
    out = capsys.readouterr().out

    # "obras de saneamento" appears once; it must not be offered as a pattern.
    assert "obras de saneamento" not in out


@pytest.mark.django_db
def test_pruned_acts_are_counted_and_skipped(noisy, capsys):
    """After the retention window the bodies are gone; say so rather than
    silently reporting a smaller corpus as if it were the whole one."""
    Act.objects.filter(identifier="a2").update(search_text="", raw_text="")

    call_command("watch_term_contexts", "--watch", str(noisy.pk), "--window", "2")
    out = capsys.readouterr().out

    assert "3 matched act(s) with text" in out
    assert "1 pruned and skipped" in out


@pytest.mark.django_db
def test_reports_nothing_when_every_matched_act_is_pruned(noisy, capsys):
    Act.objects.all().update(search_text="", raw_text="")

    call_command("watch_term_contexts", "--watch", str(noisy.pk))
    out = capsys.readouterr().out

    assert "past the text retention window" in out


@pytest.mark.django_db
def test_unknown_watch_is_an_error(db):
    from django.core.management.base import CommandError

    with pytest.raises(CommandError, match="no watch with id 999"):
        call_command("watch_term_contexts", "--watch", "999")
