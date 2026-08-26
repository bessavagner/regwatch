import datetime

from django.conf import settings
from django.utils import formats

from config.formatting import br_date

DATE = datetime.date(2026, 8, 26)


def test_the_project_speaks_brazilian_portuguese():
    assert settings.LANGUAGE_CODE == "pt-br"


def test_the_project_keeps_brasilia_time():
    assert settings.TIME_ZONE == "America/Sao_Paulo"
    # Rows stay in UTC; only rendering and timezone.localdate() shift.
    assert settings.USE_TZ is True


def test_django_is_already_on_the_brazilian_date_format():
    assert formats.date_format(DATE) == "26 de Agosto de 2026"


def test_br_date_lowercases_the_month_the_way_portuguese_does():
    assert br_date(DATE) == "26 de agosto de 2026"


def test_br_date_leaves_the_digits_alone():
    assert br_date(datetime.date(2026, 1, 1)) == "1 de janeiro de 2026"
