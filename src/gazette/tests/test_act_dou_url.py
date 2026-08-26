import datetime

import pytest

from gazette.models import Act, Edition

DATE = datetime.date(2026, 6, 26)
ANCHOR = (
    "http://pesquisa.in.gov.br/imprensa/jsp/visualiza/index.jsp"
    "?data=26/06/2026&jornal=515&pagina=19"
)
INLABS_ZIP = "https://inlabs.in.gov.br/index.php?p=2026-06-26&dl=2026-06-26-DO1.zip"


@pytest.fixture
def edition(db):
    return Edition.objects.create(date=DATE, section="DO1", source_url=INLABS_ZIP)


def _act(edition, anchor):
    return Act.objects.create(
        edition=edition, identifier="a1", title="Portaria 12", agency="Org",
        raw_text="corpo", search_text="corpo", source_anchor=anchor,
    )


@pytest.mark.django_db
def test_uses_the_source_anchor_when_there_is_one(edition):
    assert _act(edition, ANCHOR).dou_url == ANCHOR.replace("http://", "https://", 1)


@pytest.mark.django_db
def test_an_https_anchor_is_left_alone(edition):
    url = ANCHOR.replace("http://", "https://", 1)
    assert _act(edition, url).dou_url == url


@pytest.mark.django_db
def test_never_hands_the_reader_the_authenticated_inlabs_zip(edition):
    assert "inlabs" not in _act(edition, "").dou_url


@pytest.mark.django_db
def test_falls_back_to_the_public_edition_page(edition):
    assert _act(edition, "").dou_url == (
        "https://www.in.gov.br/leiturajornal?data=26-06-2026&secao=do1"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "section,expected", [("DO1", "do1"), ("DO2", "do2"), ("DO1E", "do1e"), ("1", "do1")]
)
def test_fallback_normalises_the_section(db, section, expected):
    ed = Edition.objects.create(date=DATE, section=section, source_url=INLABS_ZIP)
    assert _act(ed, "").dou_url.endswith(f"&secao={expected}")
