import datetime
import pytest
from accounts.models import Workspace
from watches.models import Client, Watch
from gazette.contracts import RawEdition, RawItem
from gazette.ingest import ingest_edition
from matching.matcher import match_edition
from matching.models import Match


def _edition_with(text, section="1"):
    return ingest_edition(RawEdition(
        date=datetime.date(2026, 6, 26), section=section,
        source_url="https://example.test/s1",
        items=(RawItem("a1", "Ato", "Org", text, "#a1"),),
    ))


def _group(*texts, kind="entity"):
    return {"terms": [{"text": t, "kind": kind} for t in texts]}


def _watch(*groups, name="Beta", **kwargs):
    ws = Workspace.objects.create(name=f"WS-{name}")
    client = Client.objects.create(workspace=ws, name=name)
    return Watch.objects.create(client=client, terms=[], groups=list(groups), **kwargs)


@pytest.mark.django_db
def test_single_term_group_matches():
    watch = _watch(_group("beta corp"))
    matches = match_edition(_edition_with("Licença concedida à BETA CORP nesta data."))
    assert len(matches) == 1
    assert matches[0].watch == watch


@pytest.mark.django_db
def test_no_match_when_term_absent():
    _watch(_group("beta corp"))
    assert match_edition(_edition_with("Documento sem relação alguma.")) == []


@pytest.mark.django_db
def test_terms_within_a_group_are_ored():
    # This is the fix for the 2026-07-21 zero-match bug: aliases of one concept
    # must not all have to appear.
    _watch(_group("alfa", "beta"))
    assert len(match_edition(_edition_with("apenas alfa aqui"))) == 1


@pytest.mark.django_db
def test_groups_are_anded():
    _watch(_group("alfa"), _group("beta"))
    assert match_edition(_edition_with("apenas alfa aqui")) == []


@pytest.mark.django_db
def test_all_groups_present_matches():
    _watch(_group("alfa"), _group("beta"))
    assert len(match_edition(_edition_with("alfa e beta juntos"))) == 1


@pytest.mark.django_db
def test_watch_with_no_groups_matches_nothing():
    _watch()
    assert match_edition(_edition_with("qualquer texto")) == []


@pytest.mark.django_db
def test_group_with_no_terms_matches_nothing():
    _watch({"terms": []})
    assert match_edition(_edition_with("qualquer texto")) == []


@pytest.mark.django_db
def test_exclude_term_suppresses_match():
    watch = _watch(_group("beta corp"), name="Ex")
    watch.exclude = ["revogado"]
    watch.save()
    assert match_edition(_edition_with("BETA CORP REVOGADO nesta data.")) == []


@pytest.mark.django_db
def test_matcher_is_idempotent():
    _watch(_group("beta corp"))
    edition = _edition_with("BETA CORP citada.")
    match_edition(edition)
    match_edition(edition)
    assert Match.objects.count() == 1


@pytest.mark.django_db
def test_section_filter():
    ws = Workspace.objects.create(name="SecWS")
    client = Client.objects.create(workspace=ws, name="Sec")
    w_wrong = Watch.objects.create(client=client, terms=[], groups=[_group("sectterm")], section="2")
    w_right = Watch.objects.create(client=client, terms=[], groups=[_group("sectterm")], section="1")
    w_any = Watch.objects.create(client=client, terms=[], groups=[_group("sectterm")], section="")
    matches = match_edition(_edition_with("sectterm presente", section="1"))
    matched_ids = {m.watch_id for m in matches}
    assert w_wrong.pk not in matched_ids
    assert w_right.pk in matched_ids
    assert w_any.pk in matched_ids


@pytest.mark.django_db
def test_regression_2026_07_21_seven_term_watch():
    # The real production watch ANDed seven terms, so its intersection was empty
    # every day. Regrouped as aliases of one concept, it matches: only the terms
    # actually present in the body are needed, not all seven.
    body = (
        "Convenio com o SEBRAE para o polo de inovacao, com recursos "
        "EMBRAPII/SEBRAE aprovados nesta data."
    )
    _watch(_group(
        "sebrae", "embrapii", "pólo de inovação", "JUBILATO SOLUÇÕES",
        "SEBRAE Nacional", "EMBRAPII Unidade", "consórcio JUBILATO",
    ))
    assert len(match_edition(_edition_with(body))) == 1


@pytest.mark.django_db
def test_one_malformed_group_disables_the_whole_watch():
    _watch(_group("alfa"), {"terms": []})
    assert match_edition(_edition_with("alfa presente aqui")) == []


@pytest.mark.django_db
def test_non_dict_group_disables_the_whole_watch():
    _watch(_group("alfa"), "lixo")
    assert match_edition(_edition_with("alfa presente aqui")) == []


@pytest.mark.django_db
def test_non_string_exclude_entry_is_skipped_not_crashed():
    watch = _watch(_group("beta corp"), name="ExBad")
    watch.exclude = [1]
    watch.save()
    matches = match_edition(_edition_with("BETA CORP citada nesta data."))
    assert len(matches) == 1
    assert matches[0].watch == watch
